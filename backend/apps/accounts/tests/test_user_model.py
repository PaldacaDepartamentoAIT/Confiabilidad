import pytest
from django.db import IntegrityError

from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user


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
    make_user(email="dup@example.com")

    with pytest.raises(IntegrityError):
        make_user(email="dup@example.com")


@pytest.mark.django_db
def test_make_user_creates_active_user_with_default_password() -> None:
    user = make_user()

    assert user.pk is not None
    assert user.is_active
    assert user.check_password(DEFAULT_PASSWORD)


@pytest.mark.django_db
def test_make_user_generates_distinct_emails() -> None:
    assert make_user().email != make_user().email


@pytest.mark.django_db
def test_make_user_applies_overrides() -> None:
    user = make_user(email="ana@example.com", is_staff=True)

    assert user.email == "ana@example.com"
    assert user.is_staff
