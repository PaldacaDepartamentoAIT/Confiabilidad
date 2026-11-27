from datetime import UTC, datetime
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.accounts import disable
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
