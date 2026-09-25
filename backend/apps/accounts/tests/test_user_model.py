import pytest
from django.db import IntegrityError

from apps.accounts.models import User


@pytest.mark.django_db
def test_create_user_normalizes_email() -> None:
    user = User.objects.create_user(email="User@Example.COM", password="secret123")

    assert user.email == "user@example.com"
    assert user.check_password("secret123")
    assert user.is_active
    assert not user.is_staff


@pytest.mark.django_db
def test_create_superuser_sets_flags() -> None:
    admin = User.objects.create_superuser(email="admin@example.com", password="secret123")

    assert admin.is_staff
    assert admin.is_superuser


@pytest.mark.django_db
def test_email_is_unique() -> None:
    User.objects.create_user(email="dup@example.com", password="x")

    with pytest.raises(IntegrityError):
        User.objects.create_user(email="dup@example.com", password="y")
