import json
from datetime import date

import pytest
from django.core.cache import cache
from django.test import Client

from apps.accounts.models import User
from apps.audit.models import EventType, SecurityEvent
from apps.core.fingerprints import audit_email_fingerprint

pytestmark = pytest.mark.django_db

BROWSER_LOGIN = "/_allauth/browser/v1/auth/login"
APP_LOGIN = "/_allauth/app/v1/auth/login"
EMAIL = "ana@x.com"
PASSWORD = "Clave-segura-2026!"


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


def _post(url: str, email: str, password: str) -> object:
    return Client().post(
        url,
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
        REMOTE_ADDR="203.0.113.7",
    )


def test_wrong_password_records_one_failed_login_row(audit_key: None, user: User) -> None:
    _post(BROWSER_LOGIN, EMAIL, "contraseña-incorrecta")

    event = SecurityEvent.objects.get(event_type=EventType.LOGIN, success=False)
    assert event.ip == "203.0.113.7"
    assert event.user_email_hash == audit_email_fingerprint(EMAIL)
    assert event.metadata == {"reason": "invalid_credentials"}
    assert event.session_key == ""


def test_unknown_email_records_row_without_account_link(audit_key: None) -> None:
    _post(BROWSER_LOGIN, "nadie@x.com", "cualquiera")

    event = SecurityEvent.objects.get(event_type=EventType.LOGIN, success=False)
    assert event.user_email_hash == audit_email_fingerprint("nadie@x.com")


def test_failed_login_is_recorded_on_headless_flow_too(audit_key: None, user: User) -> None:
    _post(APP_LOGIN, EMAIL, "contraseña-incorrecta")

    assert SecurityEvent.objects.filter(event_type=EventType.LOGIN, success=False).count() == 1


def test_password_is_never_stored(audit_key: None, user: User) -> None:
    _post(BROWSER_LOGIN, EMAIL, "contraseña-incorrecta")

    event = SecurityEvent.objects.get(event_type=EventType.LOGIN, success=False)
    stored = f"{event.user_agent} {event.user_email_hash} {event.session_key} {event.metadata}"
    assert "contraseña-incorrecta" not in stored


def test_inactive_account_with_valid_password_records_failed_login(
    audit_key: None,
) -> None:
    inactive = User.objects.create_user(
        "ina@x.com", PASSWORD, name="Ina", birthdate=date(1990, 1, 1), country="ES", is_active=False
    )
    assert inactive.is_active is False
    _post(BROWSER_LOGIN, "ina@x.com", PASSWORD)

    event = SecurityEvent.objects.get(event_type=EventType.LOGIN, success=False)
    assert event.metadata == {"reason": "inactive_account"}
    assert event.user_email_hash == audit_email_fingerprint("ina@x.com")


def test_inactive_account_is_recorded_on_headless_flow_too(audit_key: None) -> None:
    User.objects.create_user(
        "ina@x.com", PASSWORD, name="Ina", birthdate=date(1990, 1, 1), country="ES", is_active=False
    )
    _post(APP_LOGIN, "ina@x.com", PASSWORD)

    assert (
        SecurityEvent.objects.filter(
            event_type=EventType.LOGIN, success=False, metadata={"reason": "inactive_account"}
        ).count()
        == 1
    )
