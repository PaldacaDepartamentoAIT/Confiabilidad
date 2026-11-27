from datetime import UTC, datetime, timedelta

import pytest
from django.utils import timezone

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
