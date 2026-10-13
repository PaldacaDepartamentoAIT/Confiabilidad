import json
from datetime import date

import pytest
from django.core.cache import cache
from django.test import Client

from apps.accounts.models import User
from apps.audit.models import EventType, SecurityEvent

pytestmark = pytest.mark.django_db

BROWSER_LOGIN = "/_allauth/browser/v1/auth/login"
EMAIL = "ana@x.com"
PASSWORD = "Clave-segura-2026!"
ALLAUTH_LIMIT = 5


@pytest.fixture(autouse=True)
def clear_login_rate_limits() -> None:
    cache.clear()


@pytest.fixture
def audit_key(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = "test-audit-key"  # type: ignore[attr-defined]


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        EMAIL, PASSWORD, name="Ana", birthdate=date(1990, 1, 1), country="ES"
    )


def _wrong_attempt() -> int:
    response = Client().post(
        BROWSER_LOGIN,
        data=json.dumps({"email": EMAIL, "password": "incorrecta"}),
        content_type="application/json",
        REMOTE_ADDR="203.0.113.7",
    )
    return response.status_code


def test_rejected_attempt_by_limit_records_failed_login_and_lockout(
    audit_key: None, user: User
) -> None:
    for _ in range(ALLAUTH_LIMIT):
        assert _wrong_attempt() == 400

    assert _wrong_attempt() == 400

    assert SecurityEvent.objects.filter(event_type=EventType.LOGIN, success=False).count() == (
        ALLAUTH_LIMIT + 1
    )
    lockout = SecurityEvent.objects.get(event_type=EventType.LOCKOUT)
    assert lockout.success is False
    assert lockout.ip == "203.0.113.7"
    assert lockout.metadata == {"reason": "too_many_login_attempts"}


def test_attempts_under_the_limit_record_no_lockout(audit_key: None, user: User) -> None:
    for _ in range(ALLAUTH_LIMIT):
        _wrong_attempt()

    assert not SecurityEvent.objects.filter(event_type=EventType.LOCKOUT).exists()


def test_each_rejected_attempt_records_its_own_lockout(audit_key: None, user: User) -> None:
    for _ in range(ALLAUTH_LIMIT):
        _wrong_attempt()
    _wrong_attempt()
    _wrong_attempt()

    assert SecurityEvent.objects.filter(event_type=EventType.LOCKOUT).count() == 2
