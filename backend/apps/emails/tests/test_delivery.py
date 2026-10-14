import importlib
from datetime import timedelta
from typing import Any
from unittest import mock

import pytest
from django.apps import apps as global_apps
from django.utils import timezone

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
