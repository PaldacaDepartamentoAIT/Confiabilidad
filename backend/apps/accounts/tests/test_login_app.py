import pytest
from django.test import Client

from apps.accounts.models import User
from apps.accounts.tests.conftest import TEST_EMAIL, TEST_PASSWORD

APP = "/_allauth/app/v1"


@pytest.mark.django_db
def test_app_login_returns_token_and_authenticates(test_user: User) -> None:
    client = Client()
    resp = client.post(
        f"{APP}/auth/login",
        data={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        content_type="application/json",
    )
    assert resp.status_code == 200

    token = resp.json()["meta"]["session_token"]
    assert token

    session = client.get(f"{APP}/auth/session", headers={"X-Session-Token": token})
    assert session.status_code == 200
    assert session.json()["data"]["user"]["email"] == TEST_EMAIL
