from datetime import date, timedelta
from typing import Any

import pytest
from allauth.account.models import EmailAddress
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import override_settings
from django.utils import timezone

from apps.accounts import codes, password_reset, registration
from apps.accounts.models import PasswordResetRequest, PendingRegistration, User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user

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


VerifyResult = password_reset.VerifyResult
AccountRefusal = password_reset.AccountRefusal
ResendRefusal = password_reset.ResendRefusal


def _wrong(code: str) -> str:
    return "000000" if code != "000000" else "111111"


def test_verify_accepts_the_right_code(user: User) -> None:
    started = _started()

    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.VERIFIED
    )
    assert _stored().code_validated_at is not None


def test_verify_counts_wrong_codes_and_locks_at_the_maximum(user: User) -> None:
    started = _started()
    wrong = _wrong(started.code)

    for attempt in range(1, 6):
        assert password_reset.verify(public_id=started.public_id, code=wrong) == (
            VerifyResult.WRONG_CODE
        )
        assert _stored().failed_attempts == attempt

    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.LOCKED
    )
    assert _stored().code_validated_at is None


def test_verify_rejects_an_expired_code_within_the_grace_period(user: User) -> None:
    started = _started()
    _age(code_expires_at=1)

    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.CODE_EXPIRED
    )


@pytest.mark.parametrize("aged", [{"code_expires_at": 16}, {"created_at": 61}])
def test_expired_request_rejects_verify_and_resend(user: User, aged: dict[str, int]) -> None:
    started = _started()
    _age(**aged)

    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.EXPIRED
    )
    assert password_reset.resend(public_id=started.public_id) == ResendRefusal.EXPIRED


def test_verify_rejects_any_code_once_validated(user: User) -> None:
    started = _started()
    password_reset.verify(public_id=started.public_id, code=started.code)

    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.ALREADY_VERIFIED
    )
    assert password_reset.resend(public_id=started.public_id) == ResendRefusal.ALREADY_VERIFIED


def test_unknown_or_registration_public_ids_are_not_found(user: User) -> None:
    pending = registration.start(
        email="new@x.com", name="Nuevo", birthdate=date(1990, 1, 1), country="ES"
    )
    assert isinstance(pending, registration.Started)

    assert password_reset.verify(public_id=pending.public_id, code=pending.code) == (
        VerifyResult.NOT_FOUND
    )
    assert password_reset.resend(public_id=pending.public_id) == ResendRefusal.NOT_FOUND
    assert password_reset.verify(public_id="unknown", code="123456") == VerifyResult.NOT_FOUND


def test_resend_keeps_the_public_id_with_a_new_code(user: User) -> None:
    started = _started()
    PasswordResetRequest.objects.update(failed_attempts=5)

    resent = password_reset.resend(public_id=started.public_id)

    assert isinstance(resent, password_reset.Resent)
    stored = _stored()
    assert resent.public_id == stored.public_id == started.public_id
    assert codes.verify_code(PURPOSE, started.public_id, resent.code, stored.code_hash)
    assert not codes.verify_code(PURPOSE, started.public_id, started.code, stored.code_hash)
    assert stored.failed_attempts == 0
    assert password_reset.verify(public_id=started.public_id, code=resent.code) == (
        VerifyResult.VERIFIED
    )


def _deactivate(user: User) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)


def _change_email(user: User) -> None:
    User.objects.filter(pk=user.pk).update(email="nueva@x.com")


def _change_password(user: User) -> None:
    user.set_password("another-long-passw0rd")
    user.save()


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        (_deactivate, AccountRefusal.INACTIVE),
        (_change_email, AccountRefusal.ACCOUNT_CHANGED),
        (_change_password, AccountRefusal.ACCOUNT_CHANGED),
    ],
)
def test_account_changes_block_verify_and_resend_without_touching_the_request(
    user: User, change: Any, refusal: AccountRefusal
) -> None:
    started = _started()
    change(user)
    before = _stored()

    assert password_reset.verify(public_id=started.public_id, code=started.code) == refusal
    assert password_reset.verify(public_id=started.public_id, code=_wrong(started.code)) == refusal
    assert password_reset.resend(public_id=started.public_id) == refusal

    after = _stored()
    assert (after.code_hash, after.failed_attempts, after.code_validated_at) == (
        before.code_hash,
        0,
        None,
    )


def test_reactivated_account_can_use_its_request_again(user: User) -> None:
    started = _started()
    _deactivate(user)
    assert password_reset.resend(public_id=started.public_id) == AccountRefusal.INACTIVE

    User.objects.filter(pk=user.pk).update(is_active=True)

    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.VERIFIED
    )


def test_email_case_change_alone_does_not_block(user: User) -> None:
    started = _started()
    User.objects.filter(pk=user.pk).update(email="ANA@X.com")

    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.VERIFIED
    )


