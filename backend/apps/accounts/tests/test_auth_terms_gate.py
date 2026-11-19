import json
import secrets
from datetime import timedelta
from typing import Any, ClassVar

import pytest
from django.core.exceptions import ValidationError
from django.test import Client, RequestFactory
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import sessions
from apps.accounts.api import auth_views
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user
from apps.consents.models import Terms, UserTerms
from apps.consents.tests.factories import publish_version

pytestmark = pytest.mark.django_db


class _PrivateGateProbe(APIView):
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]
    client_kind: ClassVar[str] = "app"

    def get(self, request: Request) -> Response:
        auth = auth_views._require_auth(request, self.client_kind, "es", require_terms=True)
        if isinstance(auth, Response):
            return auth
        return Response({"ok": True})


def _client() -> Client:
    ip = f"10.{secrets.randbelow(254) + 1}.{secrets.randbelow(254) + 1}.1"
    return Client(enforce_csrf_checks=True, REMOTE_ADDR=ip)


def _csrf(client: Client) -> str:
    client.get("/api/browser/v1/auth/session")
    return client.cookies["csrftoken"].value


def _login(client: Client, kind: str, email: str) -> Any:
    headers = {"X-CSRFToken": _csrf(client)} if kind == "browser" else {}
    return client.post(
        f"/api/{kind}/v1/auth/login",
        data=json.dumps({"email": email, "password": DEFAULT_PASSWORD, "language": "es"}),
        content_type="application/json",
        headers=headers,
    )


def _accept(client: Client, kind: str, body: Any, *, token: str | None = None) -> Any:
    headers: dict[str, str] = {}
    if kind == "browser":
        headers["X-CSRFToken"] = (
            client.cookies["csrftoken"].value if "csrftoken" in client.cookies else _csrf(client)
        )
    elif token:
        headers["X-Session-Token"] = token
    return client.post(
        f"/api/{kind}/v1/auth/terms/accept",
        data=json.dumps(body),
        content_type="application/json",
        headers=headers,
    )


@pytest.mark.parametrize("kind", ["browser", "app"])
def test_terms_accept_flow_and_session_status(kind: str) -> None:
    publish_version(version="1", published_at=timezone.now() - timedelta(days=2))
    user = make_user()
    client = _client()

    login_resp = _login(client, kind, user.email)
    assert login_resp.status_code == 200
    login_body = login_resp.json()
    assert login_body["terms_status"] == "not_accepted"
    assert login_body["terms"]["version"] == "1"
    token = login_body.get("session_token")

    accepted = _accept(
        client, kind, {"version": "1", "locale": "es", "accepted": True}, token=token
    )
    assert accepted.status_code == 200
    assert accepted.json() == {"terms_status": "accepted"}
    assert UserTerms.objects.filter(user=user, terms__version="1").exists()

    headers = {"X-Session-Token": token} if token else {}
    sess = client.get(f"/api/{kind}/v1/auth/session", headers=headers)
    assert sess.status_code == 200
    assert sess.json()["terms_status"] == "accepted"
    assert sess.json()["terms"] is None


def test_terms_accept_requires_auth_csrf_and_valid_document() -> None:
    publish_version(version="1", published_at=timezone.now() - timedelta(days=2))
    publish_version(version="2", published_at=timezone.now() - timedelta(days=1))
    publish_version(kind=Terms.Kind.MARKETING, version="m1")
    user = make_user()
    client = _client()

    assert (
        _accept(client, "app", {"version": "2", "locale": "es", "accepted": True}).status_code
        == 401
    )
    no_csrf = client.post(
        "/api/browser/v1/auth/terms/accept",
        data=json.dumps({"version": "2", "locale": "es", "accepted": True}),
        content_type="application/json",
    )
    assert no_csrf.status_code == 403

    token = _login(client, "app", user.email).json()["session_token"]
    for payload, expected_code in [
        ({"version": "2", "locale": "es", "accepted": False}, "terms_not_accepted"),
        ({"version": "99", "locale": "es", "accepted": True}, "document_not_found"),
        ({"version": "m1", "locale": "es", "accepted": True}, "wrong_kind"),
        ({"version": "1", "locale": "es", "accepted": True}, "not_current_document"),
    ]:
        resp = _accept(client, "app", payload, token=token)
        assert resp.status_code == 400
        assert resp.json()["errors"]["non_field_errors"][0]["code"] == expected_code


def test_terms_accept_without_current_version_and_concurrent_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = make_user()
    client = _client()
    token = _login(client, "app", user.email).json()["session_token"]

    missing = _accept(
        client, "app", {"version": "1", "locale": "es", "accepted": True}, token=token
    )
    assert missing.status_code == 400
    assert missing.json()["errors"]["non_field_errors"][0]["code"] == "no_current_version"

    publish_version(version="1", published_at=timezone.now() - timedelta(days=1))

    def _boom(*_args: Any, **_kwargs: Any) -> Any:
        raise ValidationError("outdated", code="not_current_document")

    monkeypatch.setattr(auth_views, "accept_terms", _boom)
    race = _accept(client, "app", {"version": "1", "locale": "es", "accepted": True}, token=token)
    assert race.status_code == 400
    assert race.json()["errors"]["non_field_errors"][0]["code"] == "not_current_document"


def test_private_gate_blocks_until_accepted_and_rechecks_new_versions() -> None:
    user = make_user()
    client = _client()
    token = _login(client, "app", user.email).json()["session_token"]

    probe = _PrivateGateProbe.as_view()
    factory = RequestFactory()

    # Sin versión vigente: sesión y logout permitidos; área privada bloqueada.
    assert (
        client.get("/api/app/v1/auth/session", headers={"X-Session-Token": token}).status_code
        == 200
    )
    gate_none = probe(factory.get("/", HTTP_X_SESSION_TOKEN=token))
    assert gate_none.status_code == 403
    assert gate_none.data["code"] == "terms_required"
    assert gate_none.data["terms_status"] == "no_current_version"

    # Versión v1 sin aceptar: bloqueado hasta aceptar.
    publish_version(version="1", published_at=timezone.now() - timedelta(days=2))
    gate_v1 = probe(factory.get("/", HTTP_X_SESSION_TOKEN=token))
    assert gate_v1.status_code == 403 and gate_v1.data["terms_status"] == "not_accepted"

    assert (
        _accept(
            client, "app", {"version": "1", "locale": "es", "accepted": True}, token=token
        ).status_code
        == 200
    )
    assert probe(factory.get("/", HTTP_X_SESSION_TOKEN=token)).status_code == 200

    # Nueva versión v2 obligatoria en caliente con la sesión ya abierta (C-06).
    publish_version(version="2", published_at=timezone.now() - timedelta(minutes=1))
    gate_v2 = probe(factory.get("/", HTTP_X_SESSION_TOKEN=token))
    assert gate_v2.status_code == 403 and gate_v2.data["terms_status"] == "not_accepted"

    assert (
        client.post("/api/app/v1/auth/logout", headers={"X-Session-Token": token}).status_code
        == 200
    )
    assert not sessions.is_session_active(token, user.pk)
