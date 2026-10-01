from datetime import date
from itertools import count
from typing import Any

from apps.accounts.models import User

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
