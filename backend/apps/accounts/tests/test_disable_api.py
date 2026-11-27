import json
import secrets
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.test import Client
from django.utils import timezone

from apps.accounts import throttling
from apps.accounts.api import messages
from apps.accounts.api.profile_serializers import AccountDisableSerializer
from apps.accounts.api.views import _render
from apps.accounts.models import PasswordResetRequest, User, UserSession
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_reset_request, make_user
from apps.audit.models import EventType, SecurityEvent
from apps.companies.models import Company
from apps.consents.models import UserTerms
from apps.consents.tests.factories import publish_version
from apps.emails import locales
from apps.emails.models import EmailTemplate, OutboundEmail


def _client() -> Client:
    ip = f"10.{secrets.randbelow(254) + 1}.{secrets.randbelow(254) + 1}.1"
    return Client(enforce_csrf_checks=True, REMOTE_ADDR=ip)


def _login_headers(
    client: Client,
    kind: str,
    user: User,
    *,
    accept_terms: bool = True,
    password: str = DEFAULT_PASSWORD,
) -> dict[str, str]:
    if accept_terms:
        docs = publish_version()
        UserTerms.objects.create(user=user, terms=docs["es"])
    headers: dict[str, str] = {}
    if kind == "browser":
        client.get("/api/browser/v1/auth/session")
        headers = {"X-CSRFToken": client.cookies["csrftoken"].value}
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


@pytest.mark.parametrize("language", locales.SUPPORTED)
@pytest.mark.parametrize(
    "code",
    ["owns_company", "last_superuser", "account_disabled", "account_disabled_expired"],
)
def test_profile_eligibility_messages_exist_in_all_languages(code: str, language: str) -> None:
    text = messages.error_text(code, language, params={"support_email": "soporte@ejemplo.com"})
    assert text.strip()
    assert "%(" not in text


@pytest.mark.parametrize("language", locales.SUPPORTED)
def test_profile_eligibility_disable_serializer_validation(language: str) -> None:
    missing = AccountDisableSerializer(data={})
    assert not missing.is_valid()
    assert _render(missing.errors, language)["current_password"][0]["code"] == "required"

    blank = AccountDisableSerializer(data={"current_password": ""})
    assert not blank.is_valid()
    assert _render(blank.errors, language)["current_password"][0]["code"] == "blank"

    surrogate = AccountDisableSerializer(data={"current_password": "bad\ud800"})
    assert not surrogate.is_valid()
    assert (
        _render(surrogate.errors, language)["current_password"][0]["code"]
        == "surrogate_characters_not_allowed"
    )


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["browser", "app"])
def test_profile_eligibility_fields_reflect_company_superuser_and_lock(kind: str) -> None:
    cache.clear()
    user = make_user(email=f"elig-{kind}@example.com", is_superuser=True, is_staff=True)
    client = _client()
    headers = _login_headers(client, kind, user)

    first = client.get(f"/api/{kind}/v1/auth/profile", headers=headers).json()
    assert first["can_disable"] is False
    assert first["disable_block_reason"] == "last_superuser"
    assert first["disable_retry_after"] == 0

    make_user(email=f"other-super-{kind}@example.com", is_superuser=True, is_staff=True)
    Company.objects.create(name="Empresa Test", owner=user)
    second = client.get(f"/api/{kind}/v1/auth/profile", headers=headers).json()
    assert second["can_disable"] is False
    assert second["disable_block_reason"] == "owns_company"

    Company.objects.filter(owner=user).delete()
    for _ in range(5):
        throttling.record_account_disable_failure(user.pk)
    third = client.get(f"/api/{kind}/v1/auth/profile", headers=headers).json()
    assert third["can_disable"] is True
    assert third["disable_block_reason"] is None
    assert third["disable_retry_after"] > 0


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["browser", "app"])
def test_disable_endpoint_enforces_terms_csrf_and_prioritizes_blocks(kind: str) -> None:
    cache.clear()
    client = _client()
    assert client.post(f"/api/{kind}/v1/auth/account/disable").status_code in (401, 403)

    user = make_user(email=f"terms-{kind}@example.com", is_superuser=True, is_staff=True)
    headers = _login_headers(client, kind, user, accept_terms=False)
    no_terms = client.post(
        f"/api/{kind}/v1/auth/account/disable",
        data=json.dumps({"current_password": DEFAULT_PASSWORD}),
        content_type="application/json",
        headers=headers,
    )
    assert no_terms.status_code == 403
    assert no_terms.json()["code"] == "terms_required"

    docs = publish_version()
    UserTerms.objects.create(user=user, terms=docs["es"])

    # Último superusuario activo se rechaza antes de evaluar la contraseña.
    last_super = client.post(
        f"/api/{kind}/v1/auth/account/disable",
        data=json.dumps({"current_password": "wrong"}),
        content_type="application/json",
        headers=headers,
    )
    assert last_super.status_code == 400
    assert last_super.json()["code"] == "last_superuser"
    assert throttling.check_account_disable(user.pk).allowed is True

    make_user(email=f"super2-{kind}@example.com", is_superuser=True, is_staff=True)
    Company.objects.create(name="Empresa API", owner=user)
    owns = client.post(
        f"/api/{kind}/v1/auth/account/disable",
        data=json.dumps({"current_password": "wrong"}),
        content_type="application/json",
        headers=headers,
    )
    assert owns.status_code == 400
    assert owns.json()["code"] == "owns_company"
    assert throttling.check_account_disable(user.pk).allowed is True

    if kind == "browser":
        no_csrf = client.post(
            "/api/browser/v1/auth/account/disable",
            data=json.dumps({"current_password": DEFAULT_PASSWORD}),
            content_type="application/json",
        )
        assert no_csrf.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["browser", "app"])