GOOD_PASSWORD = "Kq7#mZ2!vR9p"
CompleteRefusal = password_reset.CompleteRefusal


def _validated() -> password_reset.Started:
    started = _started()
    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.VERIFIED
    )
    return started


def _account() -> User:
    return User.objects.get(email=EMAIL)


def test_complete_sets_the_password_verifies_the_email_and_deletes_the_request(
    user: User,
) -> None:
    started = _validated()

    result = password_reset.complete(public_id=started.public_id, password=GOOD_PASSWORD)

    assert result == password_reset.Completed(user=user)
    assert _account().check_password(GOOD_PASSWORD)
    assert not PasswordResetRequest.objects.exists()
    address = EmailAddress.objects.get(user=user)
    assert (address.email, address.verified, address.primary) == (EMAIL, True, True)


def test_complete_verifies_an_existing_unverified_address(user: User) -> None:
    EmailAddress.objects.create(user=user, email=EMAIL, verified=False, primary=True)
    started = _validated()

    password_reset.complete(public_id=started.public_id, password=GOOD_PASSWORD)

    address = EmailAddress.objects.get(user=user)
    assert (address.email, address.verified, address.primary) == (EMAIL, True, True)


def test_complete_does_not_steal_the_primary_flag(user: User) -> None:
    EmailAddress.objects.create(user=user, email="old@x.com", verified=True, primary=True)
    started = _validated()

    password_reset.complete(public_id=started.public_id, password=GOOD_PASSWORD)

    new = EmailAddress.objects.get(user=user, email=EMAIL)
    assert (new.verified, new.primary) == (True, False)
    assert EmailAddress.objects.get(user=user, email="old@x.com").primary


def test_complete_accepts_the_current_password(user: User) -> None:
    _change_password_to(user, GOOD_PASSWORD)
    started = _validated()

    result = password_reset.complete(public_id=started.public_id, password=GOOD_PASSWORD)

    assert isinstance(result, password_reset.Completed)
    assert _account().check_password(GOOD_PASSWORD)


def _change_password_to(user: User, password: str) -> None:
    user.set_password(password)
    user.save()


@pytest.mark.parametrize(
    ("password", "codes_expected"),
    [
        ("12345678", {"password_too_short", "password_too_common", "password_entirely_numeric"}),
        ("anagarcía1990", {"password_too_similar"}),
        ("ana@x.com.1990", {"password_too_similar"}),
    ],
)
def test_complete_rejects_a_password_against_the_policy(
    user: User, password: str, codes_expected: set[str]
) -> None:
    started = _validated()

    with pytest.raises(ValidationError) as excinfo:
        password_reset.complete(public_id=started.public_id, password=password)

    assert codes_expected <= {error.code for error in excinfo.value.error_list}
    assert _account().check_password(DEFAULT_PASSWORD)
    assert _stored().public_id == started.public_id
    assert not EmailAddress.objects.exists()


def test_complete_requires_the_validated_code(user: User) -> None:
    started = _started()

    assert password_reset.complete(public_id=started.public_id, password=GOOD_PASSWORD) == (
        CompleteRefusal.CODE_NOT_VERIFIED
    )
    assert _account().check_password(DEFAULT_PASSWORD)
    assert PasswordResetRequest.objects.exists()


@pytest.mark.parametrize("aged", [{"code_expires_at": 16}, {"created_at": 61}])
def test_complete_rejects_an_expired_request(user: User, aged: dict[str, int]) -> None:
    started = _validated()
    _age(**aged)

    assert password_reset.complete(public_id=started.public_id, password=GOOD_PASSWORD) == (
        CompleteRefusal.EXPIRED
    )
    assert _account().check_password(DEFAULT_PASSWORD)


def test_complete_after_code_expiry_within_the_grace_period(user: User) -> None:
    started = _validated()
    _age(code_expires_at=10)

    result = password_reset.complete(public_id=started.public_id, password=GOOD_PASSWORD)

    assert isinstance(result, password_reset.Completed)


def test_complete_of_an_unknown_request_is_not_found(user: User) -> None:
    assert password_reset.complete(public_id="unknown", password=GOOD_PASSWORD) == (
        CompleteRefusal.NOT_FOUND
    )


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        (_deactivate, AccountRefusal.INACTIVE),
        (_change_email, AccountRefusal.ACCOUNT_CHANGED),
        (_change_password, AccountRefusal.ACCOUNT_CHANGED),
    ],
)
def test_account_changes_block_complete(user: User, change: Any, refusal: AccountRefusal) -> None:
    started = _validated()
    change(user)
    password_before = User.objects.get(pk=user.pk).password

    assert password_reset.complete(public_id=started.public_id, password=GOOD_PASSWORD) == refusal

    assert User.objects.get(pk=user.pk).password == password_before
    assert _stored().public_id == started.public_id
    assert not EmailAddress.objects.exists()


