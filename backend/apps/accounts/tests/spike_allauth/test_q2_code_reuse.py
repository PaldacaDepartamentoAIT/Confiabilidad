from typing import Any

import pytest
from allauth.account.models import EmailAddress
from django.core import mail

from apps.accounts.tests.spike_allauth.conftest import (
    SPIKE_PASSWORD,
    HeadlessClient,
    latest_code,
)


@pytest.mark.django_db
def test_second_validation_in_same_session_is_rejected(
    spike_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    headless_client.post("/auth/signup", {"email": unique_email, "password": SPIKE_PASSWORD})
    code = latest_code(unique_email)

    first_status, _ = headless_client.post("/auth/email/verify", {"key": code})
    session_status, _ = headless_client.get("/auth/session")
    second_status, _ = headless_client.post("/auth/email/verify", {"key": code})

    assert first_status == 200
    assert session_status == 200
    assert second_status == 409


@pytest.mark.django_db
def test_code_from_another_session_is_rejected_before_validation(
    spike_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    headless_client.post("/auth/signup", {"email": unique_email, "password": SPIKE_PASSWORD})
    code = latest_code(unique_email)

    other_status, _ = headless_client.fresh().post("/auth/email/verify", {"key": code})
    verified_after_other = EmailAddress.objects.get(email=unique_email).verified
    original_status, _ = headless_client.post("/auth/email/verify", {"key": code})

    assert other_status == 409
    assert not verified_after_other
    assert original_status == 200


@pytest.mark.django_db
def test_code_from_another_session_is_rejected_after_validation(
    spike_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    headless_client.post("/auth/signup", {"email": unique_email, "password": SPIKE_PASSWORD})
    code = latest_code(unique_email)

    original_status, _ = headless_client.post("/auth/email/verify", {"key": code})
    other_status, _ = headless_client.fresh().post("/auth/email/verify", {"key": code})

    assert original_status == 200
    assert other_status == 409


@pytest.mark.django_db
def test_immediate_resend_is_rate_limited_and_keeps_old_code(
    spike_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    spike_settings.ACCOUNT_EMAIL_VERIFICATION_SUPPORTS_RESEND = True
    headless_client.post("/auth/signup", {"email": unique_email, "password": SPIKE_PASSWORD})
    old_code = latest_code(unique_email)

    resend_status, _ = headless_client.post("/auth/email/verify/resend", {})
    sent = [m for m in mail.outbox if unique_email in m.to]
    old_status, _ = headless_client.post("/auth/email/verify", {"key": old_code})

    assert resend_status == 429
    assert len(sent) == 1
    assert old_status == 200


@pytest.mark.django_db
def test_resend_invalidates_old_code_and_issues_new_one(
    spike_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    spike_settings.ACCOUNT_EMAIL_VERIFICATION_SUPPORTS_RESEND = True
    spike_settings.ACCOUNT_RATE_LIMITS = {"signup": None, "confirm_email": None}
    headless_client.post("/auth/signup", {"email": unique_email, "password": SPIKE_PASSWORD})
    old_code = latest_code(unique_email)

    resend_status, _ = headless_client.post("/auth/email/verify/resend", {})
    new_code = latest_code(unique_email)
    old_status, old_body = headless_client.post("/auth/email/verify", {"key": old_code})
    new_status, _ = headless_client.post("/auth/email/verify", {"key": new_code})

    assert resend_status == 200
    assert new_code != old_code
    assert old_status == 400
    assert old_body["errors"][0]["code"] == "incorrect_code"
    assert new_status == 200
