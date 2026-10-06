from datetime import date, timedelta
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import override_settings
from django.utils import timezone

from apps.accounts import codes, registration
from apps.accounts.models import PendingRegistration
from apps.accounts.tests.factories import make_user

pytestmark = pytest.mark.django_db

DATA: dict[str, Any] = {"name": "Ana García", "birthdate": date(1990, 5, 10), "country": "ES"}


def _start(email: str = "ana@x.com", **overrides: Any) -> registration.Started:
    result = registration.start(email=email, **{**DATA, **overrides})
    assert isinstance(result, registration.Started)
    return result


def test_start_stores_the_registration_and_returns_the_code_once() -> None:
    before = timezone.now()
    result = _start(" Ana@X.com ")

    pending = PendingRegistration.objects.get()
    assert pending.public_id == result.public_id
    assert (pending.email, pending.failed_attempts, pending.code_validated_at) == (
        "ana@x.com",
        0,
        None,
    )
    assert codes.verify_code(result.public_id, result.code, pending.code_hash)
    stored = PendingRegistration.objects.values().get()
    assert result.code not in [str(value) for value in stored.values()]
    assert (
        before + timedelta(minutes=15)
        <= pending.code_expires_at
        <= timezone.now() + timedelta(minutes=15)
    )


@override_settings(REGISTRATION_CODE_TTL_MINUTES=5)
def test_code_lifetime_follows_settings() -> None:
    _start()

    remaining = PendingRegistration.objects.get().code_expires_at - timezone.now()
    assert timedelta(minutes=4) < remaining <= timedelta(minutes=5)


@pytest.mark.parametrize("is_active", [True, False])
def test_start_with_account_returns_account_exists_and_stores_nothing(is_active: bool) -> None:
    make_user(email="ana@x.com", is_active=is_active)

    result = registration.start(email="ANA@x.com", **DATA)

    assert result == registration.AccountExists()
    assert not PendingRegistration.objects.exists()


@pytest.mark.parametrize("has_account", [False, True])
def test_invalid_data_is_rejected_whether_or_not_the_email_has_an_account(
    has_account: bool,
) -> None:
    if has_account:
        make_user(email="ana@x.com")

    with pytest.raises(ValidationError) as excinfo:
        registration.start(email="ana@x.com", **{**DATA, "country": "XX"})

    assert set(excinfo.value.error_dict) == {"country"}
    assert not PendingRegistration.objects.exists()


def test_malformed_email_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        registration.start(email="not-an-email", **DATA)

    assert set(excinfo.value.error_dict) == {"email"}
    assert not PendingRegistration.objects.exists()


def test_start_deletes_only_the_expired_registration_of_the_same_email() -> None:
    old = _start("ana@x.com")
    other = _start("bea@x.com")
    PendingRegistration.objects.update(created_at=timezone.now() - timedelta(hours=2))

    new = _start("ANA@x.com")

    assert set(PendingRegistration.objects.values_list("public_id", flat=True)) == {
        new.public_id,
        other.public_id,
    }
    assert new.public_id != old.public_id


def test_repeat_keeps_the_data_and_issues_a_new_public_id_and_code() -> None:
    first = _start("ana@x.com")
    PendingRegistration.objects.update(
        failed_attempts=3,
        code_validated_at=timezone.now(),
        code_expires_at=timezone.now() - timedelta(minutes=1),
    )
    created_at = PendingRegistration.objects.get().created_at

    second = _start("ANA@x.com", name="Otra Persona", country="MX")

    pending = PendingRegistration.objects.get()
    assert (pending.name, pending.country, pending.created_at) == ("Ana García", "ES", created_at)
    assert pending.public_id == second.public_id != first.public_id
    assert (pending.failed_attempts, pending.code_validated_at) == (0, None)
    assert pending.code_expires_at > timezone.now() + timedelta(minutes=14)
    assert codes.verify_code(second.public_id, second.code, pending.code_hash)
    assert not codes.verify_code(first.public_id, first.code, pending.code_hash)
    if first.code != second.code:
        assert not codes.verify_code(second.public_id, first.code, pending.code_hash)


def test_repeat_with_invalid_data_is_rejected_and_changes_nothing() -> None:
    first = _start()

    with pytest.raises(ValidationError) as excinfo:
        registration.start(email="ana@x.com", **{**DATA, "country": "XX"})

    assert set(excinfo.value.error_dict) == {"country"}
    assert PendingRegistration.objects.get().public_id == first.public_id


def test_repeat_after_the_email_got_an_account_returns_account_exists() -> None:
    first = _start()
    make_user(email="ana@x.com")

    assert registration.start(email="ana@x.com", **DATA) == registration.AccountExists()
    assert PendingRegistration.objects.get().public_id == first.public_id


def test_conflict_not_caused_by_the_email_is_not_treated_as_a_repeat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    taken = _start("bea@x.com").public_id
    monkeypatch.setattr("apps.accounts.registration.codes.generate_public_id", lambda: taken)

    with pytest.raises(IntegrityError):
        registration.start(email="ana@x.com", **DATA)

    assert not PendingRegistration.objects.filter(email="ana@x.com").exists()
