import logging
from datetime import UTC, date, datetime, timedelta
from io import StringIO

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts import disable, registration
from apps.accounts import tasks as account_tasks
from apps.accounts.models import PendingRegistration, User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user
from apps.audit.models import EventType, SecurityEvent
from apps.companies.models import Company
from apps.consents.models import Terms
from apps.consents.services import TermsState, accept_terms, consent_status
from apps.core.maintenance import SimulatedMaintenanceFailure
from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus


def test_retention_deadline_handles_leap_day_and_configurable_months() -> None:
    leap = datetime(2024, 2, 29, 14, 30, tzinfo=UTC)
    assert disable.retention_deadline(leap) == datetime(2025, 2, 28, 14, 30, tzinfo=UTC)
    assert disable.retention_deadline(leap, months=48) == datetime(2028, 2, 29, 14, 30, tzinfo=UTC)

    jan_end = datetime(2025, 1, 31, 8, 0, tzinfo=UTC)
    with override_settings(ACCOUNT_DISABLE_RETENTION_MONTHS=1):
        assert disable.retention_deadline(jan_end) == datetime(2025, 2, 28, 8, 0, tzinfo=UTC)


@pytest.mark.django_db
def test_reactivate_account_before_and_after_12_months() -> None:
    for locale in ("es", "pt-BR", "en"):
        Terms.objects.create(
            kind=Terms.Kind.TERMS,
            version="1.0",
            locale=locale,
            content=f"Terminos {locale}",
            published_at=datetime(2024, 1, 1, tzinfo=UTC),
            requires_reacceptance=True,
        )
    user = make_user(email="react@example.com", password=DEFAULT_PASSWORD)
    accept_terms(user, version="1.0", locale="es")

    disabled_at = datetime(2024, 2, 29, 10, 0, tzinfo=UTC)
    user.is_active = False
    user.disabled_at = disabled_at
    user.save(update_fields=["is_active", "disabled_at"])

    # Justo a los 12 meses calendario (28 feb 2025 10:00 UTC) ya está vencida.
    at_deadline = datetime(2025, 2, 28, 10, 0, tzinfo=UTC)
    expired = disable.reactivate_account(user, now=at_deadline)
    assert isinstance(expired, disable.ReactivationExpired)
    user.refresh_from_db()
    assert user.is_active is False

    # Un segundo antes sigue dentro de plazo y conserva contraseña y consentimientos.
    before_deadline = datetime(2025, 2, 28, 9, 59, 59, tzinfo=UTC)
    reactivated = disable.reactivate_account(user, now=before_deadline)
    assert isinstance(reactivated, disable.AccountReactivated)

    user.refresh_from_db()
    assert user.is_active is True
    assert user.disabled_at is None
    assert user.check_password(DEFAULT_PASSWORD) is True
    assert consent_status(user).terms is TermsState.ACCEPTED
    assert isinstance(disable.reactivate_account(user), disable.ReactivationAlreadyActive)


