from datetime import UTC, datetime, timedelta

import pytest
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.utils import timezone

from apps.accounts import conf, throttling
from apps.accounts.models import User
from apps.accounts.tests.factories import make_user


@pytest.mark.django_db
def test_disabled_at_defaults_to_none_on_active_user() -> None:
    user = make_user()
    assert user.is_active is True
    assert user.disabled_at is None


@pytest.mark.django_db
def test_disabled_at_is_recorded_in_utc_when_deactivating_and_cleared_on_reactivation() -> None:
    user = make_user()
    before = timezone.now()
    user.is_active = False
    user.save()
    after = timezone.now()

    user.refresh_from_db()
    assert user.disabled_at is not None
    assert user.disabled_at.tzinfo == UTC
    assert before <= user.disabled_at <= after

    user.is_active = True
    user.save()
    user.refresh_from_db()
    assert user.disabled_at is None

    history = list(user.history.order_by("history_date", "history_id"))
    assert len(history) == 3
    assert history[0].disabled_at is None
    assert history[1].is_active is False and history[1].disabled_at is not None
    assert history[2].is_active is True and history[2].disabled_at is None


@pytest.mark.django_db
def test_disabled_at_syncs_even_with_update_fields_only_is_active() -> None:
    user = make_user()
    user.is_active = False
    user.save(update_fields=["is_active"])
    user.refresh_from_db()
    assert user.disabled_at is not None

    # Actualizar solo disabled_at en cuenta ya inactiva conserva la fecha explícita.
    custom = datetime(2025, 1, 15, 12, 0, tzinfo=UTC)
    user.disabled_at = custom
    user.save(update_fields=["disabled_at"])
    user.refresh_from_db()
    assert user.disabled_at == custom

    user.is_active = True
    user.save(update_fields=["is_active"])
    user.refresh_from_db()
    assert user.disabled_at is None


@pytest.mark.django_db
def test_creating_inactive_user_sets_disabled_at_unless_explicit() -> None:
    explicit = timezone.now() - timedelta(days=30)
    with_explicit = make_user(is_active=False, disabled_at=explicit)
    assert with_explicit.disabled_at == explicit

    without_explicit = make_user(is_active=False)
    assert without_explicit.disabled_at is not None
    assert User.objects.get(pk=without_explicit.pk).disabled_at == without_explicit.disabled_at


def test_account_disable_throttle_defaults_and_lockout_are_independent() -> None:
    cache.clear()
    user_id = 42
    t0 = 1000.0
    assert throttling.check_account_disable(user_id, now=t0).allowed is True

    for i in range(4):
        verdict = throttling.record_account_disable_failure(user_id, now=t0 + i)
        assert verdict.allowed is True

    locked = throttling.record_account_disable_failure(user_id, now=t0 + 4)
    assert locked.allowed is False
    assert locked.retry_after == 300

    # El contador de deshabilitación no afecta ni comparte estado con cambio de contraseña.
    assert throttling.check_password_change(user_id, now=t0 + 5).allowed is True
    assert throttling.check_account_disable(user_id, now=t0 + 10).allowed is False
    assert throttling.check_account_disable(user_id, now=t0 + 10).retry_after == 294

    # Al expirar el bloqueo vuelve a estar permitido con ventana limpia.
    assert throttling.check_account_disable(user_id, now=t0 + 304).allowed is True

    throttling.record_account_disable_failure(user_id, now=t0 + 400)
    throttling.clear_account_disable_failures(user_id)
    assert throttling.check_account_disable(user_id, now=t0 + 401).allowed is True


@override_settings(
    ACCOUNT_DISABLE_MAX_FAILED_ATTEMPTS=2,
    ACCOUNT_DISABLE_ATTEMPT_WINDOW_MINUTES=1,
    ACCOUNT_DISABLE_LOCKOUT_MINUTES=2,
    ACCOUNT_DISABLE_RETENTION_MONTHS=6,
)
def test_account_disable_throttle_and_retention_are_configurable() -> None:
    cache.clear()
    assert conf.account_disable_retention_months() == 6
    assert throttling.record_account_disable_failure(7, now=100.0).allowed is True
    verdict = throttling.record_account_disable_failure(7, now=101.0)
    assert verdict.allowed is False
    assert verdict.retry_after == 120


@override_settings(ACCOUNT_DISABLE_RETENTION_MONTHS=0)
def test_account_disable_retention_rejects_zero() -> None:
    with pytest.raises(ImproperlyConfigured):
        conf.account_disable_retention_months()
