import importlib
import logging
import smtplib
from datetime import timedelta
from typing import Any
from unittest import mock

import pytest
from django.apps import apps as global_apps
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from apps.core import fingerprints
from apps.emails import delivery, outbox, tasks
from apps.emails.models import OutboundEmail
from apps.emails.tests.backends import FAKE_BACKEND, FakeBackend

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _environment(settings: Any) -> None:
    settings.EMAIL_BACKEND = FAKE_BACKEND
    settings.DEFAULT_FROM_EMAIL = "no-responder@notificaciones.ejemplo.com"
    settings.EMAIL_SUPPORT_ADDRESS = "ayuda@ejemplo.com"
    settings.FRONTEND_BASE_URL = "https://app.ejemplo.com"
    FakeBackend.reset()
    migration = importlib.import_module("apps.emails.migrations.0002_initial_templates")
    migration.create_initial_templates(global_apps, None)


class _Checker:
    def __init__(self) -> None:
        self.expiry: Any = timezone.now() + timedelta(minutes=10)
        self.calls: list[tuple[str, str]] = []

    def __call__(self, public_id: str, code: str) -> Any:
        self.calls.append((public_id, code))
        return self.expiry


@pytest.fixture(autouse=True)
def checker() -> Any:
    current = _Checker()
    with mock.patch.dict(delivery._CODE_CHECKS, {"registration": current}, clear=True):
        yield current


@pytest.fixture
def send_task() -> Any:
    with mock.patch("celery.current_app.send_task") as patched:
        yield patched


def _pending(kind: str = "password_changed", locale: str = "es", **fields: Any) -> OutboundEmail:
    return OutboundEmail.objects.create(
        kind=kind, locale=locale, recipient="ana@example.com", context={"name": "Ana"}, **fields
    )


def test_delivering_sends_the_template_of_its_kind_and_language_and_forgets_the_email() -> None:
    email = _pending(locale="pt-BR")

    delivery.deliver(email.pk)

    [message] = FakeBackend.sent
    assert message.to == ["ana@example.com"]
    assert message.from_email == "no-responder@notificaciones.ejemplo.com"
    assert message.subject == "Sua senha foi alterada"
    assert message.body.startswith("Olá, Ana:")
    assert "ayuda@ejemplo.com" in message.body
    assert not OutboundEmail.objects.filter(pk=email.pk).exists()


def test_a_delivered_email_has_no_unsubscribe_header_or_link() -> None:
    delivery.deliver(_pending().pk)

    [message] = FakeBackend.sent
    headers = {name.lower() for name in message.extra_headers}
    assert "list-unsubscribe" not in headers
    assert "list-unsubscribe" not in str(message.message()).lower()
    assert "baja" not in message.body.lower()


def test_an_email_that_is_not_due_yet_is_not_delivered() -> None:
    email = _pending(next_attempt_at=timezone.now() + timedelta(minutes=1))

    delivery.deliver(email.pk)

    assert FakeBackend.sent == []
    assert OutboundEmail.objects.filter(pk=email.pk).exists()


def test_a_missing_email_is_ignored() -> None:
    delivery.deliver(123456789)

    assert FakeBackend.sent == []


def test_the_sweep_queues_only_the_pending_emails_that_are_due(send_task: Any) -> None:
    due = _pending()
    _pending(next_attempt_at=timezone.now() + timedelta(minutes=1))
    _pending(status=OutboundEmail.Status.FAILED)

    queued = delivery.dispatch_due()

    assert queued == 1
    send_task.assert_called_once_with(outbox.DELIVER_TASK, args=[due.pk])


def test_an_email_left_pending_by_a_queue_outage_goes_out_on_the_next_sweep(
    send_task: Any, django_capture_on_commit_callbacks: Any
) -> None:
    send_task.side_effect = ConnectionError("broker down")
    with django_capture_on_commit_callbacks(execute=True):
        email = outbox.enqueue(
            kind="account_disabled",
            recipient="ana@example.com",
            locale="en",
            context={"name": "Ana"},
        )
    assert email is not None
    send_task.side_effect = None
    send_task.reset_mock()

    delivery.dispatch_due()
    [call] = send_task.call_args_list
    tasks.deliver(*call.kwargs["args"])

    assert [message.subject for message in FakeBackend.sent] == ["Your account has been disabled"]
    assert not OutboundEmail.objects.filter(pk=email.pk).exists()