def test_disable_endpoint_lockout_success_revocation_and_login_messages(
    kind: str, django_capture_on_commit_callbacks: object
) -> None:
    cache.clear()
    user = make_user(email=f"api-bye-{kind}@example.com", language="en")
    current_client = _client()
    headers = _login_headers(current_client, kind, user, accept_terms=True)

    other_kind = "app" if kind == "browser" else "browser"
    other_client = _client()
    other_headers = _login_headers(other_client, other_kind, user, accept_terms=False)
    make_reset_request(user.email)

    for _ in range(5):
        wrong = current_client.post(
            f"/api/{kind}/v1/auth/account/disable",
            data=json.dumps({"current_password": "wrong", "language": "es"}),
            content_type="application/json",
            headers=headers,
        )
        assert wrong.status_code == 400
        assert wrong.json()["errors"]["current_password"][0]["code"] == "current_password_incorrect"

    locked = current_client.post(
        f"/api/{kind}/v1/auth/account/disable",
        data=json.dumps({"current_password": DEFAULT_PASSWORD, "language": "es"}),
        content_type="application/json",
        headers=headers,
    )
    assert locked.status_code == 429
    assert int(locked.headers["Retry-After"]) > 0
    assert locked.json()["retry_after"] > 0

    throttling.clear_account_disable_failures(user.pk)
    before_audit = SecurityEvent.objects.filter(event_type=EventType.ACCOUNT_DISABLE).count()
    before_emails = OutboundEmail.objects.count()

    with django_capture_on_commit_callbacks(execute=True):  # type: ignore[operator]
        ok = current_client.post(
            f"/api/{kind}/v1/auth/account/disable",
            data=json.dumps({"current_password": DEFAULT_PASSWORD, "language": "es"}),
            content_type="application/json",
            headers=headers,
        )
    assert ok.status_code == 200
    assert ok.json() == {"result": "account_disabled"}

    user.refresh_from_db()
    assert user.is_active is False
    assert UserSession.objects.filter(user=user).count() == 0
    assert not PasswordResetRequest.objects.filter(user=user).exists()
    assert SecurityEvent.objects.filter(event_type=EventType.ACCOUNT_DISABLE).count() == (
        before_audit + 1
    )
    queued = OutboundEmail.objects.order_by("-pk").first()
    assert OutboundEmail.objects.count() == before_emails + 1
    assert queued is not None and queued.kind == EmailTemplate.Kind.ACCOUNT_DISABLED
    assert queued.locale == "en"

    # Revocación inmediata en ambas sesiones.
    assert current_client.get(f"/api/{kind}/v1/auth/session", headers=headers).status_code == 401
    assert (
        other_client.get(f"/api/{other_kind}/v1/auth/session", headers=other_headers).status_code
        == 401
    )

    # Login tras baja: mensaje específico con clave válida y neutro si falla la contraseña.
    login_client = _client()
    login_headers = (
        {"X-CSRFToken": login_client.cookies["csrftoken"].value}
        if kind == "browser" and login_client.get("/api/browser/v1/auth/session")
        else {}
    )
    bad_pw = login_client.post(
        f"/api/{kind}/v1/auth/login",
        data=json.dumps({"email": user.email, "password": "wrong", "language": "es"}),
        content_type="application/json",
        headers=login_headers,
    )
    assert bad_pw.status_code == 400 and bad_pw.json()["code"] == "invalid_credentials"

    valid_disabled = login_client.post(
        f"/api/{kind}/v1/auth/login",
        data=json.dumps({"email": user.email, "password": DEFAULT_PASSWORD, "language": "es"}),
        content_type="application/json",
        headers=login_headers,
    )
    assert valid_disabled.status_code == 400
    assert valid_disabled.json()["code"] == "account_disabled"

    User.objects.filter(pk=user.pk).update(disabled_at=timezone.now() - timedelta(days=400))
    valid_expired = login_client.post(
        f"/api/{kind}/v1/auth/login",
        data=json.dumps({"email": user.email, "password": DEFAULT_PASSWORD, "language": "es"}),
        content_type="application/json",
        headers=login_headers,
    )
    assert valid_expired.status_code == 400
    assert valid_expired.json()["code"] == "account_disabled_expired"
