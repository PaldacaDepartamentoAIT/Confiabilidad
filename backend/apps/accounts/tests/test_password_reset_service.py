from datetime import timedelta
from typing import Any

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts import codes, password_reset
from apps.accounts.models import PasswordResetRequest, User
from apps.accounts.tests.factories import make_user

pytestmark = pytest.mark.django_db

PURPOSE = codes.Purpose.PASSWORD_RESET
EMAIL = "ana@x.com"


@pytest.fixture
def user() -> User:
    return make_user(email=EMAIL, name="Ana García")


def _stored() -> PasswordResetRequest:
    return PasswordResetRequest.objects.get()


def _started(email: str = EMAIL) -> password_reset.Started:
    result = password_reset.start(email=email)
    assert isinstance(result, password_reset.Started)
    return result


def _age(**minutes: int) -> None:
    now = timezone.now()
    PasswordResetRequest.objects.update(
        **{field: now - timedelta(minutes=value) for field, value in minutes.items()}
    )


def test_start_creates_a_request_with_a_code(user: User) -> None:
    result = _started()

    stored = _stored()
    assert stored.user == user
    assert stored.public_id == result.public_id
    assert codes.verify_code(PURPOSE, result.public_id, result.code, stored.code_hash)
    assert codes.account_stamp_matches(stored.account_stamp, user.email, user.password)
    assert (stored.failed_attempts, stored.code_validated_at) == (0, None)
    assert not stored.is_expired


def test_start_ignores_case_and_surrounding_spaces(user: User) -> None:
    result = _started("  ANA@X.com ")

    assert _stored().public_id == result.public_id


def test_repeating_replaces_the_request(user: User) -> None:
    first = _started()
    PasswordResetRequest.objects.update(failed_attempts=3, code_validated_at=timezone.now())
    _age(created_at=30)
    user.set_password("another-long-passw0rd")
    user.save()

    second = _started()

    stored = _stored()
    assert second.public_id != first.public_id
    assert stored.public_id == second.public_id
    assert codes.verify_code(PURPOSE, second.public_id, second.code, stored.code_hash)
    assert not codes.verify_code(PURPOSE, second.public_id, first.code, stored.code_hash)
    assert (stored.failed_attempts, stored.code_validated_at) == (0, None)
    assert stored.created_at > timezone.now() - timedelta(minutes=1)
    assert codes.account_stamp_matches(stored.account_stamp, user.email, user.password)


def test_repeating_replaces_an_expired_request(user: User) -> None:
    first = _started()
    _age(created_at=61, code_expires_at=30)
    assert _stored().is_expired

    second = _started()

    stored = _stored()
    assert stored.public_id == second.public_id != first.public_id
    assert not stored.is_expired


def test_unknown_email_has_no_eligible_account() -> None:
    make_user(email="other@x.com")

    assert password_reset.start(email=EMAIL) == password_reset.NoEligibleAccount()
    assert not PasswordResetRequest.objects.exists()


def test_inactive_account_gets_the_same_result_and_keeps_its_request(user: User) -> None:
    first = _started()
    before = _stored()
    User.objects.filter(pk=user.pk).update(is_active=False)

    assert password_reset.start(email=EMAIL) == password_reset.NoEligibleAccount()

    after = _stored()
    assert (after.public_id, after.code_hash, after.created_at) == (
        first.public_id,
        before.code_hash,
        before.created_at,
    )


def test_concurrent_insert_is_turned_into_a_replacement(
    user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = _started()
    real_lookup = password_reset._locked_request
    calls: list[Any] = []

    def miss_once(account: User) -> PasswordResetRequest | None:
        calls.append(account)
        return None if len(calls) == 1 else real_lookup(account)

    monkeypatch.setattr(password_reset, "_locked_request", miss_once)

    second = _started()

    assert len(calls) == 2
    stored = _stored()
    assert stored.public_id == second.public_id != first.public_id
    assert codes.verify_code(PURPOSE, second.public_id, second.code, stored.code_hash)


def test_other_integrity_errors_are_not_hidden(user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    taken = _started().public_id
    PasswordResetRequest.objects.update(user=make_user())
    monkeypatch.setattr("apps.accounts.processes.codes.generate_public_id", lambda: taken)

    with pytest.raises(IntegrityError):
        password_reset.start(email=EMAIL)

    assert not PasswordResetRequest.objects.filter(user=user).exists()
