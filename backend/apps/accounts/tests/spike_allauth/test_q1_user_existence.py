from typing import Any

import pytest

from apps.accounts.models import User
from apps.accounts.tests.spike_allauth.conftest import (
    SPIKE_PASSWORD,
    HeadlessClient,
    latest_code,
    pending_flows,
)


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
