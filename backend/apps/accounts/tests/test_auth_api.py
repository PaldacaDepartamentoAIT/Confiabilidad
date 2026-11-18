import json
import secrets
from datetime import timedelta
from typing import Any

import pytest
from django.core.cache import cache
from django.test import Client, override_settings
from django.utils import timezone

from apps.accounts.models import User, UserSession
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user
from apps.audit.models import EventType, SecurityEvent
from apps.core.fingerprints import audit_session_fingerprint

pytestmark = pytest.mark.django_db


def _client() -> Client:
    ip = f"10.{secrets.randbelow(254) + 1}.{secrets.randbelow(254) + 1}.1"
    return Client(enforce_csrf_checks=True, REMOTE_ADDR=ip)


def _csrf(client: Client) -> str:
    client.get("/api/browser/v1/auth/session")
    return client.cookies["csrftoken"].value


def _login(
    client: Client,
    kind: str,
    email: str,
    password: str = DEFAULT_PASSWORD,
    *,
    headers: dict[str, str] | None = None,
    language: str = "es",
) -> Any:
    extra = dict(headers or {})
    if kind == "browser" and "X-CSRFToken" not in extra:
        extra["X-CSRFToken"] = _csrf(client)
    return client.post(
        f"/api/{kind}/v1/auth/login",
        data=json.dumps({"email": email, "password": password, "language": language}),
        content_type="application/json",
        headers=extra,
    )


@pytest.mark.parametrize("kind", ["browser", "app"])
def test_login_session_and_logout_lifecycle(kind: str) -> None:
    user = make_user(email="ana@x.com", name="Ana")
    client = _client()
    resp = _login(client, kind, " ANA@X.COM ")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"] == {"email": "ana@x.com", "name": "Ana"}
    assert body["terms_status"] == "no_current_version"
    user.refresh_from_db()
    assert user.last_login is not None
    assert UserSession.objects.filter(user=user).count() == 1
    assert SecurityEvent.objects.filter(event_type=EventType.LOGIN, success=True).count() == 1

    token = body.get("session_token")
    headers = {"X-Session-Token": token} if kind == "app" else {}
    assert client.get(f"/api/{kind}/v1/auth/session", headers=headers).status_code == 200
    already = _login(client, kind, "ana@x.com", headers=headers)
    assert already.status_code == 400 and already.json()["code"] == "already_authenticated"

    out_headers = (
        {**headers, "X-CSRFToken": client.cookies["csrftoken"].value}
        if kind == "browser"
        else headers
    )
    assert client.post(f"/api/{kind}/v1/auth/logout", headers=out_headers).status_code == 200
    assert not UserSession.objects.filter(user=user).exists()
    assert client.get(f"/api/{kind}/v1/auth/session", headers=headers).status_code == 401
    event = SecurityEvent.objects.get(event_type=EventType.LOGOUT, success=True)
    if token:
        assert event.session_key == audit_session_fingerprint(token)


def test_browser_csrf_and_unauthenticated_logout_without_audit() -> None:
    user = make_user()
    client = _client()
    no_csrf = client.post(
        "/api/browser/v1/auth/login",
        data=json.dumps({"email": user.email, "password": DEFAULT_PASSWORD}),
        content_type="application/json",
    )
    assert no_csrf.status_code == 403
    out = client.post("/api/browser/v1/auth/logout", headers={"X-CSRFToken": _csrf(client)})
    assert out.status_code == 401
    assert not SecurityEvent.objects.filter(event_type=EventType.LOGOUT).exists()


def test_queryset_deactivation_invalidates_session_and_deletes_rows() -> None:
    user = make_user()
    client = _client()
    token = _login(client, "app", user.email).json()["session_token"]
    User.objects.filter(pk=user.pk).update(is_active=False)

    resp = client.get("/api/app/v1/auth/session", headers={"X-Session-Token": token})
    assert resp.status_code == 401
    assert not UserSession.objects.filter(user=user).exists()


@override_settings(LOGIN_RATE_IP_PER_MINUTE=2)
def test_login_ip_rate_limit_returns_429_without_audit_event() -> None:
    cache.clear()
    client = _client()
    for _ in range(2):
        assert _login(client, "app", "nobody@x.com", "wrong").status_code == 400
    limited = _login(client, "app", "nobody@x.com", "wrong", language="pt-BR")
    assert limited.status_code == 429
    assert int(limited.headers["Retry-After"]) > 0
    assert limited.json()["retry_after"] > 0
    assert SecurityEvent.objects.filter(event_type=EventType.LOGIN).count() == 2


def test_session_touch_updates_after_interval_and_language_selects_error_text() -> None:
    user = make_user()
    client = _client()
    token = _login(client, "app", user.email).json()["session_token"]
    row = UserSession.objects.get(user=user)
    old = timezone.now() - timedelta(seconds=61)
    UserSession.objects.filter(pk=row.pk).update(last_seen_at=old)

    assert (
        client.get("/api/app/v1/auth/session", headers={"X-Session-Token": token}).status_code
        == 200
    )
    row.refresh_from_db()
    assert row.last_seen_at > old
    en_msg = _login(_client(), "app", "nobody@x.com", "wrong", language="en").json()["message"]
    es_msg = _login(_client(), "app", "nobody@x.com", "wrong", language="es").json()["message"]
    assert en_msg != es_msg
