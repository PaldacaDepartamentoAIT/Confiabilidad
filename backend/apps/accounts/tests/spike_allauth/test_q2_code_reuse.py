from typing import Any

import pytest
from allauth.account.models import EmailAddress

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
