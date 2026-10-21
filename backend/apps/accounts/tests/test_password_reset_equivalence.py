import threading
import time
from collections.abc import Callable
from datetime import timedelta
from typing import Any
from unittest import mock

import pytest
from django.db import connection
from django.db.models import F
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts import password_reset, registration, tasks
from apps.accounts.models import PasswordResetRequest, PhantomProcess, User
from apps.accounts.tests.factories import (
    DEFAULT_PROFILE,
    code_sent_to,
    make_pending,
    make_reset_request,
    make_user,
)
from apps.emails import outbox
from apps.emails.models import OutboundEmail

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


def _inactive() -> str:
    # Cuenta inactiva sin solicitud: la plaza queda como identificador sin solicitud detrás.
    make_user(email=EMAIL, is_active=False)
    return _phantom()


def _inactive_with_request() -> str:
    # Cuenta con una solicitud anterior que después se desactiva.
    make_user(email=EMAIL)
    make_reset_request(EMAIL)
    User.objects.update(is_active=False)
    return _phantom()


PHANTOMS = [
    pytest.param(_phantom, id="phantom"),
    pytest.param(_inactive, id="inactive"),
    pytest.param(_inactive_with_request, id="inactive-with-request"),
]
SOURCES = [*PHANTOMS, pytest.param(_real, id="real")]


def _age(**minutes_ago: int) -> None:
    changes = {field: timezone.now() - timedelta(minutes=m) for field, m in minutes_ago.items()}
    PasswordResetRequest.objects.update(**changes)
    PhantomProcess.objects.update(**changes)


def _verify(public_id: str) -> str:
    return password_reset.verify(public_id=public_id, code=WRONG)


def _complete(public_id: str) -> object:
    return password_reset.complete(public_id=public_id, password=GOOD_PASSWORD)


def _resend(public_id: str) -> object:
    result = password_reset.resend(public_id=public_id)
    return "resent" if result == password_reset.Resent(public_id=public_id) else result


def _resend_after_lock_journey(public_id: str) -> list[object]:
    locked = [_verify(public_id) for _ in range(6)]
    resent = _resend(public_id)
    before_reissue = _verify(public_id)
    password_reset.reissue_code(public_id)
    return [*locked, resent, before_reissue, _verify(public_id), _complete(public_id)]


def _resend_with_an_expired_code_journey(public_id: str) -> list[object]:
    _age(code_expires_at=1)
    resent = _resend(public_id)
    before_reissue = _verify(public_id)
    password_reset.reissue_code(public_id)
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
    (
        _resend_after_lock_journey,
        [
            *["wrong_code"] * 5,
            "locked",
            "resent",
            "wrong_code",
            "wrong_code",
            CompleteRefusal.CODE_NOT_VERIFIED,
        ],
    ),
    (_resend_with_an_expired_code_journey, ["resent", "code_expired", "wrong_code"]),
    (_resend_after_grace_journey, [password_reset.ResendRefusal.EXPIRED]),
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


@pytest.mark.parametrize("source", PHANTOMS)
@pytest.mark.parametrize(
    "action", [_verify, _resend, _complete], ids=["verify", "resend", "complete"]
)
def test_each_step_does_the_same_queries_for_a_phantom_and_a_request(
    source: Callable[[], str], action: Callable[[str], Any]
) -> None:
    phantom = _queries(source, action)
    User.objects.all().delete()
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

    assert [_verify(public_id), _resend(public_id), _complete(public_id)] == [
        "expired",
        "expired",
        CompleteRefusal.EXPIRED,
    ]


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
        assert _resend(public_id) == password_reset.ResendRefusal.NOT_FOUND
        assert _complete(public_id) == CompleteRefusal.NOT_FOUND


def test_a_phantom_never_completes_even_if_marked_as_verified() -> None:
    public_id = _phantom()
    PhantomProcess.objects.update(code_validated_at=timezone.now())

    assert _complete(public_id) == CompleteRefusal.CODE_NOT_VERIFIED


@pytest.mark.parametrize("source", SOURCES)
def test_resend_queues_the_reissue_once_committed(
    source: Callable[[], str], django_capture_on_commit_callbacks: Any
) -> None:
    public_id = source()
    with mock.patch("celery.current_app.send_task") as send_task:
        with django_capture_on_commit_callbacks() as callbacks:
            password_reset.resend(public_id=public_id)
        send_task.assert_not_called()
        for callback in callbacks:
            callback()

    send_task.assert_called_once_with(
        "apps.accounts.tasks.reissue_code", args=["password_reset", public_id]
    )


