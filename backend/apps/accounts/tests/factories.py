from itertools import count
from typing import Any

from apps.accounts.models import User

DEFAULT_PASSWORD = "secret123"
_email_sequence = count(1)


def make_user(**overrides: Any) -> User:
    fields: dict[str, Any] = {
        "email": f"user{next(_email_sequence)}@example.com",
        "password": DEFAULT_PASSWORD,
    }
    fields.update(overrides)
    return User.objects.create_user(**fields)
