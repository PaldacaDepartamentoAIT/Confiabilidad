import smtplib

import pytest
from django.core.mail import EmailMessage, get_connection

from apps.emails.errors import Failure, classify
from apps.emails.tests.backends import FAKE_BACKEND, FakeBackend


@pytest.mark.parametrize(
    "error",
    [
        smtplib.SMTPRecipientsRefused({"x@ejemplo.com": (550, b"No such user")}),
        smtplib.SMTPSenderRefused(553, b"Sender rejected", "no-responder@ejemplo.com"),
        smtplib.SMTPDataError(554, b"Message refused"),
    ],
)
def test_a_5xx_rejection_is_permanent(error: Exception) -> None:
    assert classify(error) is Failure.PERMANENT


@pytest.mark.parametrize(
    "error",
    [
        smtplib.SMTPRecipientsRefused({"x@ejemplo.com": (450, b"Mailbox busy")}),
        smtplib.SMTPSenderRefused(451, b"Try later", "no-responder@ejemplo.com"),
        smtplib.SMTPDataError(421, b"Rate limit exceeded"),
        smtplib.SMTPServerDisconnected("gone"),
        smtplib.SMTPConnectError(421, b"Too busy"),
        smtplib.SMTPAuthenticationError(535, b"Bad credentials"),
        TimeoutError("slow"),
        OSError("network unreachable"),
        RuntimeError("anything else"),
    ],
)
def test_everything_else_is_temporary(error: Exception) -> None:
    assert classify(error) is Failure.TEMPORARY


def test_a_mix_of_refused_recipients_is_temporary() -> None:
    error = smtplib.SMTPRecipientsRefused(
        {"a@ejemplo.com": (550, b"No such user"), "b@ejemplo.com": (452, b"Full")}
    )

    assert classify(error) is Failure.TEMPORARY


def _message() -> EmailMessage:
    return EmailMessage("Asunto", "Cuerpo", "de@ejemplo.com", ["para@ejemplo.com"])


def test_the_fake_backend_raises_the_queued_errors_in_order_and_then_delivers(
    settings: object,
) -> None:
    settings.EMAIL_BACKEND = FAKE_BACKEND  # type: ignore[attr-defined]
    FakeBackend.reset(TimeoutError("first"), smtplib.SMTPServerDisconnected("second"))

    with pytest.raises(TimeoutError):
        get_connection().send_messages([_message()])
    with pytest.raises(smtplib.SMTPServerDisconnected):
        get_connection().send_messages([_message()])
    assert get_connection().send_messages([_message()]) == 1

    assert [message.subject for message in FakeBackend.sent] == ["Asunto"]