def test_the_previous_code_stops_serving_as_soon_as_a_resend_is_asked() -> None:
    make_user(email=EMAIL)
    started = make_reset_request(EMAIL)

    password_reset.resend(public_id=started.public_id)

    assert password_reset.verify(public_id=started.public_id, code=started.code) == "wrong_code"
    password_reset.reissue_code(started.public_id)
    new_code = code_sent_to(started.public_id)
    if new_code != started.code:
        assert password_reset.verify(public_id=started.public_id, code=started.code) == (
            "wrong_code"
        )
    assert password_reset.verify(public_id=started.public_id, code=new_code) == "verified"


def test_the_task_emails_a_new_code_for_a_real_request_in_the_request_language() -> None:
    make_user(email=EMAIL, language="es", name="Eva Titular")
    public_id = make_reset_request(EMAIL, language="en").public_id
    password_reset.resend(public_id=public_id)

    tasks.reissue_code.apply(args=["password_reset", public_id])

    email = OutboundEmail.objects.order_by("-pk").first()
    assert email is not None
    assert (email.kind, email.public_id, email.locale, email.recipient, email.context) == (
        "password_reset_code",
        public_id,
        "en",
        EMAIL,
        {"name": "Eva Titular"},
    )
    assert PasswordResetRequest.objects.get().code_hash != ""


def test_the_task_gives_a_phantom_a_new_code_without_any_email() -> None:
    public_id = _phantom()
    password_reset.resend(public_id=public_id)

    tasks.reissue_code.apply(args=["password_reset", public_id])

    assert not OutboundEmail.objects.exists()
    assert PhantomProcess.objects.get().code_hash != ""


@pytest.mark.parametrize(
    "prepare",
    [
        pytest.param(lambda: _age(created_at=61), id="expired"),
        pytest.param(_deactivate, id="inactive"),
        pytest.param(
            lambda: PasswordResetRequest.objects.update(code_validated_at=timezone.now()),
            id="verified",
        ),
        pytest.param(_delete_account, id="deleted"),
    ],
)
def test_the_task_issues_nothing_for_a_process_that_no_longer_takes_codes(
    prepare: Callable[[], object],
) -> None:
    public_id = _real()
    password_reset.resend(public_id=public_id)
    emails = OutboundEmail.objects.count()
    prepare()

    password_reset.reissue_code(public_id)

    assert OutboundEmail.objects.count() == emails
    assert not PasswordResetRequest.objects.exclude(code_hash="").exists()
    assert not PhantomProcess.objects.exclude(code_hash="").exists()


@pytest.mark.parametrize("has_account", [False, True])
def test_the_newest_request_wins_even_if_the_tasks_run_out_of_order(has_account: bool) -> None:
    if has_account:
        make_user(email=EMAIL)
    older = password_reset.start(email=EMAIL).public_id
    newer = password_reset.start(email=EMAIL).public_id

    password_reset.resolve_password_reset(older)
    password_reset.resolve_password_reset(newer)

    assert [_verify(older), _verify(newer)] == ["not_found", "wrong_code"]
    assert list(OutboundEmail.objects.values_list("public_id", flat=True)) == (
        [newer] if has_account else []
    )
    assert list(PasswordResetRequest.objects.values_list("public_id", flat=True)) == (
        [newer] if has_account else []
    )


def _pass(minutes: int) -> None:
    # Simula el paso del tiempo moviendo hacia atrás todas las fechas guardadas (D-11).
    shift = timedelta(minutes=minutes)
    for model in (PasswordResetRequest, PhantomProcess):
        model.objects.update(
            created_at=F("created_at") - shift, code_expires_at=F("code_expires_at") - shift
        )


def _start(has_account: bool) -> str:
    if has_account and not User.objects.exists():
        make_user(email=EMAIL)
    return password_reset.start(email=EMAIL).public_id


def _attempts_before_resolving(has_account: bool) -> list[object]:
    public_id = _start(has_account)
    before = [_verify(public_id) for _ in range(3)]
    password_reset.resolve_password_reset(public_id)
    return [*before, *(_verify(public_id) for _ in range(3))]