def test_the_tasks_are_registered_under_the_names_the_outbox_uses() -> None:
    assert tasks.deliver.name == outbox.DELIVER_TASK
    assert tasks.dispatch_due.name == "apps.emails.tasks.dispatch_due"


def test_the_sweep_task_returns_how_many_emails_it_queued(send_task: Any) -> None:
    _pending()

    assert tasks.dispatch_due() == 1


def _due_now(email: OutboundEmail) -> None:
    OutboundEmail.objects.filter(pk=email.pk).update(next_attempt_at=timezone.now())


def _wait_after_failure(attempts_before: int) -> float:
    email = _pending(attempts=attempts_before)
    FakeBackend.reset(TimeoutError("slow"))
    before = timezone.now()

    delivery.deliver(email.pk)

    email.refresh_from_db()
    return (email.next_attempt_at - before).total_seconds()


def test_a_temporary_error_keeps_the_email_pending_for_a_later_attempt() -> None:
    email = _pending()
    FakeBackend.reset(TimeoutError("slow server"))

    delivery.deliver(email.pk)

    email.refresh_from_db()
    assert email.status == OutboundEmail.Status.PENDING
    assert email.attempts == 1
    assert "slow server" in email.last_error
    assert FakeBackend.sent == []


@pytest.mark.parametrize(
    ("attempts_before", "expected_seconds"),
    [(0, 30), (1, 60), (2, 120), (3, 240), (4, 480), (5, 900), (12, 900)],
)
def test_the_wait_doubles_up_to_fifteen_minutes(
    attempts_before: int, expected_seconds: int
) -> None:
    waited = _wait_after_failure(attempts_before)

    assert expected_seconds <= waited < expected_seconds + 5


def test_an_email_is_delivered_after_two_temporary_errors() -> None:
    email = _pending()
    FakeBackend.reset(TimeoutError("one"), ConnectionError("two"))

    for _ in range(3):
        delivery.deliver(email.pk)
        _due_now(email)

    assert len(FakeBackend.sent) == 1
    assert not OutboundEmail.objects.filter(pk=email.pk).exists()


def test_a_failed_attempt_is_not_retried_before_its_time() -> None:
    email = _pending()
    FakeBackend.reset(TimeoutError("slow"))
    delivery.deliver(email.pk)

    delivery.deliver(email.pk)

    email.refresh_from_db()
    assert email.attempts == 1
    assert FakeBackend.sent == []


@pytest.mark.parametrize(
    ("hours", "window", "status"), [(25, 24, "failed"), (23, 24, "pending"), (3, 2, "failed")]
)
def test_a_notice_stops_being_retried_after_its_window(
    settings: Any, hours: int, window: int, status: str
) -> None:
    settings.EMAIL_NOTICE_RETRY_HOURS = window
    email = _pending()
    OutboundEmail.objects.filter(pk=email.pk).update(
        created_at=timezone.now() - timedelta(hours=hours)
    )
    FakeBackend.reset(TimeoutError("slow"))

    delivery.deliver(email.pk)

    email.refresh_from_db()
    assert email.status == status


def test_the_notice_window_does_not_apply_to_code_emails(settings: Any) -> None:
    settings.EMAIL_NOTICE_RETRY_HOURS = 1
    email = _pending(kind="registration_code")
    OutboundEmail.objects.filter(pk=email.pk).update(created_at=timezone.now() - timedelta(hours=2))
    FakeBackend.reset(TimeoutError("slow"))

    with mock.patch("apps.emails.delivery.rendering.compose", return_value=("A", "B")):
        delivery.deliver(email.pk)

    email.refresh_from_db()
    assert email.status == OutboundEmail.Status.PENDING


