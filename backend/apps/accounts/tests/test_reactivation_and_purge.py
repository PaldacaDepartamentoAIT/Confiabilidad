from datetime import UTC, datetime
from io import StringIO

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, override_settings
from django.urls import reverse

from apps.accounts import disable
from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user
from apps.consents.models import Terms
from apps.consents.services import TermsState, accept_terms, consent_status


def test_retention_deadline_handles_leap_day_and_configurable_months() -> None:
    leap = datetime(2024, 2, 29, 14, 30, tzinfo=UTC)
    assert disable.retention_deadline(leap) == datetime(2025, 2, 28, 14, 30, tzinfo=UTC)
    assert disable.retention_deadline(leap, months=48) == datetime(2028, 2, 29, 14, 30, tzinfo=UTC)

    jan_end = datetime(2025, 1, 31, 8, 0, tzinfo=UTC)
    with override_settings(ACCOUNT_DISABLE_RETENTION_MONTHS=1):
        assert disable.retention_deadline(jan_end) == datetime(2025, 2, 28, 8, 0, tzinfo=UTC)


@pytest.mark.django_db
def test_reactivate_account_before_and_after_12_months() -> None:
    Terms.objects.create(
        kind=Terms.Kind.TERMS,
        version="1.0",
        locale="es",
        content="Terminos",
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
