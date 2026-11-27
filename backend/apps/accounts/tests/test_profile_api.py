import json
import secrets
from datetime import date
from typing import Any

import pytest
from django.core.cache import cache
from django.test import Client, override_settings

from apps.accounts.api import messages
from apps.accounts.api.profile_serializers import PasswordChangeSerializer, ProfileUpdateSerializer
from apps.accounts.api.views import _render
from apps.accounts.models import User, UserSession
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user
from apps.audit.models import EventType, SecurityEvent
from apps.consents.models import UserTerms
from apps.consents.tests.factories import publish_version
from apps.emails import locales
from apps.emails.models import OutboundEmail


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


def _login_headers(
    client: Client, kind: str, user: User, *, accept_terms: bool, password: str = DEFAULT_PASSWORD
) -> dict[str, str]:
    if accept_terms:
        docs = publish_version()
        UserTerms.objects.create(user=user, terms=docs["es"])
    headers = {"X-CSRFToken": _csrf(client)} if kind == "browser" else {}
    resp = client.post(
        f"/api/{kind}/v1/auth/login",
        data=json.dumps({"email": user.email, "password": password, "language": "es"}),
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


@pytest.mark.parametrize("language", locales.SUPPORTED)
def test_password_serializer_messages_and_forbidden_chars(language: str) -> None:
    assert messages.error_text("current_password_incorrect", language).strip()

    missing = PasswordChangeSerializer(data={})
    assert not missing.is_valid()
    assert _render(missing.errors, language)["current_password"][0]["code"] == "required"

    surrogate = PasswordChangeSerializer(
        data={"current_password": "ok", "new_password": "bad\ud800"}
    )
    assert not surrogate.is_valid()
    assert (
        _render(surrogate.errors, language)["new_password"][0]["code"]
        == "surrogate_characters_not_allowed"
    )

    partial = PasswordChangeSerializer(data={"current_password": "wrong"})
    assert partial.is_valid(), partial.errors


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["browser", "app"])
def test_password_change_endpoint_keeps_current_session_and_revokes_others(kind: str) -> None:
    cache.clear()
    user = make_user(email="pwapi@example.com", password="OldPassword123!", language="en")
    current_client = _client()
    current_headers = _login_headers(
        current_client, kind, user, accept_terms=True, password="OldPassword123!"
    )
    other_kind = "app" if kind == "browser" else "browser"
    other_client = _client()
    other_headers = _login_headers(
        other_client, other_kind, user, accept_terms=False, password="OldPassword123!"
    )
    before_pw = SecurityEvent.objects.filter(event_type=EventType.PASSWORD_CHANGE).count()
    before_mail = OutboundEmail.objects.count()

    resp = current_client.post(
        f"/api/{kind}/v1/auth/password/change",
        data=json.dumps(
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
                "language": "es",
            }
        ),
        content_type="application/json",
        headers=current_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"result": "password_changed"}
    if kind == "browser":
        current_headers = {"X-CSRFToken": current_client.cookies["csrftoken"].value}

    assert (
        current_client.get(f"/api/{kind}/v1/auth/profile", headers=current_headers).status_code
        == 200
    )
    assert (
        other_client.get(f"/api/{other_kind}/v1/auth/session", headers=other_headers).status_code
        == 401
    )
    assert UserSession.objects.filter(user=user).count() == 1
    assert (
        SecurityEvent.objects.filter(event_type=EventType.PASSWORD_CHANGE).count() == before_pw + 1
    )
    queued = list(OutboundEmail.objects.order_by("pk")[before_mail:])
    assert [(m.kind, m.locale) for m in queued] == [
        ("password_changed", "en"),
        ("sessions_closed", "en"),
    ]

    # Nueva contraseña inicia sesión; antigua falla.
    assert (
        _client()
        .post(
            "/api/app/v1/auth/login",
            data=json.dumps({"email": user.email, "password": "NewPassword456!"}),
            content_type="application/json",
        )
        .status_code
        == 200
    )