@pytest.mark.django_db
def test_reactivate_cli_command() -> None:
    recent = make_user(email="cli-react@example.com")
    recent.is_active = False
    recent.save(update_fields=["is_active"])

    out = StringIO()
    call_command("account", "reactivate", "--email", "CLI-REACT@example.com", stdout=out)
    recent.refresh_from_db()
    assert recent.is_active is True
    assert recent.disabled_at is None
    assert f"reactivated: {recent.email}" in out.getvalue()

    old = make_user(
        email="cli-expired@example.com",
        is_active=False,
        disabled_at=datetime(2020, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(CommandError, match="12-month"):
        call_command("account", "reactivate", "--email", old.email)

    with pytest.raises(CommandError, match="already active"):
        call_command("account", "reactivate", "--email", recent.email)


def _admin_payload(user: User, *, is_active: bool) -> dict[str, str]:
    data = {
        "email": user.email,
        "name": user.name,
        "birthdate": user.birthdate.isoformat(),
        "country": user.country,
        "language": user.language,
    }
    if is_active:
        data["is_active"] = "on"
    if user.is_staff:
        data["is_staff"] = "on"
    if user.is_superuser:
        data["is_superuser"] = "on"
    return data


@pytest.mark.django_db
def test_admin_support_can_reactivate_within_12_months_and_is_blocked_after() -> None:
    support_group, _ = Group.objects.get_or_create(name="Soporte técnico")
    support_user = make_user(email="support@example.com", is_staff=True)
    support_user.groups.add(support_group)

    target = make_user(email="target@example.com")
    target.is_active = False
    target.save(update_fields=["is_active"])

    client = Client()
    client.force_login(support_user)
    change_url = reverse("admin:accounts_user_change", args=[target.pk])

    response = client.post(change_url, _admin_payload(target, is_active=True))
    assert response.status_code == 302
    target.refresh_from_db()
    assert target.is_active is True
    assert target.disabled_at is None
    latest = target.history.latest("history_id")
    assert latest.history_user_id == support_user.pk

    # Desactivar manualmente desde admin registra disabled_at en UTC.
    deactivate_res = client.post(change_url, _admin_payload(target, is_active=False))
    assert deactivate_res.status_code == 302
    target.refresh_from_db()
    assert target.is_active is False
    assert target.disabled_at is not None

    # Si han pasado 12 meses, el panel rechaza reactivarla.
    User.objects.filter(pk=target.pk).update(disabled_at=datetime(2020, 1, 1, tzinfo=UTC))
    expired_res = client.post(change_url, _admin_payload(target, is_active=True))
    assert expired_res.status_code == 200
    target.refresh_from_db()
    assert target.is_active is False

    # La acción masiva también respeta los 12 meses.
    changelist_url = reverse("admin:accounts_user_changelist")
    action_res = client.post(
        changelist_url,
        {
            "action": "reactivate_selected",
            "select_across": "0",
            "index": "0",
            "_selected_action": [str(target.pk)],
        },
    )
    assert action_res.status_code == 302
    target.refresh_from_db()
    assert target.is_active is False

    # El historial no puede revertirse mediante POST desde el panel.
    history_url = reverse("admin:accounts_user_history", args=[target.pk])
    assert client.get(history_url).status_code == 200


@pytest.mark.django_db
def test_purge_accounts_deletes_expired_preserves_history_and_frees_email() -> None:
    now = timezone.now()
    expired = make_user(email="old@example.com")
    expired_pk = expired.pk
    disable.disable_account(expired, current_password=DEFAULT_PASSWORD)
    User.objects.filter(pk=expired_pk).update(disabled_at=now - timedelta(days=400))

    recent = make_user(email="recent@example.com")
    recent.is_active = False
    recent.disabled_at = now - timedelta(days=30)
    recent.save(update_fields=["is_active", "disabled_at"])

    legacy_null = make_user(email="legacy@example.com", is_active=False)
    User.objects.filter(pk=legacy_null.pk).update(disabled_at=None)

    active = make_user(email="active@example.com")
    before_events = SecurityEvent.objects.filter(event_type=EventType.ACCOUNT_DISABLE).count()

    deleted = disable.purge_expired_accounts(now=now)
    assert deleted == 1
    assert not User.objects.filter(pk=expired_pk).exists()
    assert User.objects.filter(pk=recent.pk).exists()
    assert User.objects.filter(pk=legacy_null.pk).exists()
    assert User.objects.filter(pk=active.pk).exists()
    assert User.history.filter(id=expired_pk).exists()
    assert SecurityEvent.objects.filter(event_type=EventType.ACCOUNT_DISABLE).count() == (
        before_events
    )

    # Al quedar libre el correo tras la purga física, admite un nuevo registro.
    started = registration.start(
        email="old@example.com",
        name="Nueva Persona",
        birthdate=date(1992, 4, 10),
        country="ES",
    )
    registration.resolve_registration(started.public_id)
    assert PendingRegistration.objects.filter(email__iexact="old@example.com").exists()


@pytest.mark.django_db
def test_purge_accounts_is_partial_when_expired_account_owns_company(
    caplog: pytest.LogCaptureFixture,
) -> None:
    now = timezone.now()
    valid_expired = make_user(
        email="purge-ok@example.com",
        is_active=False,
        disabled_at=now - timedelta(days=400),
    )
    anomalous_owner = make_user(email="purge-owner@example.com")
    Company.objects.create(name="Anomalia", owner=anomalous_owner)
    User.objects.filter(pk=anomalous_owner.pk).update(
        is_active=False,
        disabled_at=now - timedelta(days=400),
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(disable.DisabledAccountPurgeAnomaly):
            disable.purge_expired_accounts(now=now)

    assert not User.objects.filter(pk=valid_expired.pk).exists()
    assert User.objects.filter(pk=anomalous_owner.pk).exists()
    assert "still owns at least one company" in caplog.text


@pytest.mark.django_db
def test_maintenance_task_purge_disabled_accounts_alerts_and_cli() -> None:
    assert "accounts-purge-disabled-accounts" in django_settings.CELERY_BEAT_SCHEDULE
    now = timezone.now()
    valid = make_user(
        email="maint-ok@example.com",
        is_active=False,
        disabled_at=now - timedelta(days=400),
    )
    owner = make_user(email="maint-owner@example.com")
    company = Company.objects.create(name="Pendiente", owner=owner)
    User.objects.filter(pk=owner.pk).update(
        is_active=False,
        disabled_at=now - timedelta(days=400),
    )

    with override_settings(MAINTENANCE_ALERT_EMAILS=["ops@example.com"]):
        with pytest.raises(SimulatedMaintenanceFailure):
            account_tasks.purge_disabled_accounts(simulate_failure=True)
        assert User.objects.filter(pk=valid.pk).exists()
        assert len(mail.outbox) == 1

        # En ejecución real con anomalía: purga la cuenta válida, omite la propietaria y alerta.
        with pytest.raises(disable.DisabledAccountPurgeAnomaly):
            account_tasks.purge_disabled_accounts()
        assert not User.objects.filter(pk=valid.pk).exists()
        assert User.objects.filter(pk=owner.pk).exists()
        status_row = MaintenanceTaskStatus.objects.get(
            task_name=MaintenanceTaskName.PURGE_DISABLED_ACCOUNTS
        )
        assert status_row.status == MaintenanceTaskStatus.Status.FAILURE
        assert (
            MaintenanceAlert.objects.filter(
                task_name=MaintenanceTaskName.PURGE_DISABLED_ACCOUNTS,
                resolved_at__isnull=True,
            ).count()
            == 2
        )

        # Al borrarse la empresa, la siguiente corrida purga la cuenta y resuelve alertas.
        company.delete()
        out = StringIO()
        call_command("maintenance_tasks", "run", "purge_disabled_accounts", stdout=out)
        assert "completed purge_disabled_accounts: deleted=1" in out.getvalue()
        assert not User.objects.filter(pk=owner.pk).exists()
        assert not MaintenanceAlert.objects.filter(
            task_name=MaintenanceTaskName.PURGE_DISABLED_ACCOUNTS,
            resolved_at__isnull=True,
        ).exists()


@pytest.mark.django_db
def test_admin_non_support_staff_cannot_reactivate_inactive_user() -> None:
    other_staff = make_user(email="otherstaff@example.com", is_staff=True)
    change_perm = Permission.objects.get(codename="change_user")
    view_perm = Permission.objects.get(codename="view_user")
    other_staff.user_permissions.add(change_perm, view_perm)

    inactive = make_user(email="locked@example.com")
    inactive.is_active = False
    inactive.save(update_fields=["is_active"])

    client = Client()
    client.force_login(other_staff)
    change_url = reverse("admin:accounts_user_change", args=[inactive.pk])

    response = client.post(change_url, _admin_payload(inactive, is_active=True))
    assert response.status_code == 403
    inactive.refresh_from_db()
    assert inactive.is_active is False
