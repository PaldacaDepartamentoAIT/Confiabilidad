from typing import Any

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.accounts.tests.factories import make_user

TEST_EMAIL = "web@example.com"
TEST_PASSWORD = "secret123"


@pytest.fixture
def test_user() -> User:
    return make_user(email=TEST_EMAIL, password=TEST_PASSWORD)


@pytest.fixture
def csrf_client() -> Client:
    return Client(enforce_csrf_checks=True)


@pytest.fixture(autouse=True)
def _no_pwned_passwords_requests(settings: Any) -> None:
    settings.PWNED_PASSWORDS_ENABLED = False
