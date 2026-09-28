from typing import Any

import pytest

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
