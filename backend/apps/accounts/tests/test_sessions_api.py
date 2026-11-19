import json
import secrets
from datetime import timedelta
from typing import Any

import pytest
from django.test import Client
from django.utils import timezone

from apps.accounts.models import UserSession
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user
from apps.audit.models import EventType, SecurityEvent
from apps.consents.services import accept_terms
from apps.consents.tests.factories import publish_version

pytestmark = pytest.mark.django_db


def _client(ip: str | None = None, user_agent: str = "Agent/1.0") -> Client:
    addr = ip or f"10.{secrets.randbelow(254) + 1}.{secrets.randbelow(254) + 1}.1"
    return Client(enforce_csrf_checks=True, REMOTE_ADDR=addr, HTTP_USER_AGENT=user_agent)


def _csrf(client: Client) -> str:
    if "csrftoken" not in client.cookies:
        client.get("/api/browser/v1/auth/session")
    return client.cookies["csrftoken"].value


def _login(client: Client, kind: str, email: str) -> tuple[Any, dict[str, str]]:
    headers = {"X-CSRFToken": _csrf(client)} if kind == "browser" else {}
    resp = client.post(
        f"/api/{kind}/v1/auth/login",
        data=json.dumps({"email": email, "password": DEFAULT_PASSWORD, "language": "es"}),
        content_type="application/json",
        headers=headers,
    )
    assert resp.status_code == 200
    if kind == "app":
        return resp, {"X-Session-Token": resp.json()["session_token"]}
    return resp, {"X-CSRFToken": client.cookies["csrftoken"].value}


def test_private_session_endpoints_require_auth_csrf_and_current_terms() -> None:
    publish_version(version="1", published_at=timezone.now() - timedelta(days=2))
    user = make_user()
    client = _client()

    assert client.get("/api/app/v1/auth/sessions").status_code == 401
    assert (
        client.post(
            "/api/app/v1/auth/sessions/revoke", data="{}", content_type="application/json"
        ).status_code
        == 401
    )
    assert client.post("/api/app/v1/auth/sessions/revoke-others").status_code == 401
    assert client.post("/api/browser/v1/auth/sessions/revoke-others").status_code == 403

    _, headers = _login(client, "app", user.email)
    for call in [
        lambda: client.get("/api/app/v1/auth/sessions", headers=headers),
        lambda: client.post(
            "/api/app/v1/auth/sessions/revoke",
            data=json.dumps({"session_id": 1}),
            content_type="application/json",
            headers=headers,
        ),
        lambda: client.post("/api/app/v1/auth/sessions/revoke-others", headers=headers),
    ]:
        blocked = call()
        assert blocked.status_code == 403 and blocked.json()["code"] == "terms_required"

    accept_terms(user, version="1", locale="es")
    assert client.get("/api/app/v1/auth/sessions", headers=headers).status_code == 200
    bad_revoke = client.post(
        "/api/app/v1/auth/sessions/revoke",
        data=json.dumps({"session_id": 0}),
        content_type="application/json",
        headers=headers,
    )
    assert bad_revoke.status_code == 400 and "session_id" in bad_revoke.json()["errors"]

    publish_version(version="2", published_at=timezone.now() - timedelta(minutes=1))
    reblocked = client.get("/api/app/v1/auth/sessions", headers=headers)
    assert reblocked.status_code == 403 and reblocked.json()["code"] == "terms_required"


