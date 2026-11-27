import json
import secrets

import pytest
from django.core.cache import cache
from django.test import Client

from apps.accounts import throttling
from apps.accounts.api import messages
from apps.accounts.api.profile_serializers import AccountDisableSerializer
from apps.accounts.api.views import _render
from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user
from apps.companies.models import Company
from apps.consents.models import UserTerms
from apps.consents.tests.factories import publish_version
from apps.emails import locales


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
