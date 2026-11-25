import json
import secrets
from datetime import date
from typing import Any

import pytest
from django.test import Client

from apps.accounts.api import messages
from apps.accounts.api.profile_serializers import ProfileUpdateSerializer
from apps.accounts.api.views import _render
from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user
from apps.audit.models import EventType, SecurityEvent
from apps.consents.models import UserTerms
from apps.consents.tests.factories import publish_version
from apps.emails import locales


@pytest.mark.parametrize("language", locales.SUPPORTED)
@pytest.mark.parametrize("code", ["email_immutable", "unknown_field", "no_profile_fields"])
def test_profile_serializer_error_codes_exist_in_all_languages(code: str, language: str) -> None:
    assert messages.error_text(code, language).strip()


def test_profile_update_serializer_accepts_partial_and_preserves_zz() -> None:
    serializer = ProfileUpdateSerializer(
        data={"name": "  Ana  ", "language": "es"},
        context={"stored_country": "ZZ"},
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data == {"name": "Ana"}

    keep_zz = ProfileUpdateSerializer(data={"country": "zz"}, context={"stored_country": "ZZ"})
    assert keep_zz.is_valid(), keep_zz.errors
    assert keep_zz.validated_data == {"country": "ZZ"}

    restore_zz = ProfileUpdateSerializer(data={"country": "zz"}, context={"stored_country": "ES"})
    assert not restore_zz.is_valid()
    assert _render(restore_zz.errors, "es")["country"][0]["code"] == "country_invalid"


def test_profile_update_serializer_rejects_email_empty_and_unknown_fields() -> None:
    with_email = ProfileUpdateSerializer(data={"name": "Ana", "email": "other@example.com"})
    assert not with_email.is_valid()
    assert _render(with_email.errors, "en")["email"][0]["code"] == "email_immutable"

    empty = ProfileUpdateSerializer(data={"language": "pt-BR"})
    assert not empty.is_valid()
    assert _render(empty.errors, "pt-BR")["non_field_errors"][0]["code"] == "no_profile_fields"

    unknown = ProfileUpdateSerializer(data={"name": "Ana", "nickname": "anny"})
    assert not unknown.is_valid()
    assert _render(unknown.errors, "es")["nickname"][0]["code"] == "unknown_field"

    bad_fields = ProfileUpdateSerializer(data={"name": "Ana  Luis", "birthdate": "2099-01-01"})
    assert not bad_fields.is_valid()
    assert set(bad_fields.errors) == {"name", "birthdate"}


def _client() -> Client:
    ip = f"10.{secrets.randbelow(254) + 1}.{secrets.randbelow(254) + 1}.1"
    return Client(enforce_csrf_checks=True, REMOTE_ADDR=ip)


def _csrf(client: Client) -> str:
    client.get("/api/browser/v1/auth/session")
    return client.cookies["csrftoken"].value


def _login_headers(client: Client, kind: str, user: User, *, accept_terms: bool) -> dict[str, str]:
    if accept_terms:
        docs = publish_version()
        UserTerms.objects.create(user=user, terms=docs["es"])
    headers = {"X-CSRFToken": _csrf(client)} if kind == "browser" else {}
    resp = client.post(
        f"/api/{kind}/v1/auth/login",
        data=json.dumps({"email": user.email, "password": DEFAULT_PASSWORD, "language": "es"}),
        content_type="application/json",
        headers=headers,
    )
    assert resp.status_code == 200
    if kind == "app":
        return {"X-Session-Token": resp.json()["session_token"]}
    return {"X-CSRFToken": client.cookies["csrftoken"].value}


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["browser", "app"])
def test_profile_get_and_patch_flow_in_both_clients(kind: str) -> None:
    user = make_user(
        email="ana@example.com", name="Ana Pérez", birthdate=date(1992, 3, 4), country="ES"
    )
    client = _client()
    headers = _login_headers(client, kind, user, accept_terms=True)
    before = SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT, success=True).count()

    got = client.get(f"/api/{kind}/v1/auth/profile", headers=headers)
    assert got.status_code == 200
    assert got.json() == {
        "email": "ana@example.com",
        "name": "Ana Pérez",
        "birthdate": "1992-03-04",
        "country": "ES",
    }

    patched = client.patch(
        f"/api/{kind}/v1/auth/profile",
        data=json.dumps({"name": "  Ana Maria ", "country": "pt"}),
        content_type="application/json",
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json() == {
        "email": "ana@example.com",
        "name": "Ana Maria",
        "birthdate": "1992-03-04",
        "country": "PT",
    }
    assert (
        SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT, success=True).count()
        == before + 1
    )

    noop = client.patch(
        f"/api/{kind}/v1/auth/profile",
        data=json.dumps({"name": "Ana Maria"}),
        content_type="application/json",
        headers=headers,
    )
    assert noop.status_code == 200
    assert (
        SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT, success=True).count()
        == before + 1
    )


@pytest.mark.django_db
def test_profile_api_rejects_csrf_email_empty_unknown_and_bad_json() -> None:
    user = make_user(email="web@example.com", name="Web User")
    client = _client()
    headers = _login_headers(client, "browser", user, accept_terms=True)

    no_csrf = client.patch(
        "/api/browser/v1/auth/profile",
        data=json.dumps({"name": "Otro"}),
        content_type="application/json",
    )
    assert no_csrf.status_code == 403

    bad_json = client.patch(
        "/api/browser/v1/auth/profile", data="{", content_type="application/json", headers=headers
    )
    assert bad_json.status_code == 400
    assert bad_json.json()["errors"]["non_field_errors"][0]["code"] == "invalid"

    for payload, field, code in [
        ({"email": "otro@example.com", "language": "en"}, "email", "email_immutable"),
        ({"language": "pt-BR"}, "non_field_errors", "no_profile_fields"),
        ({"extra": "val", "language": "es"}, "extra", "unknown_field"),
    ]:
        resp = client.patch(
            "/api/browser/v1/auth/profile",
            data=json.dumps(payload),
            content_type="application/json",
            headers=headers,
        )
        assert resp.status_code == 400
        assert resp.json()["errors"][field][0]["code"] == code

    user.refresh_from_db()
    assert user.email == "web@example.com" and user.name == "Web User"


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["browser", "app"])
def test_profile_api_enforces_terms_and_active_account(kind: str) -> None:
    user = make_user()
    client = _client()
    assert client.get(f"/api/{kind}/v1/auth/profile").status_code == 401
    headers: dict[str, Any] = _login_headers(client, kind, user, accept_terms=False)

    no_terms = client.get(f"/api/{kind}/v1/auth/profile", headers=headers)
    assert no_terms.status_code == 403 and no_terms.json()["code"] == "terms_required"

    patch_no_terms = client.patch(
        f"/api/{kind}/v1/auth/profile",
        data=json.dumps({"name": "Otro"}),
        content_type="application/json",
        headers=headers,
    )
    assert patch_no_terms.status_code == 403 and patch_no_terms.json()["code"] == "terms_required"

    User.objects.filter(pk=user.pk).update(is_active=False)
    assert client.get(f"/api/{kind}/v1/auth/profile", headers=headers).status_code == 401
