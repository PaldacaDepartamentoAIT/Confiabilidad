from collections.abc import Callable
from datetime import timedelta
from typing import Any
from unittest import mock

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts import registration, tasks
from apps.accounts.models import PendingRegistration, PhantomProcess, User
from apps.accounts.tests.factories import DEFAULT_PROFILE, code_sent_to, make_pending, make_user
from apps.emails.models import OutboundEmail

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


def _resend(public_id: str) -> object:
    result = registration.resend(public_id=public_id)
    return "resent" if result == registration.Resent(public_id=public_id) else result


def _resend_after_lock_journey(public_id: str) -> list[object]:
    locked = [_verify(public_id) for _ in range(6)]
    resent = _resend(public_id)
    before_reissue = _verify(public_id)
    registration.reissue_code(public_id)
    return [*locked, resent, before_reissue, _verify(public_id), _complete(public_id)]


def _resend_with_an_expired_code_journey(public_id: str) -> list[object]:
    _age(code_expires_at=1)
    resent = _resend(public_id)
    before_reissue = _verify(public_id)
    registration.reissue_code(public_id)
    return [resent, before_reissue, _verify(public_id)]


def _resend_after_grace_journey(public_id: str) -> list[object]:
    _age(code_expires_at=16)
    return [_resend(public_id)]


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
    (
        _resend_after_lock_journey,
        [
            *["wrong_code"] * 5,
            "locked",
            "resent",
            "wrong_code",
            "wrong_code",
            registration.CompleteRefusal.CODE_NOT_VERIFIED,
        ],
    ),
    (_resend_with_an_expired_code_journey, ["resent", "code_expired", "wrong_code"]),
    (_resend_after_grace_journey, [registration.ResendRefusal.EXPIRED]),
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


@pytest.mark.parametrize(
    "action", [_verify, _resend, _complete], ids=["verify", "resend", "complete"]
)
def test_each_step_does_the_same_queries_for_a_phantom_and_a_registration(
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
    assert _resend(public_id) == registration.ResendRefusal.NOT_FOUND
    assert _complete(public_id) == registration.CompleteRefusal.NOT_FOUND


def test_a_phantom_never_completes_even_if_marked_as_verified() -> None:
    public_id = _phantom()
    PhantomProcess.objects.update(code_validated_at=timezone.now())

    assert _complete(public_id) == registration.CompleteRefusal.CODE_NOT_VERIFIED
    assert User.objects.count() == 1


@pytest.mark.parametrize("source", SOURCES)
def test_resend_queues_the_reissue_once_committed(
    source: Callable[[], str], django_capture_on_commit_callbacks: Any
) -> None:
    public_id = source()
    with mock.patch("celery.current_app.send_task") as send_task:
        with django_capture_on_commit_callbacks() as callbacks:
            registration.resend(public_id=public_id)
        send_task.assert_not_called()
        for callback in callbacks:
            callback()

    send_task.assert_called_once_with(
        "apps.accounts.tasks.reissue_code", args=["registration", public_id]
    )


def test_resend_answers_and_warns_when_the_queue_is_down(
    django_capture_on_commit_callbacks: Any, caplog: pytest.LogCaptureFixture
) -> None:
    public_id = _real()
    with mock.patch("celery.current_app.send_task", side_effect=ConnectionError("down")):
        with django_capture_on_commit_callbacks(execute=True):
            result = registration.resend(public_id=public_id)

    assert result == registration.Resent(public_id=public_id)
    assert any(record.levelname == "WARNING" for record in caplog.records)


def test_the_previous_code_stops_serving_as_soon_as_a_resend_is_asked() -> None:
    started = make_pending(EMAIL)

    registration.resend(public_id=started.public_id)

    assert registration.verify(public_id=started.public_id, code=started.code) == "wrong_code"
    registration.reissue_code(started.public_id)
    new_code = code_sent_to(started.public_id)
    if new_code != started.code:
        assert registration.verify(public_id=started.public_id, code=started.code) == "wrong_code"
    assert registration.verify(public_id=started.public_id, code=new_code) == "verified"


def test_the_task_emails_a_new_code_for_a_real_registration() -> None:
    public_id = _real()
    PendingRegistration.objects.update(language="en")
    registration.resend(public_id=public_id)

    tasks.reissue_code.apply(args=["registration", public_id])

    email = OutboundEmail.objects.order_by("-pk").first()
    assert email is not None
    assert (email.kind, email.public_id, email.locale, email.recipient) == (
        "registration_code",
        public_id,
        "en",
        EMAIL,
    )
    assert PendingRegistration.objects.get().code_hash != ""


def test_the_task_gives_a_phantom_a_new_code_without_any_email() -> None:
    public_id = _phantom()
    emails = OutboundEmail.objects.count()
    registration.resend(public_id=public_id)

    tasks.reissue_code.apply(args=["registration", public_id])

    assert OutboundEmail.objects.count() == emails
    assert PhantomProcess.objects.get().code_hash != ""


@pytest.mark.parametrize(
    "prepare",
    [
        pytest.param(lambda: _age(created_at=61), id="expired"),
        pytest.param(
            lambda: PendingRegistration.objects.update(code_validated_at=timezone.now()),
            id="verified",
        ),
        pytest.param(lambda: PendingRegistration.objects.all().delete(), id="gone"),
    ],
)
def test_the_task_issues_nothing_for_a_process_that_no_longer_takes_codes(
    prepare: Callable[[], object],
) -> None:
    public_id = _real()
    registration.resend(public_id=public_id)
    emails = OutboundEmail.objects.count()
    prepare()

    registration.reissue_code(public_id)

    assert OutboundEmail.objects.count() == emails
    assert not PendingRegistration.objects.exclude(code_hash="").exists()


@pytest.mark.parametrize("has_account", [False, True])
def test_the_newest_request_wins_even_if_the_tasks_run_out_of_order(has_account: bool) -> None:
    if has_account:
        make_user(email=EMAIL)
    older = registration.start(email=EMAIL, **DEFAULT_PROFILE).public_id
    newer = registration.start(email=EMAIL, **DEFAULT_PROFILE).public_id

    registration.resolve_registration(older)
    registration.resolve_registration(newer)

    assert [_verify(older), _verify(newer)] == ["not_found", "wrong_code"]
    assert list(OutboundEmail.objects.values_list("public_id", flat=True)) == (
        [""] if has_account else [newer]
    )
