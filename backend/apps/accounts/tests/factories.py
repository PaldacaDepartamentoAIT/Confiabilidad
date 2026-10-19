from dataclasses import dataclass
from datetime import date
from itertools import count
from typing import Any

from apps.accounts import password_reset, registration
from apps.accounts.models import PhantomProcess, User
from apps.core import fingerprints
from apps.emails.models import OutboundEmail

DEFAULT_PASSWORD = "secret123"
DEFAULT_PROFILE: dict[str, Any] = {
    "name": "Test User",
    "birthdate": date(1990, 1, 1),
    "country": "ES",
}
_email_sequence = count(1)


def make_user(**overrides: Any) -> User:
    fields: dict[str, Any] = {
        "email": f"user{next(_email_sequence)}@example.com",
        "password": DEFAULT_PASSWORD,
        **DEFAULT_PROFILE,
    }
    fields.update(overrides)
    return User.objects.create_user(**fields)


@dataclass(frozen=True)
class StartedWithCode:
    public_id: str
    code: str


def code_sent_to(public_id: str) -> str:
    # Hace en el test lo que harían las tareas: resuelve la plaza y lee el último código enviado.
    slot = PhantomProcess.objects.filter(public_id=public_id, payload__isnull=False).first()
    if slot is not None and slot.purpose == PhantomProcess.Purpose.REGISTRATION:
        registration.resolve_registration(public_id)
    elif slot is not None:
        password_reset.resolve_password_reset(public_id)
    email = (
        OutboundEmail.objects.filter(public_id=public_id, masked_code__isnull=False)
        .order_by("-pk")
        .first()
    )
    assert email is not None and email.masked_code is not None, "no code was sent"
    return fingerprints.unmask_code(email.masked_code, email.code_nonce)


def make_pending(email: str = "ana@x.com", **data: Any) -> StartedWithCode:
    fields: dict[str, Any] = {**DEFAULT_PROFILE, **data}
    started = registration.start(email=email, **fields)
    return StartedWithCode(public_id=started.public_id, code=code_sent_to(started.public_id))


def make_reset_request(email: str, **options: Any) -> StartedWithCode:
    started = password_reset.start(email=email, **options)
    return StartedWithCode(public_id=started.public_id, code=code_sent_to(started.public_id))
