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
PROXY = "10.0.0.5"
REAL_CLIENT = "198.51.100.20"


@pytest.fixture(autouse=True)
def trusted_proxy(settings: object) -> None:
    cache.clear()
    settings.TRUSTED_PROXY_IPS = [PROXY]  # type: ignore[attr-defined]


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        EMAIL, PASSWORD, name="Ana", birthdate=date(1990, 1, 1), country="ES"
    )


def _login(password: str) -> None:
    Client().post(
        BROWSER_LOGIN,
        data=json.dumps({"email": EMAIL, "password": password}),
        content_type="application/json",
        REMOTE_ADDR=PROXY,
        HTTP_X_FORWARDED_FOR=REAL_CLIENT,
    )


def test_successful_and_failed_login_through_trusted_proxy_record_two_rows_with_real_ip(
    user: User,
) -> None:
    _login(PASSWORD)
    _login("contraseña-incorrecta")

    rows = SecurityEvent.objects.filter(event_type=EventType.LOGIN).order_by("created_at")
    assert rows.count() == 2
    assert [row.success for row in rows] == [True, False]
    assert {row.ip for row in rows} == {REAL_CLIENT}


def test_forged_forwarded_header_from_direct_connection_is_ignored(user: User) -> None:
    Client().post(
        BROWSER_LOGIN,
        data=json.dumps({"email": EMAIL, "password": "contraseña-incorrecta"}),
        content_type="application/json",
        REMOTE_ADDR="203.0.113.9",
        HTTP_X_FORWARDED_FOR=REAL_CLIENT,
    )

    row = SecurityEvent.objects.get(event_type=EventType.LOGIN, success=False)
    assert row.ip == "203.0.113.9"