def _delayed_resolution(has_account: bool) -> list[object]:
    public_id = _start(has_account)
    _pass(4)
    password_reset.resolve_password_reset(public_id)
    _pass(12)
    at_16 = _verify(public_id)
    _pass(15)
    return [at_16, _verify(public_id)]


def _delayed_resolution_then_lifetime(has_account: bool) -> list[object]:
    public_id = _start(has_account)
    _pass(4)
    password_reset.resolve_password_reset(public_id)
    for _ in range(4):
        _pass(12)
        _resend(public_id)
        password_reset.reissue_code(public_id)
    _pass(10)
    return [_verify(public_id)]


TIMED: list[tuple[Callable[[bool], list[object]], list[object]]] = [
    (_attempts_before_resolving, ["wrong_code"] * 6),
    (_delayed_resolution, ["wrong_code", "code_expired"]),
    (_delayed_resolution_then_lifetime, ["wrong_code"]),
]


@pytest.mark.parametrize("has_account", [True, False], ids=["real", "phantom"])
@pytest.mark.parametrize(
    ("sequence", "expected"),
    [
        pytest.param(sequence, expected, id=sequence.__name__.strip("_"))
        for sequence, expected in TIMED
    ],
)
def test_a_phantom_counts_attempts_and_time_like_a_request(
    has_account: bool,
    sequence: Callable[[bool], list[object]],
    expected: list[object],
) -> None:
    assert sequence(has_account) == expected


CONCURRENT: dict[str, tuple[Callable[[str], object], object]] = {
    "verify": (_verify, "wrong_code"),
    "resend": (_resend, "resent"),
    "complete": (_complete, CompleteRefusal.CODE_NOT_VERIFIED),
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("has_account", [True, False], ids=["real", "phantom"])
@pytest.mark.parametrize("action", list(CONCURRENT))
def test_an_operation_during_the_resolution_answers_like_after_it(
    has_account: bool, action: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # La resolución se detiene dentro de su transacción mientras otra conexión opera con el mismo
    # identificador (D-05). Sin cuenta no encola correo: se detiene al guardar la plaza.
    monkeypatch.setattr("celery.current_app.send_task", mock.Mock())
    if has_account:
        make_user(email=EMAIL)
    public_id = password_reset.start(email=EMAIL).public_id
    paused, release = threading.Event(), threading.Event()

    def pause_then(real: Callable[..., Any]) -> Callable[..., Any]:
        def paused_call(*args: Any, **kwargs: Any) -> Any:
            paused.set()
            release.wait(10)
            return real(*args, **kwargs)

        return paused_call

    if has_account:
        monkeypatch.setattr(outbox, "enqueue", pause_then(outbox.enqueue))
    else:
        monkeypatch.setattr(
            password_reset, "_leave_as_issued", pause_then(password_reset._leave_as_issued)
        )
    operation, expected = CONCURRENT[action]
    results: dict[str, object] = {}

    def in_own_connection(name: str, work: Callable[[], object]) -> Callable[[], None]:
        def run() -> None:
            try:
                results[name] = work()
            finally:
                connection.close()

        return run

    resolver = threading.Thread(
        target=in_own_connection(
            "resolve", lambda: password_reset.resolve_password_reset(public_id)
        )
    )
    resolver.start()
    assert paused.wait(10)
    other = threading.Thread(target=in_own_connection(action, lambda: operation(public_id)))
    other.start()
    time.sleep(0.5)
    release.set()
    resolver.join(10)
    other.join(10)

    assert results == {"resolve": None, action: expected}


@pytest.mark.parametrize("has_account", [True, False], ids=["real", "phantom"])
@pytest.mark.parametrize(
    ("first", "second", "account"),
    [
        ("ſam@x.com", "sam@x.com", "sam@x.com"),
        ("sam@x.com", "ſam@x.com", "sam@x.com"),
        ("ana@gmaıl.com", "ana@gmail.com", "ana@gmail.com"),
    ],
)
def test_a_unicode_variant_of_the_email_counts_as_the_same_request(
    has_account: bool, first: str, second: str, account: str
) -> None:
    if has_account:
        make_user(email=account)
    older = password_reset.start(email=first).public_id
    password_reset.resolve_password_reset(older)
    newer = password_reset.start(email=second).public_id
    password_reset.resolve_password_reset(newer)

    assert [_verify(older), _verify(newer)] == ["not_found", "wrong_code"]
