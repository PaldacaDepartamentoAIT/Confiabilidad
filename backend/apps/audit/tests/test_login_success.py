import json
from datetime import date

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.audit.models import EventType, SecurityEvent
from apps.core.fingerprints import audit_email_fingerprint, audit_session_fingerprint

pytestmark = pytest.mark.django_db

BROWSER_LOGIN = "/_allauth/browser/v1/auth/login"
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


def test_successful_login_records_one_login_row_with_real_ip(audit_key: None, user: User) -> None:
    client = Client()
    response = client.post(
        BROWSER_LOGIN,
        data=json.dumps({"email": EMAIL, "password": PASSWORD}),
        content_type="application/json",
        REMOTE_ADDR="203.0.113.7",
    )
    assert response.status_code == 200

    event = SecurityEvent.objects.get(event_type=EventType.LOGIN, success=True)
    assert event.ip == "203.0.113.7"
    assert event.user_email_hash == audit_email_fingerprint(EMAIL)


def test_login_row_stores_session_key_after_rotation(audit_key: None, user: User) -> None:
    client = Client()
    response = client.post(
        BROWSER_LOGIN,
        data=json.dumps({"email": EMAIL, "password": PASSWORD}),
        content_type="application/json",
    )
    session_key = response.cookies["sessionid"].value

    event = SecurityEvent.objects.get(event_type=EventType.LOGIN, success=True)
    assert event.session_key == audit_session_fingerprint(session_key)
    assert event.session_key != session_key
