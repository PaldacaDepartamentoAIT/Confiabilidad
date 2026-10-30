from collections.abc import Callable
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts import registration
from apps.accounts.models import PendingRegistration, PhantomProcess
from apps.accounts.tests.factories import DEFAULT_PROFILE, StartedWithCode, make_pending, make_user

pytestmark = pytest.mark.django_db

EMAIL = "ana@x.com"
Result = registration.VerifyResult


def _wrong(code: str) -> str:
    return "000000" if code != "000000" else "111111"


def _validated() -> StartedWithCode:
    started = make_pending(EMAIL)
    assert registration.verify_code(public_id=started.public_id, code=started.code) is (
        Result.VERIFIED
    )
    return started


def _stored() -> PendingRegistration:
    return PendingRegistration.objects.get()


def _age(**minutes_ago: int) -> None:
    changes = {field: timezone.now() - timedelta(minutes=m) for field, m in minutes_ago.items()}
    PendingRegistration.objects.update(**changes)
    PhantomProcess.objects.update(**changes)


def test_right_code_validates_the_registration() -> None:
    started = make_pending(EMAIL)

    result = registration.verify_code(public_id=started.public_id, code=started.code)

    assert result is Result.VERIFIED
    assert _stored().code_validated_at is not None


def test_a_validated_code_is_accepted_again_without_changes() -> None:
    started = _validated()
    before = _stored()

    result = registration.verify_code(public_id=started.public_id, code=started.code)

    after = _stored()
    assert result is Result.VERIFIED
    assert (after.failed_attempts, after.code_validated_at) == (0, before.code_validated_at)


def test_a_validated_code_is_accepted_again_during_the_grace_period() -> None:
    started = _validated()
    _age(code_expires_at=1)

    result = registration.verify_code(public_id=started.public_id, code=started.code)

    assert result is Result.VERIFIED


def test_a_wrong_code_on_a_validated_registration_counts_an_attempt() -> None:
    started = _validated()

    result = registration.verify_code(public_id=started.public_id, code=_wrong(started.code))

    assert result is Result.WRONG_CODE
    assert _stored().failed_attempts == 1


def test_a_wrong_code_on_a_validated_registration_with_an_expired_code_is_not_counted() -> None:
    started = _validated()
    _age(code_expires_at=1)

    result = registration.verify_code(public_id=started.public_id, code=_wrong(started.code))

    assert result is Result.CODE_EXPIRED
    assert _stored().failed_attempts == 0


def test_a_locked_validated_registration_rejects_even_the_right_code() -> None:
    started = _validated()
    PendingRegistration.objects.update(failed_attempts=5)

    result = registration.verify_code(public_id=started.public_id, code=started.code)

    assert result is Result.LOCKED


def test_an_expired_validated_registration_rejects_even_the_right_code() -> None:
    started = _validated()
    _age(code_expires_at=20)

    result = registration.verify_code(public_id=started.public_id, code=started.code)

    assert result is Result.EXPIRED


def test_an_unknown_public_id_is_not_found() -> None:
    assert registration.verify_code(public_id="unknown", code="123456") is Result.NOT_FOUND


def _phantom() -> str:
    make_user(email=EMAIL)
    started = registration.start(email=EMAIL, **DEFAULT_PROFILE)
    registration.resolve_registration(started.public_id)
    return started.public_id


def _real() -> str:
    started = make_pending(EMAIL)
    assert started.code != "000000"
    return started.public_id


def _journey(public_id: str) -> list[Result]:
    results = [registration.verify_code(public_id=public_id, code="000000") for _ in range(6)]
    _age(code_expires_at=1)
    results.append(registration.verify_code(public_id=public_id, code="000000"))
    PendingRegistration.objects.update(failed_attempts=0)
    PhantomProcess.objects.update(failed_attempts=0)
    results.append(registration.verify_code(public_id=public_id, code="000000"))
    _age(code_expires_at=20)
    results.append(registration.verify_code(public_id=public_id, code="000000"))
    return results


@pytest.mark.parametrize("source", [_phantom, _real], ids=["phantom", "real"])
def test_a_phantom_answers_like_a_registration_whose_code_is_never_guessed(
    source: Callable[[], str],
) -> None:
    assert _journey(source()) == [
        *[Result.WRONG_CODE] * 5,
        Result.LOCKED,
        Result.LOCKED,
        Result.CODE_EXPIRED,
        Result.EXPIRED,
    ]


def test_a_new_slot_is_sent_now_without_resends() -> None:
    before = timezone.now()

    started = registration.start(email=EMAIL, **DEFAULT_PROFILE)

    slot = PhantomProcess.objects.get(public_id=started.public_id)
    assert slot.resend_count == 0
    assert slot.last_sent_at is not None and before <= slot.last_sent_at <= timezone.now()


def _resolved() -> PendingRegistration | PhantomProcess:
    # Envejece los contadores antes de resolver para ver que la resolución los pone al día.
    started = registration.start(email=EMAIL, **DEFAULT_PROFILE)
    PhantomProcess.objects.update(resend_count=3, last_sent_at=timezone.now() - timedelta(hours=1))
    PendingRegistration.objects.update(
        resend_count=3, last_sent_at=timezone.now() - timedelta(hours=1)
    )
    before = timezone.now()
    registration.resolve_registration(started.public_id)
    process = PendingRegistration.objects.filter(
        public_id=started.public_id
    ).first() or PhantomProcess.objects.get(public_id=started.public_id)
    assert process.last_sent_at is not None and before <= process.last_sent_at
    return process


def _with_account() -> str:
    make_user(email=EMAIL)
    return EMAIL


def _with_pending() -> str:
    make_pending(EMAIL)
    return EMAIL


@pytest.mark.parametrize(
    "prepare",
    [lambda: EMAIL, _with_pending, _with_account],
    ids=["new", "repeated", "account"],
)
def test_resolving_resets_the_resend_counters(prepare: Callable[[], str]) -> None:
    prepare()

    process = _resolved()

    assert process.resend_count == 0
