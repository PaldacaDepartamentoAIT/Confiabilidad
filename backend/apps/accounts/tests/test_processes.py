from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.accounts import codes, processes, registration
from apps.accounts.models import PasswordResetRequest
from apps.accounts.processes import VerifyResult
from apps.accounts.tests.factories import make_user

pytestmark = pytest.mark.django_db

PURPOSE = codes.Purpose.PASSWORD_RESET


def _issued() -> tuple[PasswordResetRequest, str]:
    request = PasswordResetRequest(user=make_user(), account_stamp="b" * 64)
    code = processes.issue_code(request, PURPOSE)
    request.save()
    return request, code


def _stored(request: PasswordResetRequest) -> PasswordResetRequest:
    return PasswordResetRequest.objects.get(pk=request.pk)


def test_issue_code_sets_a_fresh_public_id_and_code() -> None:
    before = timezone.now()
    request, code = _issued()

    stored = _stored(request)
    assert stored.public_id and not stored.public_id.startswith("-")
    assert codes.verify_code(PURPOSE, stored.public_id, code, stored.code_hash)
    assert not codes.verify_code(
        codes.Purpose.REGISTRATION, stored.public_id, code, stored.code_hash
    )
    assert before + timedelta(minutes=15) <= stored.code_expires_at
    assert stored.code_expires_at <= timezone.now() + timedelta(minutes=15)
    assert (stored.failed_attempts, stored.code_validated_at) == (0, None)


def test_issue_code_replaces_everything_on_an_existing_process() -> None:
    request, old_code = _issued()
    old_public_id = request.public_id
    request.failed_attempts = 3
    request.code_validated_at = timezone.now()

    new_code = processes.issue_code(request, PURPOSE)
    request.save(update_fields=processes.ISSUED_FIELDS)

    stored = _stored(request)
    assert stored.public_id != old_public_id
    assert codes.verify_code(PURPOSE, stored.public_id, new_code, stored.code_hash)
    assert not codes.verify_code(PURPOSE, stored.public_id, old_code, stored.code_hash)
    assert (stored.failed_attempts, stored.code_validated_at) == (0, None)


@override_settings(REGISTRATION_CODE_TTL_MINUTES=5)
def test_issued_code_lifetime_follows_settings() -> None:
    request, _code = _issued()

    assert _stored(request).code_expires_at <= timezone.now() + timedelta(minutes=5)


def test_right_code_is_verified() -> None:
    request, code = _issued()

    assert processes.check_code(request, PURPOSE, code) == VerifyResult.VERIFIED
    assert _stored(request).code_validated_at is not None


def test_wrong_code_adds_a_failed_attempt() -> None:
    request, code = _issued()
    wrong = "000000" if code != "000000" else "111111"

    assert processes.check_code(request, PURPOSE, wrong) == VerifyResult.WRONG_CODE
    stored = _stored(request)
    assert (stored.failed_attempts, stored.code_validated_at) == (1, None)


def test_code_of_another_purpose_is_wrong() -> None:
    request, code = _issued()
    request.code_hash = codes.code_fingerprint(codes.Purpose.REGISTRATION, request.public_id, code)

    assert processes.check_code(request, PURPOSE, code) == VerifyResult.WRONG_CODE


def test_locked_process_rejects_even_the_right_code() -> None:
    request, code = _issued()
    request.failed_attempts = 5

    assert processes.check_code(request, PURPOSE, code) == VerifyResult.LOCKED
    assert _stored(request).code_validated_at is None


def test_expired_code_is_rejected_without_counting_an_attempt() -> None:
    request, code = _issued()
    request.code_expires_at = timezone.now()

    assert processes.check_code(request, PURPOSE, code) == VerifyResult.CODE_EXPIRED
    assert _stored(request).failed_attempts == 0


def test_validated_process_rejects_any_code() -> None:
    request, code = _issued()
    assert processes.check_code(request, PURPOSE, code) == VerifyResult.VERIFIED

    assert processes.check_code(request, PURPOSE, code) == VerifyResult.ALREADY_VERIFIED
    assert processes.check_code(request, PURPOSE, "000000") == VerifyResult.ALREADY_VERIFIED
    assert _stored(request).failed_attempts == 0


def test_renew_code_keeps_the_public_id_and_resets_attempts() -> None:
    request, old_code = _issued()
    public_id = request.public_id
    request.failed_attempts = 5
    request.code_expires_at = timezone.now() - timedelta(minutes=1)
    request.save()

    new_code = processes.renew_code(request, PURPOSE)

    stored = _stored(request)
    assert stored.public_id == public_id
    assert codes.verify_code(PURPOSE, public_id, new_code, stored.code_hash)
    assert not codes.verify_code(PURPOSE, public_id, old_code, stored.code_hash)
    assert stored.failed_attempts == 0
    assert stored.code_expires_at > timezone.now()


def test_registration_exposes_the_shared_verify_result() -> None:
    assert registration.VerifyResult is VerifyResult


def test_code_is_expired_at_its_exact_expiry_instant(monkeypatch: pytest.MonkeyPatch) -> None:
    request, code = _issued()
    instant = request.code_expires_at
    monkeypatch.setattr("apps.accounts.processes.timezone.now", lambda: instant)

    assert processes.check_code(request, PURPOSE, code) == VerifyResult.CODE_EXPIRED
