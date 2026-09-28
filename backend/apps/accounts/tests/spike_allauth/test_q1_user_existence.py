from typing import Any

import pytest
from allauth.account.models import EmailAddress
from django.core import mail

from apps.accounts.models import User
from apps.accounts.tests.spike_allauth.conftest import (
    CODE_PATTERN,
    SPIKE_PASSWORD,
    HeadlessClient,
    latest_code,
    pending_flows,
)

ADAPTERS = "apps.accounts.tests.spike_allauth.adapters"


@pytest.mark.django_db
def test_signup_creates_user_before_code_is_verified(
    spike_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    status, body = headless_client.post(
        "/auth/signup", {"email": unique_email, "password": SPIKE_PASSWORD}
    )

    assert status == 401
    assert pending_flows(body) == ["verify_email"]
    assert latest_code(unique_email)
    assert User.objects.filter(email=unique_email).exists()


@pytest.mark.django_db
def test_code_request_for_unknown_email_sends_no_code(
    login_by_code_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    status, body = headless_client.post("/auth/code/request", {"email": unique_email})

    assert status == 401
    assert pending_flows(body) == ["login_by_code"]
    sent = [m for m in mail.outbox if unique_email in m.to]
    assert len(sent) == 1
    assert "Unknown Account" in sent[0].subject
    assert not CODE_PATTERN.search(str(sent[0].body))
    assert not User.objects.filter(email=unique_email).exists()


@pytest.mark.django_db
def test_confirming_code_for_unknown_email_creates_no_user(
    login_by_code_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    headless_client.post("/auth/code/request", {"email": unique_email})

    status, body = headless_client.post("/auth/code/confirm", {"code": "ABCD-EFGH"})

    assert status == 400
    assert body["errors"][0]["code"] == "incorrect_code"
    assert not User.objects.filter(email=unique_email).exists()


@pytest.mark.django_db
def test_signup_cannot_defer_user_creation_through_adapter(
    spike_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    spike_settings.ACCOUNT_ADAPTER = f"{ADAPTERS}.DeferredSaveAdapter"

    with pytest.raises(ValueError, match="unsaved related object 'user'"):
        headless_client.post("/auth/signup", {"email": unique_email, "password": SPIKE_PASSWORD})

    assert not User.objects.filter(email=unique_email).exists()


@pytest.mark.django_db
def test_trusted_email_adapter_creates_verified_user_without_code(
    spike_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    spike_settings.ACCOUNT_ADAPTER = f"{ADAPTERS}.TrustedEmailAdapter"

    status, _ = headless_client.post(
        "/auth/signup", {"email": unique_email, "password": SPIKE_PASSWORD}
    )

    assert status == 200
    assert User.objects.filter(email=unique_email).exists()
    assert EmailAddress.objects.get(email=unique_email).verified
    assert not [m for m in mail.outbox if unique_email in m.to]
