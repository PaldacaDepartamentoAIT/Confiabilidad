import uuid
from datetime import date
from typing import Any

import pytest
from django.test import Client

from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user


@pytest.fixture(params=["browser", "app"])
def kind(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture
def unique_email() -> str:
    # Los intentos fallidos cuentan para el límite de allauth por correo (C-15).
    return f"inactive-{uuid.uuid4().hex[:12]}@example.com"


def _login(client: Client, kind: str, email: str) -> tuple[int, dict[str, Any]]:
    base = f"/_allauth/{kind}/v1"
    headers: dict[str, str] = {}
    if kind == "browser":
        client.get(f"{base}/auth/session")
        headers = {"X-CSRFToken": client.cookies["csrftoken"].value}
    resp = client.post(
        f"{base}/auth/login",
        data={"email": email, "password": DEFAULT_PASSWORD},
        content_type="application/json",
        headers=headers,
    )
    body: dict[str, Any] = resp.json()
    return resp.status_code, body


def _has_session(client: Client, kind: str, body: dict[str, Any]) -> bool:
    token = body["meta"].get("session_token")
    headers = {"X-Session-Token": token} if kind == "app" and token else {}
    return client.get(f"/_allauth/{kind}/v1/auth/session", headers=headers).status_code == 200


@pytest.mark.django_db
def test_inactive_account_cannot_log_in(kind: str, unique_email: str) -> None:
    make_user(email=unique_email, is_active=False)
    client = Client(enforce_csrf_checks=True)

    status, body = _login(client, kind, unique_email)

    assert status == 401
    assert not body["meta"]["is_authenticated"]
    assert not _has_session(client, kind, body)


@pytest.mark.django_db
def test_reactivated_account_can_log_in(kind: str, unique_email: str) -> None:
    user = make_user(email=unique_email, is_active=False)
    user.is_active = True
    user.save(update_fields=["is_active"])
    client = Client(enforce_csrf_checks=True)

    status, body = _login(client, kind, unique_email)

    assert status == 200
    assert _has_session(client, kind, body)


@pytest.mark.django_db
def test_deactivation_keeps_data_and_blocks_login_until_reactivated(
    kind: str, unique_email: str
) -> None:
    user = make_user(
        email=unique_email, name="Ana García", birthdate=date(1990, 5, 10), country="MX"
    )
    user.is_active = False
    user.save()
    user.refresh_from_db()

    assert not user.is_active
    assert (user.email, user.name, user.birthdate, user.country) == (
        unique_email,
        "Ana García",
        date(1990, 5, 10),
        "MX",
    )
    assert user.check_password(DEFAULT_PASSWORD)
    status, _ = _login(Client(enforce_csrf_checks=True), kind, unique_email)
    assert status == 401

    user.is_active = True
    user.save()
    client = Client(enforce_csrf_checks=True)
    status, body = _login(client, kind, unique_email)
    assert status == 200
    assert _has_session(client, kind, body)
