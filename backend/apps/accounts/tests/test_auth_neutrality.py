import json
import secrets
from typing import Any

import pytest
from django.test import Client

from apps.accounts.models import UserSession
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user
from apps.audit.models import EventType, SecurityEvent

pytestmark = pytest.mark.django_db

CASES = ["unknown", "wrong_password", "inactive_wrong", "inactive_right"]


def _client() -> Client:
    ip = f"10.{secrets.randbelow(254) + 1}.{secrets.randbelow(254) + 1}.1"
    return Client(enforce_csrf_checks=True, REMOTE_ADDR=ip)


def _csrf_headers(client: Client, kind: str) -> dict[str, str]:
    if kind != "browser":
        return {}
    if "csrftoken" not in client.cookies:
        client.get("/api/browser/v1/auth/session")
    return {"X-CSRFToken": client.cookies["csrftoken"].value}


def _login(client: Client, kind: str, email: str, password: str) -> Any:
    return client.post(
        f"/api/{kind}/v1/auth/login",
        data=json.dumps({"email": email, "password": password, "language": "es"}),
        content_type="application/json",
        headers=_csrf_headers(client, kind),
    )


def _prepare(case: str) -> tuple[str, str]:
    email = f"neutral-{case}-{secrets.token_hex(4)}@example.com"
    if case == "wrong_password":
        make_user(email=email, is_active=True)
        return email, "wrong-password"
    if case == "inactive_wrong":
        make_user(email=email, is_active=False)
        return email, "wrong-password"
    if case == "inactive_right":
        make_user(email=email, is_active=False)
        return email, DEFAULT_PASSWORD
    return email, DEFAULT_PASSWORD


def _shape(response: Any) -> tuple[Any, ...]:
    cookies = sorted((name, dict(morsel)) for name, morsel in response.cookies.items())
    return response.status_code, response.json(), dict(response.headers), cookies


@pytest.mark.parametrize("kind", ["browser", "app"])
def test_login_failures_and_lockout_are_neutral_across_all_cases(kind: str) -> None:
    attempt_shapes: dict[str, list[tuple[Any, ...]]] = {}
    lockout_shapes: dict[str, tuple[Any, ...]] = {}

    for case in CASES:
        email, password = _prepare(case)
        client = _client()
        shapes = [_shape(_login(client, kind, email, password)) for _ in range(5)]
        attempt_shapes[case] = shapes
        lockout_shapes[case] = _shape(_login(client, kind, email, password))

    baseline_attempts = attempt_shapes["unknown"]
    assert all(shape[0] == 400 for shape in baseline_attempts)
    assert all(shape[1]["code"] == "invalid_credentials" for shape in baseline_attempts)
    for case in CASES:
        assert attempt_shapes[case] == baseline_attempts, case

    baseline_lockout = lockout_shapes["unknown"]
    assert baseline_lockout[0] == 400
    assert baseline_lockout[1]["code"] == "too_many_login_attempts"
    for case in CASES:
        assert lockout_shapes[case] == baseline_lockout, case

    assert not UserSession.objects.exists()


@pytest.mark.parametrize("kind", ["browser", "app"])
def test_inactive_account_with_right_password_audits_reason_before_lockout(kind: str) -> None:
    email, password = _prepare("inactive_right")
    client = _client()

    for _ in range(5):
        resp = _login(client, kind, email, password)
        assert resp.status_code == 400 and resp.json()["code"] == "invalid_credentials"

    locked = _login(client, kind, email, password)
    assert locked.status_code == 400 and locked.json()["code"] == "too_many_login_attempts"

    assert (
        SecurityEvent.objects.filter(
            event_type=EventType.LOGIN,
            success=False,
            metadata={"reason": "inactive_account"},
        ).count()
        == 5
    )
    assert (
        SecurityEvent.objects.filter(
            event_type=EventType.LOCKOUT,
            success=False,
            metadata={"reason": "too_many_login_attempts"},
        ).count()
        == 1
    )
