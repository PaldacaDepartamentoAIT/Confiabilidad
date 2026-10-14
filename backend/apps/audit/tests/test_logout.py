import json
from datetime import date

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.audit.models import EventType, SecurityEvent
from apps.core.fingerprints import audit_email_fingerprint, audit_session_fingerprint

pytestmark = pytest.mark.django_db

BROWSER_LOGIN = "/_allauth/browser/v1/auth/login"
BROWSER_SESSION = "/_allauth/browser/v1/auth/session"
EMAIL = "ana@x.com"
PASSWORD = "Clave-segura-2026!"


@pytest.fixture
def audit_key(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = "test-audit-key"  # type: ignore[attr-defined]


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        EMAIL, PASSWORD, name="Ana", birthdate=date(1990, 1, 1), country="ES"
    )


def test_logout_records_logout_row_with_fingerprint_of_closed_session(
    audit_key: None, user: User
) -> None:
    client = Client()
    login = client.post(
        BROWSER_LOGIN,
        data=json.dumps({"email": EMAIL, "password": PASSWORD}),
        content_type="application/json",
    )
    session_key = login.cookies["sessionid"].value

    client.delete(BROWSER_SESSION)

    event = SecurityEvent.objects.get(event_type=EventType.LOGOUT)
    assert event.success is True
    assert event.session_key == audit_session_fingerprint(session_key)
    assert event.user_email_hash == audit_email_fingerprint(EMAIL)
