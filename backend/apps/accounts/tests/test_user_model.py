from datetime import date
from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.db import IntegrityError

from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, DEFAULT_PROFILE, make_user

SUPERUSER_OPTIONS = {
    "email": "admin@example.com",
    "name": "Admin User",
    "birthdate": "1990-01-01",
    "country": "ES",
}


@pytest.mark.django_db
def test_create_user_normalizes_email() -> None:
    user = User.objects.create_user(
        email="User@Example.COM", password="secret123", **DEFAULT_PROFILE
    )

    assert user.email == "user@example.com"
    assert user.check_password("secret123")
    assert user.is_active
    assert not user.is_staff


@pytest.mark.django_db
def test_create_superuser_sets_flags() -> None:
    admin = User.objects.create_superuser(
        email="admin@example.com", password="secret123", **DEFAULT_PROFILE
    )

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


@pytest.mark.django_db
def test_create_user_requires_email() -> None:
    with pytest.raises(ValueError, match="Email is required"):
        User.objects.create_user(email="", password="x", **DEFAULT_PROFILE)


@pytest.mark.django_db
@pytest.mark.parametrize("missing", ["name", "birthdate", "country"])
def test_create_user_requires_profile_fields(missing: str) -> None:
    profile = {key: value for key, value in DEFAULT_PROFILE.items() if key != missing}

    with pytest.raises(ValueError, match=missing):
        User.objects.create_user(email="ana@example.com", password="x", **profile)
    assert not User.objects.exists()


@pytest.mark.django_db
def test_profile_fields_are_stored() -> None:
    user = make_user()
    user.refresh_from_db()

    assert {key: getattr(user, key) for key in DEFAULT_PROFILE} == DEFAULT_PROFILE


@pytest.mark.django_db
def test_createsuperuser_noinput_creates_account_with_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "secret123")

    call_command("createsuperuser", interactive=False, stdout=StringIO(), **SUPERUSER_OPTIONS)

    admin = User.objects.get(email="admin@example.com")
    assert admin.is_superuser
    assert (admin.name, admin.birthdate, admin.country) == ("Admin User", date(1990, 1, 1), "ES")


@pytest.mark.django_db
@pytest.mark.parametrize("missing", ["name", "birthdate", "country"])
def test_createsuperuser_noinput_requires_profile_fields(
    missing: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "secret123")
    options = {key: value for key, value in SUPERUSER_OPTIONS.items() if key != missing}

    with pytest.raises(CommandError, match=missing):
        call_command("createsuperuser", interactive=False, stdout=StringIO(), **options)


@pytest.mark.django_db
def test_direct_save_trims_and_lowercases_email() -> None:
    user = User(email=" Ana@X.com ", **DEFAULT_PROFILE)
    user.save()
    user.refresh_from_db()

    assert user.email == "ana@x.com"


@pytest.mark.django_db
def test_emails_differing_in_case_collide_via_create_user() -> None:
    make_user(email="Ana@x.com")

    with pytest.raises(IntegrityError):
        make_user(email="ana@x.com")


@pytest.mark.django_db
def test_emails_differing_in_case_collide_via_direct_save() -> None:
    make_user(email="ana@x.com")

    with pytest.raises(IntegrityError):
        User(email="Ana@x.com", **DEFAULT_PROFILE).save()


@pytest.mark.django_db
def test_emails_differing_in_case_collide_via_bulk_create() -> None:
    make_user(email="ana@x.com")

    with pytest.raises(IntegrityError):
        User.objects.bulk_create([User(email="Ana@x.com", **DEFAULT_PROFILE)])


@pytest.mark.django_db
def test_emails_differing_in_case_collide_via_queryset_update() -> None:
    make_user(email="ana@x.com")
    other = make_user(email="bob@x.com")

    with pytest.raises(IntegrityError):
        User.objects.filter(pk=other.pk).update(email="Ana@x.com")


@pytest.mark.django_db
def test_email_collides_with_inactive_account() -> None:
    make_user(email="ana@x.com", is_active=False)

    with pytest.raises(IntegrityError):
        User.objects.bulk_create([User(email="Ana@x.com", **DEFAULT_PROFILE)])
