from collections.abc import Sequence
from typing import Any, ClassVar

from django.core.mail import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend

FAKE_BACKEND = "apps.emails.tests.backends.FakeBackend"


class FakeBackend(BaseEmailBackend):
    # Proveedor simulado (D-15): lanza en orden los errores indicados y luego entrega.
    failures: ClassVar[list[BaseException]] = []
    sent: ClassVar[list[EmailMessage]] = []

    @classmethod
    def reset(cls, *failures: BaseException) -> None:
        cls.failures = list(failures)
        cls.sent = []

    def send_messages(self, email_messages: Sequence[EmailMessage], **kwargs: Any) -> int:
        if type(self).failures:
            raise type(self).failures.pop(0)
        type(self).sent.extend(email_messages)
        return len(email_messages)
