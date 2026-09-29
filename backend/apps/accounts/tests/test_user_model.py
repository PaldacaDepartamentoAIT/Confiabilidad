from datetime import date
from io import StringIO

import pytest
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, DEFAULT_PROFILE, make_user
from apps.accounts.validators import PLACEHOLDER_COUNTRY

SUPERUSER_OPTIONS = {
    "email": "admin@example.com",
    "name": "Admin User",
    "birthdate": "1990-01-01",
    "country": "ES",
}
INVALID_PROFILE_VALUES = [
    pytest.param("name", "Ana  García", id="name"),
    pytest.param("birthdate", date(2020, 1, 1), id="birthdate"),
    pytest.param("country", "XX", id="country"),
]


def _placeholder_user() -> User:
    user = make_user()
    User.objects.filter(pk=user.pk).update(country=PLACEHOLDER_COUNTRY)
    user.refresh_from_db()
    return user


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


@pytest.mark.django_db
@pytest.mark.parametrize(("field", "value"), INVALID_PROFILE_VALUES)
def test_create_user_rejects_invalid_profile(field: str, value: object) -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_user(**{field: value})
    assert field in excinfo.value.error_dict
    assert not User.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(("field", "value"), INVALID_PROFILE_VALUES)
def test_direct_save_rejects_invalid_profile(field: str, value: object) -> None:
    user = make_user()
    setattr(user, field, value)

    with pytest.raises(ValidationError):
        user.save()
    user.refresh_from_db()
    assert getattr(user, field) == DEFAULT_PROFILE[field]


@pytest.mark.django_db
def test_createsuperuser_rejects_invalid_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "secret123")

    with pytest.raises(CommandError, match="ISO 3166-1"):
        call_command(
            "createsuperuser",
            interactive=False,
            stdout=StringIO(),
            **{**SUPERUSER_OPTIONS, "country": "XX"},
        )
    assert not User.objects.exists()


@pytest.mark.django_db
def test_profile_is_normalized_on_save() -> None:
    user = make_user(name="  Ana García  ", country=" es ")
    user.refresh_from_db()

    assert (user.name, user.country) == ("Ana García", "ES")


@pytest.mark.django_db
def test_partial_save_validates_listed_fields() -> None:
    user = make_user()
    user.name = "Ana  García"

    with pytest.raises(ValidationError):
        user.save(update_fields=["name"])


@pytest.mark.django_db
def test_partial_save_skips_unlisted_invalid_fields() -> None:
    user = make_user()
    User.objects.filter(pk=user.pk).update(name="Ana  García")
    user.refresh_from_db()
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    user.refresh_from_db()

    assert user.last_login is not None


@pytest.mark.django_db
def test_new_account_cannot_use_placeholder_country() -> None:
    with pytest.raises(ValidationError):
        make_user(country=PLACEHOLDER_COUNTRY)


@pytest.mark.django_db
def test_placeholder_account_can_record_login() -> None:
    user = _placeholder_user()
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    user.refresh_from_db()

    assert user.last_login is not None


@pytest.mark.django_db
def test_placeholder_account_can_change_name_while_keeping_country() -> None:
    user = _placeholder_user()
    user.name = "Ana García"
    user.save()
    user.refresh_from_db()

    assert (user.name, user.country) == ("Ana García", PLACEHOLDER_COUNTRY)


@pytest.mark.django_db
def test_placeholder_country_cannot_be_restored_after_change() -> None:
    user = _placeholder_user()
    user.country = "ES"
    user.save()
    user.country = PLACEHOLDER_COUNTRY

    with pytest.raises(ValidationError):
        user.save()


@pytest.mark.django_db
def test_new_user_defaults() -> None:
    user = make_user()
    user.refresh_from_db()

    assert user.is_active
    assert not user.is_staff
    assert not user.is_superuser
    assert user.date_joined is not None
    assert user.last_login is None


@pytest.mark.django_db
def test_active_manager_excludes_inactive_accounts() -> None:
    active = make_user()
    inactive = make_user(is_active=False)

    assert list(User.active.all()) == [active]
    assert set(User.objects.all()) == {active, inactive}


@pytest.mark.django_db
def test_email_keeps_dots_and_plus_tag() -> None:
    user = make_user(email=" Ana.B+Tag@X.com ")
    user.refresh_from_db()

    assert user.email == "ana.b+tag@x.com"


@pytest.mark.django_db
def test_modified_email_is_normalized_on_save() -> None:
    user = make_user(email="ana@x.com")
    user.email = " Ana.New+Tag@X.com "
    user.save()
    user.refresh_from_db()

    assert user.email == "ana.new+tag@x.com"


@pytest.mark.django_db
@pytest.mark.parametrize("missing", ["name", "birthdate", "country"])
def test_direct_save_requires_profile_fields(missing: str) -> None:
    profile = {key: value for key, value in DEFAULT_PROFILE.items() if key != missing}

    with pytest.raises(ValidationError) as excinfo:
        User(email="ana@x.com", **profile).save()
    assert missing in excinfo.value.error_dict
    assert not User.objects.exists()


@pytest.mark.django_db
def test_modified_name_and_country_are_normalized_on_save() -> None:
    user = make_user()
    user.name = " Ana López "
    user.country = " mx "
    user.save()
    user.refresh_from_db()

    assert (user.name, user.country) == ("Ana López", "MX")