def test_a_permanent_rejection_fails_the_email_at_the_first_attempt(send_task: Any) -> None:
    email = _pending()
    FakeBackend.reset(smtplib.SMTPRecipientsRefused({"ana@example.com": (550, b"No such user")}))

    delivery.deliver(email.pk)

    failed = OutboundEmail.objects.get(pk=email.pk)
    assert failed.status == OutboundEmail.Status.FAILED
    assert failed.attempts == 1
    assert "No such user" in failed.last_error
    assert (failed.kind, failed.locale, failed.recipient) == (
        "password_changed",
        "es",
        "ana@example.com",
    )
    assert failed.created_at == email.created_at
    _due_now(failed)
    assert delivery.dispatch_due() == 0
    send_task.assert_not_called()


CODE = "482915"


def _code_email() -> OutboundEmail:
    masked, nonce = fingerprints.mask_code(CODE)
    return _pending(
        kind="registration_code",
        purpose="registration",
        public_id="pub_123",
        masked_code=masked,
        code_nonce=nonce,
    )


def test_a_code_email_is_delivered_with_the_original_code_and_its_link(caplog: Any) -> None:
    caplog.set_level(logging.DEBUG)
    email = _code_email()

    delivery.deliver(email.pk)

    [message] = FakeBackend.sent
    assert CODE in message.body
    assert "https://app.ejemplo.com/register/continue#pub_123" in message.body
    assert not OutboundEmail.objects.filter(pk=email.pk).exists()
    assert CODE not in caplog.text


def test_a_failed_code_email_keeps_no_trace_of_the_code(caplog: Any) -> None:
    caplog.set_level(logging.DEBUG)
    email = _code_email()
    FakeBackend.reset(smtplib.SMTPRecipientsRefused({"ana@example.com": (550, b"No such user")}))

    delivery.deliver(email.pk)

    failed = OutboundEmail.objects.get(pk=email.pk)
    assert failed.status == OutboundEmail.Status.FAILED
    assert (failed.masked_code, failed.code_nonce) == (None, "")
    assert CODE not in failed.last_error
    assert CODE not in caplog.text


def test_a_code_email_keeps_its_mask_while_it_can_be_retried() -> None:
    email = _code_email()
    FakeBackend.reset(TimeoutError("slow"))

    delivery.deliver(email.pk)

    pending = OutboundEmail.objects.get(pk=email.pk)
    assert pending.status == OutboundEmail.Status.PENDING
    assert pending.masked_code == email.masked_code
    assert pending.code_nonce == email.code_nonce


def test_the_checker_receives_the_public_id_and_the_recovered_code(checker: Any) -> None:
    delivery.deliver(_code_email().pk)

    assert checker.calls == [("pub_123", CODE)]


def test_a_code_that_no_longer_serves_is_discarded_without_sending(checker: Any) -> None:
    checker.expiry = None
    email = _code_email()

    delivery.deliver(email.pk)

    assert FakeBackend.sent == []
    assert not OutboundEmail.objects.filter(pk=email.pk).exists()


def test_a_code_email_is_retried_only_while_its_code_serves(checker: Any) -> None:
    email = _code_email()
    FakeBackend.reset(TimeoutError("slow"))
    delivery.deliver(email.pk)
    _due_now(email)
    checker.expiry = None

    delivery.deliver(email.pk)

    assert FakeBackend.sent == []
    assert not OutboundEmail.objects.filter(pk=email.pk).exists()


def test_a_purpose_without_a_checker_is_a_configuration_error() -> None:
    masked, nonce = fingerprints.mask_code(CODE)
    email = _pending(
        kind="password_reset_code",
        purpose="password_reset",
        public_id="pub_9",
        masked_code=masked,
        code_nonce=nonce,
    )

    with pytest.raises(ImproperlyConfigured, match="password_reset"):
        delivery.deliver(email.pk)

    assert FakeBackend.sent == []


def test_registering_a_checker_makes_it_available() -> None:
    def check(public_id: str, code: str) -> None:
        return None

    delivery.register_code_check("password_reset", check)

    assert delivery._CODE_CHECKS["password_reset"] is check
