from datetime import timedelta
from typing import Any
from unittest import mock

import pytest
from django.db import transaction
from django.utils import timezone

from apps.accounts.tests.factories import make_user
from apps.emails import outbox
from apps.emails.models import AccountExistsNotice, OutboundEmail

pytestmark = pytest.mark.django_db

DELIVER = "apps.emails.tasks.deliver"


def _enqueue(**overrides: Any) -> OutboundEmail:
    values: dict[str, Any] = {
        "kind": "password_changed",
        "recipient": "ana@example.com",
        "locale": "es",
        "context": {"name": "Ana"},
    }
    values.update(overrides)
    email = outbox.enqueue(**values)
    assert email is not None
    return email


@pytest.fixture
def send_task() -> Any:
    with mock.patch("apps.emails.outbox.current_app.send_task") as patched:
        yield patched


def test_a_requested_email_waits_in_the_outbox(send_task: Any) -> None:
    email = _enqueue()

    stored = OutboundEmail.objects.get(pk=email.pk)
    assert (stored.kind, stored.recipient, stored.locale, stored.context) == (
        "password_changed",
        "ana@example.com",
        "es",
        {"name": "Ana"},
    )
    assert stored.status == OutboundEmail.Status.PENDING
    assert stored.attempts == 0


def test_the_email_is_queued_once_when_the_operation_commits(
    send_task: Any, django_capture_on_commit_callbacks: Any
) -> None:
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        email = _enqueue()
        send_task.assert_not_called()

    for callback in callbacks:
        callback()
    send_task.assert_called_once_with(DELIVER, args=[email.pk])


def test_nothing_is_stored_or_queued_when_the_operation_rolls_back(
    send_task: Any, django_capture_on_commit_callbacks: Any
) -> None:
    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(RuntimeError), transaction.atomic():
            _enqueue()
            raise RuntimeError

    assert not OutboundEmail.objects.exists()
    send_task.assert_not_called()


def test_a_queue_outage_leaves_the_email_pending(
    send_task: Any, django_capture_on_commit_callbacks: Any
) -> None:
    send_task.side_effect = ConnectionError("broker down")

    with django_capture_on_commit_callbacks(execute=True):
        email = _enqueue()

    assert OutboundEmail.objects.get(pk=email.pk).status == OutboundEmail.Status.PENDING


def test_an_outbound_email_reads_as_its_kind_and_recipient(send_task: Any) -> None:
    assert str(_enqueue()) == "password_changed → ana@example.com"


@pytest.mark.parametrize(
    ("requested", "stored"), [("pt-br", "pt-BR"), ("EN", "en"), ("fr", "es"), ("", "es")]
)
def test_a_code_email_uses_the_requested_language(
    send_task: Any, requested: str, stored: str
) -> None:
    email = _enqueue(kind="registration_code", locale=requested)

    assert OutboundEmail.objects.get(pk=email.pk).locale == stored


@pytest.mark.parametrize("language", ["pt-BR", "en", "es"])
def test_a_security_notice_uses_the_language_of_the_account(send_task: Any, language: str) -> None:
    account = make_user(language=language)

    email = _enqueue(
        kind="password_changed", locale="fr" if language != "es" else "en", account=account
    )

    assert OutboundEmail.objects.get(pk=email.pk).locale == language


def test_a_code_email_ignores_the_language_of_the_account(send_task: Any) -> None:
    account = make_user(language="en")

    email = _enqueue(kind="password_reset_code", locale="pt-BR", account=account)

    assert OutboundEmail.objects.get(pk=email.pk).locale == "pt-BR"


def _account_exists(account: Any) -> OutboundEmail | None:
    return outbox.enqueue(
        kind="account_exists", recipient=account.email, locale="es", account=account
    )


def _age_notice(account: Any, minutes: int) -> None:
    AccountExistsNotice.objects.filter(user=account).update(
        last_queued_at=timezone.now() - timedelta(minutes=minutes)
    )


def test_the_first_account_exists_notice_is_queued(send_task: Any) -> None:
    assert _account_exists(make_user()) is not None


@pytest.mark.parametrize(
    ("window", "minutes_ago", "queued"),
    [(60, 59, False), (60, 61, True), (10, 11, True), (10, 9, False)],
)
def test_a_second_account_exists_notice_waits_for_the_window(
    send_task: Any, settings: Any, window: int, minutes_ago: int, queued: bool
) -> None:
    settings.EMAIL_ACCOUNT_EXISTS_WINDOW_MINUTES = window
    account = make_user()
    _account_exists(account)
    _age_notice(account, minutes_ago)

    second = _account_exists(account)

    assert (second is not None) is queued
    assert OutboundEmail.objects.filter(kind="account_exists").count() == (2 if queued else 1)


def test_the_cap_does_not_touch_other_kinds_or_other_accounts(send_task: Any) -> None:
    account = make_user()
    _account_exists(account)

    assert _account_exists(make_user()) is not None
    assert _enqueue(kind="password_changed", account=account) is not None
    assert _enqueue(kind="password_changed", account=account) is not None


def test_deleting_the_account_deletes_its_cap(send_task: Any) -> None:
    account = make_user()
    _account_exists(account)

    account.delete()

    assert not AccountExistsNotice.objects.exists()


def test_an_account_exists_notice_needs_the_account(send_task: Any) -> None:
    with pytest.raises(ValueError):
        outbox.enqueue(kind="account_exists", recipient="ana@example.com", locale="es")


def test_a_notice_after_the_window_restarts_the_window(send_task: Any) -> None:
    account = make_user()
    _account_exists(account)
    _age_notice(account, 61)
    _account_exists(account)

    assert _account_exists(account) is None


def test_an_account_exists_cap_reads_as_its_account_and_time(send_task: Any) -> None:
    account = make_user()
    _account_exists(account)
    notice = AccountExistsNotice.objects.get(user=account)

    assert str(notice).startswith(f"{account.pk} @ ")
