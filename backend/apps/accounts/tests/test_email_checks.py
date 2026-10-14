from datetime import date, timedelta

import pytest
from django.utils import timezone

from apps.accounts import email_checks, password_reset, registration
from apps.accounts.models import PasswordResetRequest, PendingRegistration
from apps.accounts.tests.factories import make_user
from apps.emails import delivery

pytestmark = pytest.mark.django_db


def _start_registration() -> registration.Started | registration.AccountExists:
    return registration.start(
        email="ana@x.com", name="Ana", birthdate=date(1990, 5, 10), country="ES"
    )


def _registration() -> registration.Started:
    started = _start_registration()
    assert isinstance(started, registration.Started)
    return started


def _reset() -> password_reset.Started:
    make_user(email="eva@x.com")
    started = password_reset.start(email="eva@x.com")
    assert isinstance(started, password_reset.Started)
    return started


def _other(code: str) -> str:
    return f"{(int(code) + 1) % 10**6:06d}"


def test_a_current_registration_code_returns_its_expiry() -> None:
    started = _registration()

    expiry = email_checks.registration_code_expiry(started.public_id, started.code)

    assert expiry == PendingRegistration.objects.get().code_expires_at


def test_a_current_password_reset_code_returns_its_expiry() -> None:
    started = _reset()

    expiry = email_checks.password_reset_code_expiry(started.public_id, started.code)

    assert expiry == PasswordResetRequest.objects.get().code_expires_at


def test_another_code_does_not_serve() -> None:
    started = _registration()

    assert email_checks.registration_code_expiry(started.public_id, _other(started.code)) is None


def test_a_validated_code_does_not_serve() -> None:
    started = _registration()
    registration.verify(public_id=started.public_id, code=started.code)

    assert email_checks.registration_code_expiry(started.public_id, started.code) is None


def test_an_expired_code_does_not_serve() -> None:
    started = _reset()
    PasswordResetRequest.objects.update(code_expires_at=timezone.now() - timedelta(seconds=1))

    assert email_checks.password_reset_code_expiry(started.public_id, started.code) is None


def test_a_replaced_code_does_not_serve() -> None:
    first = _registration()
    again = _start_registration()
    assert isinstance(again, registration.Started)

    assert email_checks.registration_code_expiry(first.public_id, first.code) is None
    assert email_checks.registration_code_expiry(again.public_id, again.code) is not None


def test_a_resent_code_replaces_the_previous_one() -> None:
    started = _reset()
    resent = password_reset.resend(public_id=started.public_id)
    assert isinstance(resent, password_reset.Resent)

    assert email_checks.password_reset_code_expiry(started.public_id, started.code) is None
    assert email_checks.password_reset_code_expiry(resent.public_id, resent.code) is not None


def test_an_unknown_process_does_not_serve() -> None:
    assert email_checks.registration_code_expiry("nope", "123456") is None
    assert email_checks.password_reset_code_expiry("nope", "123456") is None


def test_a_public_id_does_not_serve_for_the_other_process() -> None:
    registration_started = _registration()
    reset_started = _reset()

    assert (
        email_checks.password_reset_code_expiry(
            registration_started.public_id, registration_started.code
        )
        is None
    )
    assert (
        email_checks.registration_code_expiry(reset_started.public_id, reset_started.code) is None
    )


def test_the_checks_are_registered_when_django_starts() -> None:
    assert delivery._CODE_CHECKS["registration"] is email_checks.registration_code_expiry
    assert delivery._CODE_CHECKS["password_reset"] is email_checks.password_reset_code_expiry
