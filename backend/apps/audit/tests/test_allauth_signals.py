from datetime import date

import pytest
from allauth.account.signals import password_reset, password_set, user_signed_up
from django.test import RequestFactory

from apps.accounts.models import User
from apps.audit.models import EventType, SecurityEvent

pytestmark = pytest.mark.django_db

EMAIL = "ana@x.com"


@pytest.fixture
def audit_key(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = "test-audit-key"  # type: ignore[attr-defined]


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        EMAIL, "Clave-segura-2026!", name="Ana", birthdate=date(1990, 1, 1), country="ES"
    )


@pytest.mark.parametrize(
    ("signal", "event_type"),
    [
        (password_set, EventType.PASSWORD_CHANGE),
        (password_reset, EventType.PASSWORD_RESET),
        (user_signed_up, EventType.ACCOUNT_REGISTRATION),
    ],
)
def test_allauth_signal_records_its_event_type(
    audit_key: None, user: User, signal: object, event_type: str
) -> None:
    request = RequestFactory().post("/", REMOTE_ADDR="203.0.113.7")
    signal.send(sender=User, request=request, user=user)  # type: ignore[attr-defined]

    event = SecurityEvent.objects.get(event_type=event_type)
    assert event.success is True
    assert event.ip == "203.0.113.7"
