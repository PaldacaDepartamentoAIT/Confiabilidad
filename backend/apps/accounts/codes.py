import hashlib
import hmac
import secrets

from apps.accounts import conf

CODE_LENGTH = 6
_PUBLIC_ID_BYTES = 32


def generate_code() -> str:
    return f"{secrets.randbelow(10**CODE_LENGTH):0{CODE_LENGTH}d}"


def generate_public_id() -> str:
    return secrets.token_urlsafe(_PUBLIC_ID_BYTES)


def code_fingerprint(public_id: str, code: str) -> str:
    message = f"{public_id}:{code}".encode()
    return hmac.new(conf.code_secret().encode(), message, hashlib.sha256).hexdigest()


def verify_code(public_id: str, code: str, fingerprint: str) -> bool:
    return hmac.compare_digest(code_fingerprint(public_id, code), fingerprint)
