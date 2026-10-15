from collections.abc import Callable
from datetime import timedelta
from typing import Any

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts import password_reset, registration
from apps.accounts.models import PasswordResetRequest, PhantomProcess, User
from apps.accounts.tests.factories import (
    DEFAULT_PROFILE,
    make_pending,
    make_reset_request,
    make_user,
)

pytestmark = pytest.mark.django_db

EMAIL = "eva@x.com"
GOOD_PASSWORD = "Kq7#mZ2!vR9p"
WRONG = "000000"
CompleteRefusal = password_reset.CompleteRefusal


def _phantom() -> str:
    # Correo sin cuenta: la plaza queda como identificador sin solicitud detrás.
    started = password_reset.start(email=EMAIL)
    password_reset.resolve_password_reset(started.public_id)
    assert PhantomProcess.objects.filter(public_id=started.public_id, payload__isnull=True).exists()
    return started.public_id


def _real() -> str:
    # Solicitud real cuyo código nunca se acierta.
    make_user(email=EMAIL)
    started = make_reset_request(EMAIL)
    assert started.code != WRONG
    return started.public_id


SOURCES = [pytest.param(_phantom, id="phantom"), pytest.param(_real, id="real")]


def _age(**minutes_ago: int) -> None:
    changes = {field: timezone.now() - timedelta(minutes=m) for field, m in minutes_ago.items()}
    PasswordResetRequest.objects.update(**changes)
    PhantomProcess.objects.update(**changes)


def _verify(public_id: str) -> str:
    return password_reset.verify(public_id=public_id, code=WRONG)


def _complete(public_id: str) -> object:
    return password_reset.complete(public_id=public_id, password=GOOD_PASSWORD)


def _lock_journey(public_id: str) -> list[object]:
    return [*(_verify(public_id) for _ in range(6)), _complete(public_id)]


def _code_expiry_journey(public_id: str) -> list[object]:
    first = _verify(public_id)
    _age(code_expires_at=1)
    return [first, _verify(public_id), _complete(public_id)]


def _grace_journey(public_id: str) -> list[object]:
    _age(code_expires_at=16)
    return [_verify(public_id), _complete(public_id)]


def _lifetime_journey(public_id: str) -> list[object]:
    _verify(public_id)
    _age(created_at=61)
    return [_verify(public_id), _complete(public_id)]


def _replaced_journey(public_id: str) -> list[object]:
    again = password_reset.start(email=EMAIL)
    password_reset.resolve_password_reset(again.public_id)
    return [_verify(public_id), _complete(public_id), _verify(again.public_id)]


JOURNEYS: list[tuple[Callable[[str], list[object]], list[object]]] = [
    (_lock_journey, [*["wrong_code"] * 5, "locked", CompleteRefusal.CODE_NOT_VERIFIED]),
    (
        _code_expiry_journey,
        ["wrong_code", "code_expired", CompleteRefusal.CODE_NOT_VERIFIED],
    ),
    (_grace_journey, ["expired", CompleteRefusal.EXPIRED]),
    (_lifetime_journey, ["expired", CompleteRefusal.EXPIRED]),
    (_replaced_journey, ["not_found", CompleteRefusal.NOT_FOUND, "wrong_code"]),
]


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize(
    ("journey", "expected"),
    [
        pytest.param(journey, expected, id=journey.__name__.strip("_"))
        for journey, expected in JOURNEYS
    ],
)
def test_a_phantom_answers_like_a_request_whose_code_is_never_guessed(
    source: Callable[[], str],
    journey: Callable[[str], list[object]],
    expected: list[object],
) -> None:
    assert journey(source()) == expected


def _queries(source: Callable[[], str], action: Callable[[str], Any]) -> int:
    public_id = source()
    with CaptureQueriesContext(connection) as queries:
        action(public_id)
    return len(queries.captured_queries)


@pytest.mark.parametrize("action", [_verify, _complete], ids=["verify", "complete"])
def test_each_step_does_the_same_queries_for_a_phantom_and_a_request(
    action: Callable[[str], Any],
) -> None:
    phantom = _queries(_phantom, action)
    PhantomProcess.objects.all().delete()

    assert _queries(_real, action) == phantom


def _deactivate() -> None:
    User.objects.update(is_active=False)


def _change_email() -> None:
    User.objects.update(email="nueva@x.com")


def _change_password() -> None:
    user = User.objects.get()
    user.set_password("another-long-passw0rd")
    user.save()


def _delete_account() -> None:
    User.objects.all().delete()


@pytest.mark.parametrize(
    "change",
    [_deactivate, _change_email, _change_password, _delete_account],
    ids=["inactive", "email-changed", "password-changed", "deleted"],
)
def test_an_account_change_answers_like_an_expired_request(change: Callable[[], None]) -> None:
    public_id = _real()
    change()

    assert [_verify(public_id), _complete(public_id)] == ["expired", CompleteRefusal.EXPIRED]


def test_the_tombstone_keeps_answering_expired_until_it_is_purged() -> None:
    public_id = _real()
    _delete_account()

    assert _verify(public_id) == "expired"
    assert PhantomProcess.objects.get().failed_attempts == 0


def test_registration_ids_do_not_serve_here() -> None:
    pending = make_pending("ana@x.com").public_id
    make_user(email="bea@x.com")
    slot = registration.start(email="bea@x.com", **DEFAULT_PROFILE).public_id
    registration.resolve_registration(slot)

    for public_id in (pending, slot):
        assert _verify(public_id) == "not_found"
        assert _complete(public_id) == CompleteRefusal.NOT_FOUND


def test_a_phantom_never_completes_even_if_marked_as_verified() -> None:
    public_id = _phantom()
    PhantomProcess.objects.update(code_validated_at=timezone.now())

    assert _complete(public_id) == CompleteRefusal.CODE_NOT_VERIFIED
