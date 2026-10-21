import importlib
from io import StringIO
from typing import Any
from unittest import mock

import pytest
from django.apps import apps as global_apps
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.tests.factories import make_user
from apps.emails import delivery
from apps.emails.models import OutboundEmail
from apps.emails.tests.backends import FAKE_BACKEND, FakeBackend

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _environment(settings: Any) -> Any:
    settings.EMAIL_BACKEND = FAKE_BACKEND
    settings.FRONTEND_BASE_URL = "https://app.ejemplo.com"
    FakeBackend.reset()
    migration = importlib.import_module("apps.emails.migrations.0002_initial_templates")
    migration.create_initial_templates(global_apps, None)
    with mock.patch("celery.current_app.send_task") as send_task:
        yield send_task


def _emails(*args: str) -> str:
    out = StringIO()
    call_command("emails", *args, stdout=out)
    return out.getvalue()


def test_a_sample_code_email_is_queued_with_example_data() -> None:
    output = _emails(
        "test", "--kind", "registration_code", "--locale", "pt-BR", "--to", "x@ejemplo.com"
    )

    email = OutboundEmail.objects.get()
    assert (email.kind, email.locale, email.recipient, email.status) == (
        "registration_code",
        "pt-BR",
        "x@ejemplo.com",
        "pending",
    )
    assert email.masked_code is None
    assert f"queued: {email.pk}" in output
    assert "x@ejemplo.com" in output


def test_a_sample_code_email_goes_out_complete() -> None:
    _emails("test", "--kind", "password_reset_code", "--locale", "es", "--to", "x@ejemplo.com")

    delivery.deliver(OutboundEmail.objects.get().pk)

    [message] = FakeBackend.sent
    assert "123456" in message.body
    assert "https://app.ejemplo.com/password-reset/continue#" in message.body
    assert "15 minutos" in message.body
    assert "{{" not in message.body


def test_a_sample_notice_goes_out_with_its_report_block(settings: Any) -> None:
    settings.EMAIL_SUPPORT_ADDRESS = "ayuda@ejemplo.com"
    _emails("test", "--kind", "sessions_closed", "--locale", "en", "--to", "x@ejemplo.com")

    delivery.deliver(OutboundEmail.objects.get().pk)

    [message] = FakeBackend.sent
    assert message.subject == "Your account's sessions have been closed"
    assert "ayuda@ejemplo.com" in message.body


@pytest.mark.parametrize(
    "args",
    [
        ["--kind", "newsletter", "--locale", "es", "--to", "x@ejemplo.com"],
        ["--kind", "account_exists", "--locale", "fr", "--to", "x@ejemplo.com"],
        ["--kind", "account_exists", "--locale", "es", "--to", "no-es-un-correo"],
    ],
)
def test_an_unknown_kind_language_or_address_is_a_command_error(args: list[str]) -> None:
    with pytest.raises(CommandError):
        _emails("test", *args)

    assert not OutboundEmail.objects.exists()


def test_sample_account_exists_notices_are_not_capped(
    _environment: Any, django_capture_on_commit_callbacks: Any
) -> None:
    with django_capture_on_commit_callbacks(execute=True):
        for _ in range(2):
            _emails("test", "--kind", "account_exists", "--locale", "es", "--to", "x@ejemplo.com")

    assert OutboundEmail.objects.filter(kind="account_exists").count() == 2
    assert _environment.call_count == 2


@pytest.mark.parametrize("kind", ["password_changed", "account_disabled", "sessions_closed"])
def test_a_notice_without_its_own_action_is_queued_to_an_account(kind: str) -> None:
    make_user(email="ana@ejemplo.com", name="Ana García", language="pt-BR")

    output = _emails("notify", "--kind", kind, "--email", "ANA@ejemplo.com")

    email = OutboundEmail.objects.get()
    assert (email.kind, email.recipient, email.locale, email.context) == (
        kind,
        "ana@ejemplo.com",
        "pt-BR",
        {"name": "Ana García"},
    )
    assert f"queued: {email.pk}" in output


@pytest.mark.parametrize(
    "args",
    [
        ["--kind", "account_exists", "--email", "ana@ejemplo.com"],
        ["--kind", "registration_code", "--email", "ana@ejemplo.com"],
        ["--kind", "password_changed", "--email", "nadie@ejemplo.com"],
    ],
)
def test_notify_refuses_other_kinds_and_unknown_accounts(args: list[str]) -> None:
    make_user(email="ana@ejemplo.com")

    with pytest.raises(CommandError):
        _emails("notify", *args)

    assert not OutboundEmail.objects.exists()


def test_dispatch_queues_the_due_emails_and_says_how_many(_environment: Any) -> None:
    for _ in range(2):
        OutboundEmail.objects.create(
            kind="password_changed", locale="es", recipient="a@ejemplo.com"
        )

    output = _emails("dispatch")

    assert "queued: 2" in output
    assert _environment.call_count == 2
