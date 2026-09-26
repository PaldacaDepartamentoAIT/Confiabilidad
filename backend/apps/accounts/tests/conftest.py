import pytest
from django.test import Client

from apps.accounts.models import User

TEST_EMAIL = "web@example.com"
TEST_PASSWORD = "secret123"


@pytest.fixture
def test_user() -> User:
    return User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)


@pytest.fixture
def csrf_client() -> Client:
    return Client(enforce_csrf_checks=True)
