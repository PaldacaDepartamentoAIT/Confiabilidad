import json
from datetime import date

import pytest
from allauth.account.signals import password_changed
from django.core.cache import cache
from django.test import Client, RequestFactory

from apps.accounts import password_reset, registration
from apps.accounts.models import User
from apps.audit.models import SecurityEvent

pytestmark = pytest.mark.django_db

EMAIL = "ana@x.com"
PASSWORD = "Clave-segura-2026!"
WRONG = "Contrasena-erronea-2026!"
NEW_PASSWORD = "Otra-clave-segura-2026!"
BROWSER_LOGIN = "/_allauth/browser/v1/auth/login"
BROWSER_SESSION = "/_allauth/browser/v1/auth/session"


@pytest.fixture(autouse=True)
def clean_state() -> None:
    cache.clear()


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        EMAIL, PASSWORD, name="Ana", birthdate=date(1990, 1, 1), country="ES"
    )


def _rows_text() -> str:
    parts: list[str] = []
    for row in SecurityEvent.objects.all():
        parts.extend(str(getattr(row, f.name)) for f in SecurityEvent._meta.fields)
    return " ".join(parts)


def _assert_no_secret(secrets: list[str]) -> None:
    text = _rows_text()
    assert text, "el flujo debe haber generado filas"
    assert EMAIL not in text
    for secret in secrets:
        assert secret not in text


def _login(password: str) -> Client:
    client = Client()
    client.post(
        BROWSER_LOGIN,
        data=json.dumps({"email": EMAIL, "password": password}),
        content_type="application/json",
    )
    return client


def test_successful_login_stores_no_secret(user: User) -> None:
    client = _login(PASSWORD)
    session_key = client.cookies["sessionid"].value
    _assert_no_secret([PASSWORD, session_key])


def test_failed_login_stores_no_secret(user: User) -> None:
    _login(WRONG)
    _assert_no_secret([WRONG])


def test_lockout_stores_no_secret(user: User) -> None:
    for _ in range(6):
        _login(WRONG)
    _assert_no_secret([WRONG])


def test_logout_stores_no_secret(user: User) -> None:
    client = _login(PASSWORD)
    session_key = client.cookies["sessionid"].value
    client.delete(BROWSER_SESSION)
    _assert_no_secret([PASSWORD, session_key])


def test_registration_stores_no_secret(audit_key: None) -> None:
    started = registration.start(email=EMAIL, name="Ana", birthdate=date(1990, 1, 1), country="ES")
    assert isinstance(started, registration.Started)
    registration.verify(public_id=started.public_id, code=started.code)
    registration.complete(public_id=started.public_id, password=PASSWORD)
    _assert_no_secret([PASSWORD, started.code, started.public_id])


def test_password_reset_stores_no_secret(user: User) -> None:
    started = password_reset.start(email=EMAIL)
    assert isinstance(started, password_reset.Started)
    password_reset.verify(public_id=started.public_id, code=started.code)
    password_reset.complete(public_id=started.public_id, password=NEW_PASSWORD)
    _assert_no_secret([NEW_PASSWORD, started.code, started.public_id])


def test_password_change_stores_no_secret(user: User) -> None:
    request = RequestFactory().post("/", REMOTE_ADDR="203.0.113.7")
    password_changed.send(sender=User, request=request, user=user)
    _assert_no_secret([PASSWORD, NEW_PASSWORD])


@pytest.fixture
def audit_key(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = "test-audit-key"  # type: ignore[attr-defined]
