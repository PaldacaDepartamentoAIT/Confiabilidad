import hashlib
import hmac
import secrets
from enum import StrEnum

from django.utils import timezone

from apps.accounts import conf

CODE_LENGTH = 6
_PUBLIC_ID_BYTES = 32


class Purpose(StrEnum):
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"


def generate_code() -> str:
    return f"{secrets.randbelow(10**CODE_LENGTH):0{CODE_LENGTH}d}"


def generate_public_id() -> str:
    # Un valor que empieza por "-" se confundiría con una opción en la consola (RF-023).
    while True:
        public_id = secrets.token_urlsafe(_PUBLIC_ID_BYTES)
        if not public_id.startswith("-"):
            return public_id


def _fingerprint(secret: str, purpose: Purpose, public_id: str, code: str) -> str:
    message = f"{purpose}:{public_id}:{code}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def code_fingerprint(purpose: Purpose, public_id: str, code: str) -> str:
    return _fingerprint(conf.code_secret(), purpose, public_id, code)


def verify_code(purpose: Purpose, public_id: str, code: str, fingerprint: str) -> bool:
    if hmac.compare_digest(code_fingerprint(purpose, public_id, code), fingerprint):
        return True
    previous = _previous_secret_in_transition()
    return previous is not None and hmac.compare_digest(
        _fingerprint(previous, purpose, public_id, code), fingerprint
    )


def _previous_secret_in_transition() -> str | None:
    previous, rotated_at = conf.previous_code_secret(), conf.secret_rotated_at()
    if previous is None or rotated_at is None:
        return None
    if timezone.now() > rotated_at + conf.secret_transition():
        return None
    return previous
