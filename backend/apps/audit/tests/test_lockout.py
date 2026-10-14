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


def test_rejected_attempt_by_limit_creates_exactly_a_failed_login_and_a_lockout(
    audit_key: None, user: User
) -> None:
    for _ in range(ALLAUTH_LIMIT):
        _wrong_attempt()
    last_id = SecurityEvent.objects.order_by("-id").values_list("id", flat=True).first() or 0

    _wrong_attempt()

    created = SecurityEvent.objects.filter(id__gt=last_id).order_by("id")
    assert [(row.event_type, row.success, row.metadata) for row in created] == [
        (EventType.LOGIN, False, {"reason": "too_many_login_attempts"}),
        (EventType.LOCKOUT, False, {"reason": "too_many_login_attempts"}),
    ]


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


def _attempts_until_limit(settings: object, adapter_path: str) -> int:
    settings.ACCOUNT_ADAPTER = adapter_path  # type: ignore[attr-defined]
    cache.clear()
    for attempt in range(1, ALLAUTH_LIMIT + 3):
        response = Client().post(
            BROWSER_LOGIN,
            data=json.dumps({"email": EMAIL, "password": "incorrecta"}),
            content_type="application/json",
            REMOTE_ADDR="203.0.113.7",
        )
        if "too_many_login_attempts" in response.content.decode():
            return attempt
    raise AssertionError("el límite de allauth no se alcanzó")


def test_audit_adapter_trips_allauth_limit_at_the_same_attempt_as_default(
    settings: object,
) -> None:
    default_attempt = _attempts_until_limit(
        settings, "allauth.account.adapter.DefaultAccountAdapter"
    )
    audit_attempt = _attempts_until_limit(settings, "apps.audit.adapters.AuditAccountAdapter")
    assert audit_attempt == default_attempt == ALLAUTH_LIMIT + 1
