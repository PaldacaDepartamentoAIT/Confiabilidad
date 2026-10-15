from collections.abc import Callable
from datetime import timedelta
from typing import Any

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts import registration
from apps.accounts.models import PendingRegistration, PhantomProcess, User
from apps.accounts.tests.factories import DEFAULT_PROFILE, make_pending, make_user

pytestmark = pytest.mark.django_db

EMAIL = "ana@x.com"
GOOD_PASSWORD = "Kq7#mZ2!vR9p"
WRONG = "000000"


def _phantom() -> str:
    # Correo con cuenta: la plaza queda como identificador sin registro detrás.
    make_user(email=EMAIL)
    started = registration.start(email=EMAIL, **DEFAULT_PROFILE)
    registration.resolve_registration(started.public_id)
    assert PhantomProcess.objects.filter(public_id=started.public_id, payload__isnull=True).exists()
    return started.public_id


def _real() -> str:
    # Registro real cuyo código nunca se acierta.
    started = make_pending(EMAIL)
    assert started.code != WRONG
    return started.public_id


SOURCES = [pytest.param(_phantom, id="phantom"), pytest.param(_real, id="real")]


def _age(**minutes_ago: int) -> None:
    changes = {field: timezone.now() - timedelta(minutes=m) for field, m in minutes_ago.items()}
    PendingRegistration.objects.update(**changes)
    PhantomProcess.objects.update(**changes)


def _verify(public_id: str) -> str:
    return registration.verify(public_id=public_id, code=WRONG)


def _complete(public_id: str) -> object:
    return registration.complete(public_id=public_id, password=GOOD_PASSWORD)


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
    again = registration.start(email=EMAIL, **DEFAULT_PROFILE)
    registration.resolve_registration(again.public_id)
    return [_verify(public_id), _complete(public_id), _verify(again.public_id)]


JOURNEYS: list[tuple[Callable[[str], list[object]], list[object]]] = [
    (
        _lock_journey,
        [*["wrong_code"] * 5, "locked", registration.CompleteRefusal.CODE_NOT_VERIFIED],
    ),
    (
        _code_expiry_journey,
        ["wrong_code", "code_expired", registration.CompleteRefusal.CODE_NOT_VERIFIED],
    ),
    (_grace_journey, ["expired", registration.CompleteRefusal.EXPIRED]),
    (_lifetime_journey, ["expired", registration.CompleteRefusal.EXPIRED]),
    (
        _replaced_journey,
        ["not_found", registration.CompleteRefusal.NOT_FOUND, "wrong_code"],
    ),
]


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize(
    ("journey", "expected"),
    [
        pytest.param(journey, expected, id=journey.__name__.strip("_"))
        for journey, expected in JOURNEYS
    ],
)
def test_a_phantom_answers_like_a_registration_whose_code_is_never_guessed(
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
def test_verify_and_complete_do_the_same_queries_for_a_phantom_and_a_registration(
    action: Callable[[str], Any],
) -> None:
    phantom = _queries(_phantom, action)
    User.objects.all().delete()
    PhantomProcess.objects.all().delete()

    assert _queries(_real, action) == phantom


def test_a_slot_of_another_purpose_is_not_found() -> None:
    public_id = _phantom()
    PhantomProcess.objects.update(purpose=PhantomProcess.Purpose.PASSWORD_RESET)

    assert _verify(public_id) == "not_found"
    assert _complete(public_id) == registration.CompleteRefusal.NOT_FOUND


def test_a_phantom_never_completes_even_if_marked_as_verified() -> None:
    public_id = _phantom()
    PhantomProcess.objects.update(code_validated_at=timezone.now())

    assert _complete(public_id) == registration.CompleteRefusal.CODE_NOT_VERIFIED
    assert User.objects.count() == 1