@pytest.mark.django_db
@override_settings(PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS=2)
def test_password_change_endpoint_validation_lockout_terms_and_csrf() -> None:
    cache.clear()
    user = make_user(email="pwlock@example.com", password="ValidPassword1!")
    client = _client()
    assert (
        client.post(
            "/api/app/v1/auth/password/change", data="{}", content_type="application/json"
        ).status_code
        == 401
    )

    app_headers = _login_headers(
        client, "app", user, accept_terms=False, password="ValidPassword1!"
    )
    terms_blocked = client.post(
        "/api/app/v1/auth/password/change",
        data=json.dumps({"current_password": "ValidPassword1!", "new_password": "NewPassword9!"}),
        content_type="application/json",
        headers=app_headers,
    )
    assert terms_blocked.status_code == 403 and terms_blocked.json()["code"] == "terms_required"

    browser = _client()
    b_headers = _login_headers(
        browser, "browser", user, accept_terms=True, password="ValidPassword1!"
    )
    no_csrf = browser.post(
        "/api/browser/v1/auth/password/change",
        data=json.dumps({"current_password": "ValidPassword1!", "new_password": "NewPassword9!"}),
        content_type="application/json",
    )
    assert no_csrf.status_code == 403

    # Fallo 1 con new_password ausente también cuenta en RF-008.
    fail1 = browser.post(
        "/api/browser/v1/auth/password/change",
        data=json.dumps({"current_password": "wrong", "language": "pt-BR"}),
        content_type="application/json",
        headers=b_headers,
    )
    assert fail1.status_code == 400
    assert fail1.json()["errors"]["current_password"][0]["code"] == "current_password_incorrect"
    assert fail1.json()["errors"]["new_password"][0]["code"] == "required"

    # Fallo 2 con new_password débil activa el bloqueo tras este intento.
    fail2 = browser.post(
        "/api/browser/v1/auth/password/change",
        data=json.dumps({"current_password": "wrong", "new_password": "123", "language": "es"}),
        content_type="application/json",
        headers=b_headers,
    )
    assert fail2.status_code == 400
    assert fail2.json()["errors"]["current_password"][0]["code"] == "current_password_incorrect"
    assert fail2.json()["errors"]["new_password"][0]["code"] == "password_too_short"

    # Petición 3 recibe 429 sin evaluar contraseñas y mantiene la sesión actual abierta.
    locked = browser.post(
        "/api/browser/v1/auth/password/change",
        data=json.dumps({"current_password": "ValidPassword1!", "new_password": "NewPassword9!"}),
        content_type="application/json",
        headers=b_headers,
    )
    assert locked.status_code == 429
    assert int(locked.headers["Retry-After"]) > 0 and locked.json()["retry_after"] > 0
    assert browser.get("/api/browser/v1/auth/profile", headers=b_headers).status_code == 200


@pytest.mark.django_db(transaction=True)
@override_settings(PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS=2)
def test_password_change_lockout_shared_across_sessions_and_reset_on_success() -> None:
    cache.clear()
    user = make_user(email="sharedlock@example.com", password="ValidPassword1!")
    browser = _client()
    b_headers = _login_headers(
        browser, "browser", user, accept_terms=True, password="ValidPassword1!"
    )
    app = _client()
    app_headers = _login_headers(app, "app", user, accept_terms=True, password="ValidPassword1!")

    # Fallo 1 desde web y fallo 2 desde escritorio comparten el mismo contador de la cuenta.
    fail_web = browser.post(
        "/api/browser/v1/auth/password/change",
        data=json.dumps({"current_password": "wrong-web", "new_password": "NewPassword9!"}),
        content_type="application/json",
        headers=b_headers,
    )
    assert fail_web.status_code == 400

    fail_app = app.post(
        "/api/app/v1/auth/password/change",
        data=json.dumps({"current_password": "wrong-app", "new_password": "NewPassword9!"}),
        content_type="application/json",
        headers=app_headers,
    )
    assert fail_app.status_code == 400

    locked_web = browser.post(
        "/api/browser/v1/auth/password/change",
        data=json.dumps({"current_password": "ValidPassword1!", "new_password": "NewPassword9!"}),
        content_type="application/json",
        headers=b_headers,
    )
    locked_app = app.post(
        "/api/app/v1/auth/password/change",
        data=json.dumps({"current_password": "ValidPassword1!", "new_password": "NewPassword9!"}),
        content_type="application/json",
        headers=app_headers,
    )
    assert locked_web.status_code == 429 and int(locked_web.headers["Retry-After"]) > 0
    assert locked_app.status_code == 429 and int(locked_app.headers["Retry-After"]) > 0
    assert browser.get("/api/browser/v1/auth/profile", headers=b_headers).status_code == 200
    assert app.get("/api/app/v1/auth/profile", headers=app_headers).status_code == 200

    # Otra cuenta acumula 1 fallo, acierta (reinicia contador) y vuelve a disponer de 2 fallos.
    user2 = make_user(email="resetapi@example.com", password="ValidPassword1!")
    client2 = _client()
    headers2 = _login_headers(client2, "app", user2, accept_terms=True, password="ValidPassword1!")

    assert (
        client2.post(
            "/api/app/v1/auth/password/change",
            data=json.dumps({"current_password": "wrong-1", "new_password": "NewPassword9!"}),
            content_type="application/json",
            headers=headers2,
        ).status_code
        == 400
    )
    assert (
        client2.post(
            "/api/app/v1/auth/password/change",
            data=json.dumps(
                {"current_password": "ValidPassword1!", "new_password": "NewPassword9!"}
            ),
            content_type="application/json",
            headers=headers2,
        ).status_code
        == 200
    )
    assert (
        client2.post(
            "/api/app/v1/auth/password/change",
            data=json.dumps({"current_password": "wrong-2", "new_password": "NewPassword10!"}),
            content_type="application/json",
            headers=headers2,
        ).status_code
        == 400
    )
    assert (
        client2.post(
            "/api/app/v1/auth/password/change",
            data=json.dumps({"current_password": "wrong-3", "new_password": "NewPassword10!"}),
            content_type="application/json",
            headers=headers2,
        ).status_code
        == 400
    )
    assert (
        client2.post(
            "/api/app/v1/auth/password/change",
            data=json.dumps(
                {"current_password": "NewPassword9!", "new_password": "NewPassword10!"}
            ),
            content_type="application/json",
            headers=headers2,
        ).status_code
        == 429
    )