def test_complete_is_not_found_if_the_request_changed_before_locking(
    user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    started = _validated()
    other = make_user()
    monkeypatch.setattr(password_reset, "_owner_id", lambda _public_id: other.pk)

    assert password_reset.complete(public_id=started.public_id, password=GOOD_PASSWORD) == (
        CompleteRefusal.NOT_FOUND
    )
    assert _account().check_password(DEFAULT_PASSWORD)


def test_purge_deletes_only_expired_requests_and_no_pending_registrations() -> None:
    for email in ("alive@x.com", "grace@x.com", "lifetime@x.com"):
        make_user(email=email)
        _started(email)
    now = timezone.now()
    PasswordResetRequest.objects.filter(user__email="grace@x.com").update(
        code_expires_at=now - timedelta(minutes=16)
    )
    PasswordResetRequest.objects.filter(user__email="lifetime@x.com").update(
        created_at=now - timedelta(minutes=61)
    )
    pending = registration.start(
        email="new@x.com", name="Nuevo", birthdate=date(1990, 1, 1), country="ES"
    )
    assert isinstance(pending, registration.Started)
    PendingRegistration.objects.update(created_at=now - timedelta(minutes=61))

    assert password_reset.purge_expired() == 2

    assert list(PasswordResetRequest.objects.values_list("user__email", flat=True)) == [
        "alive@x.com"
    ]
    assert PendingRegistration.objects.count() == 1
    assert password_reset.purge_expired() == 0


@override_settings(REGISTRATION_MAX_FAILED_ATTEMPTS=2)
def test_lock_follows_the_shared_setting(user: User) -> None:
    started = _started()
    for _ in range(2):
        password_reset.verify(public_id=started.public_id, code=_wrong(started.code))

    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.LOCKED
    )


@override_settings(REGISTRATION_CODE_TTL_MINUTES=5, REGISTRATION_GRACE_MINUTES=2)
def test_code_lifetime_and_grace_follow_the_shared_settings(user: User) -> None:
    started = _started()
    remaining = _stored().code_expires_at - timezone.now()
    assert timedelta(minutes=4) < remaining <= timedelta(minutes=5)

    _age(code_expires_at=1)
    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.CODE_EXPIRED
    )
    _age(code_expires_at=3)
    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.EXPIRED
    )


@override_settings(REGISTRATION_MAX_LIFETIME_MINUTES=10)
def test_request_lifetime_follows_the_shared_setting(user: User) -> None:
    started = _started()
    _age(created_at=11)

    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        VerifyResult.EXPIRED
    )


def test_complete_is_all_or_nothing(user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    started = _validated()

    def fail(_user: User) -> None:
        raise IntegrityError("unique_verified_email")

    monkeypatch.setattr(password_reset, "_mark_email_verified", fail)

    with pytest.raises(IntegrityError):
        password_reset.complete(public_id=started.public_id, password=GOOD_PASSWORD)

    assert _account().check_password(DEFAULT_PASSWORD)
    assert _stored().public_id == started.public_id
    assert not EmailAddress.objects.exists()


def test_public_ids_do_not_cross_between_processes(user: User) -> None:
    reset = _validated()
    pending = registration.start(
        email="new@x.com", name="Nuevo", birthdate=date(1990, 1, 1), country="ES"
    )
    assert isinstance(pending, registration.Started)
    assert registration.verify(public_id=pending.public_id, code=pending.code) == (
        VerifyResult.VERIFIED
    )
    reset_before = _stored()
    pending_before = PendingRegistration.objects.get()

    assert registration.verify(public_id=reset.public_id, code=reset.code) == (
        VerifyResult.NOT_FOUND
    )
    assert registration.resend(public_id=reset.public_id) == registration.ResendRefusal.NOT_FOUND
    assert registration.complete(public_id=reset.public_id, password=GOOD_PASSWORD) == (
        registration.CompleteRefusal.NOT_FOUND
    )
    assert password_reset.complete(public_id=pending.public_id, password=GOOD_PASSWORD) == (
        CompleteRefusal.NOT_FOUND
    )

    reset_after = _stored()
    pending_after = PendingRegistration.objects.get()
    fields = ("public_id", "code_hash", "failed_attempts", "code_validated_at")
    for field in fields:
        assert getattr(reset_after, field) == getattr(reset_before, field)
        assert getattr(pending_after, field) == getattr(pending_before, field)
    assert _account().check_password(DEFAULT_PASSWORD)
    assert list(User.objects.values_list("email", flat=True)) == [EMAIL]
