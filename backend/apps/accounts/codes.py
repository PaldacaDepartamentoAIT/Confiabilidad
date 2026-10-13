import secrets
from enum import StrEnum

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