@pytest.mark.parametrize("kind", ["browser", "app"])
def test_list_and_revoke_other_session_across_clients(kind: str) -> None:
    publish_version(version="1", published_at=timezone.now() - timedelta(days=2))
    user = make_user()
    other_user = make_user(email="other@example.com")
    accept_terms(user, version="1", locale="es")
    accept_terms(other_user, version="1", locale="es")

    c_main = _client(ip="192.0.2.10", user_agent="Main/1.0")
    _, main_headers = _login(c_main, kind, user.email)

    other_kind = "app" if kind == "browser" else "browser"
    c_other = _client(ip="192.0.2.11", user_agent="Other/2.0")
    _, other_headers = _login(c_other, other_kind, user.email)

    c_expired = _client(ip="192.0.2.12", user_agent="Expired/1.0")
    _login(c_expired, "app", user.email)
    expired_row = UserSession.objects.get(user=user, ip="192.0.2.12")
    UserSession.objects.filter(pk=expired_row.pk).update(
        last_seen_at=timezone.now() - timedelta(days=30)
    )

    c_foreign = _client()
    _login(c_foreign, "app", other_user.email)
    foreign_row = UserSession.objects.get(user=other_user)

    listed = c_main.get(f"/api/{kind}/v1/auth/sessions", headers=main_headers)
    assert listed.status_code == 200
    rows = listed.json()["sessions"]
    assert len(rows) == 2
    assert not UserSession.objects.filter(pk=expired_row.pk).exists()
    assert all(
        set(item) == {"id", "ip", "user_agent", "created_at", "last_seen_at", "is_current"}
        for item in rows
    )
    current_item = next(item for item in rows if item["is_current"])
    other_item = next(item for item in rows if not item["is_current"])

    self_revoke = c_main.post(
        f"/api/{kind}/v1/auth/sessions/revoke",
        data=json.dumps({"session_id": current_item["id"]}),
        content_type="application/json",
        headers=main_headers,
    )
    assert self_revoke.status_code == 400
    assert self_revoke.json()["code"] == "cannot_revoke_current_session"

    foreign_revoke = c_main.post(
        f"/api/{kind}/v1/auth/sessions/revoke",
        data=json.dumps({"session_id": foreign_row.pk}),
        content_type="application/json",
        headers=main_headers,
    )
    assert foreign_revoke.status_code == 404
    assert foreign_revoke.json()["code"] == "not_found"

    revoked = c_main.post(
        f"/api/{kind}/v1/auth/sessions/revoke",
        data=json.dumps({"session_id": other_item["id"]}),
        content_type="application/json",
        headers=main_headers,
    )
    assert revoked.status_code == 200 and revoked.json() == {"result": "revoked"}
    assert SecurityEvent.objects.filter(event_type=EventType.LOGOUT, success=True).count() == 1
    assert (
        c_other.get(f"/api/{other_kind}/v1/auth/session", headers=other_headers).status_code == 401
    )
    assert c_main.get(f"/api/{kind}/v1/auth/session", headers=main_headers).status_code == 200


@pytest.mark.parametrize("kind", ["browser", "app"])
def test_revoke_others_handles_multiple_and_zero_other_sessions(kind: str) -> None:
    publish_version(version="1", published_at=timezone.now() - timedelta(days=2))
    user = make_user()
    accept_terms(user, version="1", locale="es")

    c_main = _client()
    _, main_headers = _login(c_main, kind, user.email)
    c_extra_browser = _client()
    _login(c_extra_browser, "browser", user.email)
    c_extra_app = _client()
    _, extra_app_headers = _login(c_extra_app, "app", user.email)

    revoked = c_main.post(f"/api/{kind}/v1/auth/sessions/revoke-others", headers=main_headers)
    assert revoked.status_code == 200 and revoked.json() == {
        "result": "revoked",
        "revoked_count": 2,
    }
    assert SecurityEvent.objects.filter(event_type=EventType.LOGOUT, success=True).count() == 2
    assert c_extra_browser.get("/api/browser/v1/auth/session").status_code == 401
    assert c_extra_app.get("/api/app/v1/auth/session", headers=extra_app_headers).status_code == 401
    assert c_main.get(f"/api/{kind}/v1/auth/session", headers=main_headers).status_code == 200

    empty = c_main.post(f"/api/{kind}/v1/auth/sessions/revoke-others", headers=main_headers)
    assert empty.status_code == 200 and empty.json() == {"result": "revoked", "revoked_count": 0}
    assert SecurityEvent.objects.filter(event_type=EventType.LOGOUT).count() == 2
