import pytest
from django.test import Client

from apps.accounts.models import User
from apps.accounts.tests.conftest import TEST_EMAIL, TEST_PASSWORD

BROWSER = "/_allauth/browser/v1"


def _login(client: Client, password: str, csrf: bool) -> int:
    client.get(f"{BROWSER}/auth/session")
    headers = {"X-CSRFToken": client.cookies["csrftoken"].value} if csrf else {}
    resp = client.post(
        f"{BROWSER}/auth/login",
        data={"email": TEST_EMAIL, "password": password},
        content_type="application/json",
        headers=headers,
    )
    return resp.status_code


@pytest.mark.django_db
def test_browser_login_authenticates_and_sets_session(csrf_client: Client, test_user: User) -> None:
    assert _login(csrf_client, TEST_PASSWORD, csrf=True) == 200

    session = csrf_client.get(f"{BROWSER}/auth/session")
    assert session.status_code == 200
    assert session.json()["data"]["user"]["email"] == TEST_EMAIL


@pytest.mark.django_db
def test_browser_login_requires_csrf(csrf_client: Client, test_user: User) -> None:
    assert _login(csrf_client, TEST_PASSWORD, csrf=False) == 403


@pytest.mark.django_db
def test_browser_login_rejects_invalid_credentials(csrf_client: Client, test_user: User) -> None:
    assert _login(csrf_client, "wrong-password", csrf=True) in (400, 401)

    session = csrf_client.get(f"{BROWSER}/auth/session")
    assert session.status_code == 401
