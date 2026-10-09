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


def _sign(secret: str, message: str) -> str:
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def _matches(message: str, fingerprint: str) -> bool:
    if hmac.compare_digest(_sign(conf.code_secret(), message), fingerprint):
        return True
    previous = _previous_secret_in_transition()
    return previous is not None and hmac.compare_digest(_sign(previous, message), fingerprint)


def _code_message(purpose: Purpose, public_id: str, code: str) -> str:
    return f"{purpose}:{public_id}:{code}"


def code_fingerprint(purpose: Purpose, public_id: str, code: str) -> str:
    return _sign(conf.code_secret(), _code_message(purpose, public_id, code))


def verify_code(purpose: Purpose, public_id: str, code: str, fingerprint: str) -> bool:
    return _matches(_code_message(purpose, public_id, code), fingerprint)


def _account_message(email: str, password_hash: str) -> str:
    return f"password_reset_account:{email.lower()}:{password_hash}"


def account_stamp(email: str, password_hash: str) -> str:
    return _sign(conf.code_secret(), _account_message(email, password_hash))


def account_stamp_matches(stamp: str, email: str, password_hash: str) -> bool:
    return _matches(_account_message(email, password_hash), stamp)


def _previous_secret_in_transition() -> str | None:
    previous, rotated_at = conf.previous_code_secret(), conf.secret_rotated_at()
    if previous is None or rotated_at is None:
        return None
    if timezone.now() > rotated_at + conf.secret_transition():
        return None
    return previous
