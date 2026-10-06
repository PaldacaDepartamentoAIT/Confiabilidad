import hashlib
import hmac
import secrets

from django.utils import timezone

from apps.accounts import conf

CODE_LENGTH = 6
_PUBLIC_ID_BYTES = 32


def generate_code() -> str:
    return f"{secrets.randbelow(10**CODE_LENGTH):0{CODE_LENGTH}d}"


def generate_public_id() -> str:
    return secrets.token_urlsafe(_PUBLIC_ID_BYTES)


def _fingerprint(secret: str, public_id: str, code: str) -> str:
    message = f"{public_id}:{code}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def code_fingerprint(public_id: str, code: str) -> str:
    return _fingerprint(conf.code_secret(), public_id, code)


def verify_code(public_id: str, code: str, fingerprint: str) -> bool:
    if hmac.compare_digest(code_fingerprint(public_id, code), fingerprint):
        return True
    previous = _previous_secret_in_transition()
    return previous is not None and hmac.compare_digest(
        _fingerprint(previous, public_id, code), fingerprint
    )


def _previous_secret_in_transition() -> str | None:
    previous, rotated_at = conf.previous_code_secret(), conf.secret_rotated_at()
    if previous is None or rotated_at is None:
        return None
    if timezone.now() > rotated_at + conf.secret_transition():
        return None
    return previous
