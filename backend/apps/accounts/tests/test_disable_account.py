from datetime import UTC, datetime, timedelta
from io import StringIO
from typing import Any

import pytest
from django.contrib.auth import HASH_SESSION_KEY, SESSION_KEY
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpRequest
from django.test import override_settings
from django.utils import timezone

from apps.accounts import conf, disable, registration, sessions, throttling
from apps.accounts.models import (
    PasswordResetRequest,
    PendingRegistration,
    PhantomProcess,
    User,
    UserSession,
)
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_reset_request, make_user
from apps.audit.models import EventType, SecurityEvent
from apps.companies.models import Company
from apps.emails.models import EmailTemplate, OutboundEmail


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


def _open_session(user: User, agent: str) -> str:
    store = sessions._session_store()
    store[SESSION_KEY] = str(user.pk)
    store[HASH_SESSION_KEY] = user.get_session_auth_hash()
    store.save()
    req = HttpRequest()
    req.session = store
    req.META["REMOTE_ADDR"] = "127.0.0.1"
    req.META["HTTP_USER_AGENT"] = agent
    sessions.register_session(req, user)
    return str(store.session_key)


@pytest.mark.django_db
def test_disable_account_blocks_company_owner_before_password_check() -> None:
    cache.clear()
    owner = make_user(email="owner-block@example.com")
    Company.objects.create(name="Planta Uno", owner=owner)
    session_key = _open_session(owner, "web")
    before_events = SecurityEvent.objects.count()
    before_emails = OutboundEmail.objects.count()

    for _ in range(6):
        result = disable.disable_account(owner, current_password="wrong-password")
        assert result == disable.DisableBlocked(reason=disable.DisableBlockReason.OWNS_COMPANY)

    assert throttling.check_account_disable(owner.pk).allowed is True
    assert sessions.is_session_active(session_key, owner.pk) is True
    assert SecurityEvent.objects.count() == before_events
    assert OutboundEmail.objects.count() == before_emails


@pytest.mark.django_db
def test_disable_account_protects_last_active_superuser_but_allows_others() -> None:
    cache.clear()
    only_super = make_user(email="super1@example.com", is_superuser=True, is_staff=True)
    result = disable.disable_account(only_super, current_password="wrong-password")
    assert result == disable.DisableBlocked(reason=disable.DisableBlockReason.LAST_SUPERUSER)
    assert throttling.check_account_disable(only_super.pk).allowed is True

    second_super = make_user(email="super2@example.com", is_superuser=True, is_staff=True)
    staff_user = make_user(email="staff@example.com", is_staff=True)
    assert disable.disable_block_reason(only_super) is None

    res_super = disable.disable_account(second_super, current_password=DEFAULT_PASSWORD)
    assert isinstance(res_super, disable.AccountDisabled)
    res_staff = disable.disable_account(staff_user, current_password=DEFAULT_PASSWORD)
    assert isinstance(res_staff, disable.AccountDisabled)


@pytest.mark.django_db
def test_disable_account_validates_password_and_applies_lockout() -> None:
    cache.clear()
    user = make_user(email="reauth@example.com")
    session_key = _open_session(user, "desktop")

    missing = disable.disable_account(user, current_password="")
    assert missing == disable.DisableInvalid(missing_password=True)
    # Contraseña vacía no consume intentos.
    for _ in range(4):
        invalid = disable.disable_account(user, current_password="wrong")
        assert invalid == disable.DisableInvalid(missing_password=False)
    assert throttling.check_account_disable(user.pk).allowed is True

    fifth = disable.disable_account(user, current_password="wrong")
    assert fifth == disable.DisableInvalid(missing_password=False)
    locked = disable.disable_account(user, current_password=DEFAULT_PASSWORD)
    assert isinstance(locked, disable.DisableLocked)
    assert locked.retry_after > 0
    assert sessions.is_session_active(session_key, user.pk) is True


@pytest.mark.django_db
def test_disable_account_revokes_access_audits_emails_and_reserves_email(
    django_capture_on_commit_callbacks: Any,
) -> None:
    cache.clear()
    user = make_user(email="bye@example.com", name="Ana Silva", language="pt-BR")
    web_key = _open_session(user, "browser")
    app_key = _open_session(user, "desktop")
    started = make_reset_request(user.email)
    throttling.record_account_disable_failure(user.pk)

    before_audit = SecurityEvent.objects.filter(event_type=EventType.ACCOUNT_DISABLE).count()
    before_emails = OutboundEmail.objects.count()

    with django_capture_on_commit_callbacks(execute=True):
        result = disable.disable_account(user, current_password=DEFAULT_PASSWORD)
    assert isinstance(result, disable.AccountDisabled)

    user.refresh_from_db()
    assert user.is_active is False
    assert user.disabled_at is not None
    assert UserSession.objects.filter(user=user).count() == 0
    assert sessions.is_session_active(web_key, user.pk) is False
    assert sessions.is_session_active(app_key, user.pk) is False
    assert not PasswordResetRequest.objects.filter(user=user).exists()
    assert PhantomProcess.objects.filter(
        public_id=started.public_id,
        purpose=PhantomProcess.Purpose.PASSWORD_RESET,
        answers_expired=True,
    ).exists()
    assert SecurityEvent.objects.filter(event_type=EventType.ACCOUNT_DISABLE).count() == (
        before_audit + 1
    )
    queued = OutboundEmail.objects.order_by("-pk").first()
    assert OutboundEmail.objects.count() == before_emails + 1
    assert queued is not None
    assert queued.kind == EmailTemplate.Kind.ACCOUNT_DISABLED
    assert queued.locale == "pt-BR"
    assert throttling.check_account_disable(user.pk).allowed is True

    # Mientras está deshabilitada, no permite nuevo registro ni envía aviso "ya tienes cuenta".
    reg = registration.start(
        email="BYE@EXAMPLE.COM",
        name="Otra",
        birthdate=datetime(1992, 5, 5, tzinfo=UTC).date(),
        country="ES",
    )
    registration.resolve_registration(reg.public_id)
    assert not PendingRegistration.objects.filter(email__iexact=user.email).exists()
    assert OutboundEmail.objects.count() == before_emails + 1


@pytest.mark.django_db
def test_account_disable_cli_command() -> None:
    cache.clear()
    owner = make_user(email="cli-owner@example.com")
    Company.objects.create(name="Empresa CLI", owner=owner)
    with pytest.raises(CommandError, match="company"):
        call_command(
            "account",
            "disable",
            "--email",
            owner.email,
            "--current-password",
            DEFAULT_PASSWORD,
        )

    user = make_user(email="cli-free@example.com")
    with pytest.raises(CommandError, match="incorrect"):
        call_command(
            "account",
            "disable",
            "--email",
            user.email,
            "--current-password",
            "wrong",
        )

    out = StringIO()
    call_command(
        "account",
        "disable",
        "--email",
        user.email,
        "--current-password",
        DEFAULT_PASSWORD,
        stdout=out,
    )
    user.refresh_from_db()
    assert user.is_active is False
    assert f"disabled: {user.email}" in out.getvalue()
