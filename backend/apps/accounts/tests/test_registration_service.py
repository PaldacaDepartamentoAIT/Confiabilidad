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


def _wrong(code: str) -> str:
    return "000000" if code != "000000" else "111111"


def _stored() -> PendingRegistration:
    return PendingRegistration.objects.get()


def test_right_code_marks_the_code_as_validated() -> None:
    started = _start()

    assert registration.verify(public_id=started.public_id, code=started.code) == "verified"
    assert _stored().code_validated_at is not None
    assert _stored().failed_attempts == 0


def test_wrong_code_adds_a_failed_attempt() -> None:
    started = _start()

    for expected_attempts in (1, 2):
        result = registration.verify(public_id=started.public_id, code=_wrong(started.code))
        assert result == registration.VerifyResult.WRONG_CODE
        assert _stored().failed_attempts == expected_attempts
    assert _stored().code_validated_at is None


def test_code_of_another_process_is_wrong() -> None:
    ana, bea = _start("ana@x.com"), _start("bea@x.com")
    if ana.code != bea.code:
        result = registration.verify(public_id=ana.public_id, code=bea.code)
        assert result == registration.VerifyResult.WRONG_CODE


@pytest.mark.parametrize(
    ("limit", "settings_override"),
    [(5, {}), (2, {"REGISTRATION_MAX_FAILED_ATTEMPTS": 2})],
)
def test_after_max_failures_even_the_right_code_is_rejected(
    limit: int, settings_override: dict[str, int]
) -> None:
    with override_settings(**settings_override):
        started = _start()
        for _ in range(limit):
            registration.verify(public_id=started.public_id, code=_wrong(started.code))

        result = registration.verify(public_id=started.public_id, code=started.code)

    assert result == registration.VerifyResult.LOCKED
    assert (_stored().failed_attempts, _stored().code_validated_at) == (limit, None)


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        pytest.param({"created_at": 120}, registration.VerifyResult.EXPIRED, id="process-expired"),
        pytest.param(
            {"code_expires_at": 1},
            registration.VerifyResult.CODE_EXPIRED,
            id="code-expired-in-grace",
        ),
    ],
)
def test_expired_code_or_process_is_rejected_without_counting(
    changes: dict[str, int], expected: registration.VerifyResult
) -> None:
    started = _start()
    PendingRegistration.objects.update(
        **{field: timezone.now() - timedelta(minutes=m) for field, m in changes.items()}
    )

    for code in (started.code, _wrong(started.code)):
        assert registration.verify(public_id=started.public_id, code=code) == expected
    assert (_stored().failed_attempts, _stored().code_validated_at) == (0, None)


def test_already_validated_code_rejects_any_code_without_counting() -> None:
    started = _start()
    registration.verify(public_id=started.public_id, code=started.code)

    for code in (started.code, _wrong(started.code)):
        result = registration.verify(public_id=started.public_id, code=code)
        assert result == registration.VerifyResult.ALREADY_VERIFIED
    assert _stored().failed_attempts == 0


def test_unknown_public_id_is_rejected() -> None:
    started = _start()

    result = registration.verify(public_id="unknown", code=started.code)

    assert result == registration.VerifyResult.NOT_FOUND


def _resend(public_id: str) -> registration.Resent:
    result = registration.resend(public_id=public_id)
    assert isinstance(result, registration.Resent)
    return result


def test_resend_keeps_the_public_id_and_replaces_the_code() -> None:
    started = _start()

    resent = _resend(started.public_id)

    assert resent.public_id == started.public_id == _stored().public_id
    assert codes.verify_code(started.public_id, resent.code, _stored().code_hash)
    if resent.code != started.code:
        assert registration.verify(public_id=started.public_id, code=started.code) == "wrong_code"


def test_resend_unlocks_a_locked_process() -> None:
    started = _start()
    for _ in range(5):
        registration.verify(public_id=started.public_id, code=_wrong(started.code))

    resent = _resend(started.public_id)

    assert _stored().failed_attempts == 0
    assert registration.verify(public_id=started.public_id, code=resent.code) == "verified"


@override_settings(REGISTRATION_CODE_TTL_MINUTES=5)
def test_resend_renews_an_expired_code_within_the_grace_period() -> None:
    started = _start()
    PendingRegistration.objects.update(code_expires_at=timezone.now() - timedelta(minutes=1))

    resent = _resend(started.public_id)

    remaining = _stored().code_expires_at - timezone.now()
    assert timedelta(minutes=4) < remaining <= timedelta(minutes=5)
    assert registration.verify(public_id=started.public_id, code=resent.code) == "verified"


def test_resend_is_refused_once_the_code_is_validated() -> None:
    started = _start()
    registration.verify(public_id=started.public_id, code=started.code)
    code_hash = _stored().code_hash

    result = registration.resend(public_id=started.public_id)

    assert result == registration.ResendRefusal.ALREADY_VERIFIED
    assert _stored().code_hash == code_hash


def test_resend_is_refused_for_an_expired_process() -> None:
    started = _start()
    PendingRegistration.objects.update(created_at=timezone.now() - timedelta(hours=2))
    code_hash = _stored().code_hash

    result = registration.resend(public_id=started.public_id)

    assert result == registration.ResendRefusal.EXPIRED
    assert _stored().code_hash == code_hash


def test_resend_with_unknown_public_id_is_refused() -> None:
    assert registration.resend(public_id="unknown") == registration.ResendRefusal.NOT_FOUND
