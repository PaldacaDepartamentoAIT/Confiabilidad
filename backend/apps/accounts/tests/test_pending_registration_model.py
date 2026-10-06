from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import PendingRegistration
from apps.accounts.tests.factories import make_user

pytestmark = pytest.mark.django_db


def _pending(email: str = "ana@x.com", public_id: str = "pid-1") -> PendingRegistration:
    return PendingRegistration(
        email=email,
        name="Ana García",
        birthdate=date(1990, 5, 10),
        country="ES",
        public_id=public_id,
        code_hash="a" * 64,
        code_expires_at=timezone.now() + timedelta(minutes=15),
    )


def test_all_fields_are_stored() -> None:
    expires = timezone.now() + timedelta(minutes=15)
    pending = _pending()
    pending.code_expires_at = expires
    pending.save()

    stored = PendingRegistration.objects.get(pk=pending.pk)
    assert (stored.email, stored.name, stored.birthdate, stored.country) == (
        "ana@x.com",
        "Ana García",
        date(1990, 5, 10),
        "ES",
    )
    assert (stored.public_id, stored.code_hash, stored.code_expires_at) == (
        "pid-1",
        "a" * 64,
        expires,
    )
    assert stored.failed_attempts == 0
    assert stored.code_validated_at is None
    assert stored.created_at is not None


def test_email_is_unique_ignoring_case_even_in_bulk_create() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        PendingRegistration.objects.bulk_create(
            [_pending("Ana@x.com", "pid-1"), _pending("ana@x.com", "pid-2")]
        )


def test_public_id_is_unique() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        PendingRegistration.objects.bulk_create(
            [_pending("ana@x.com", "same"), _pending("bea@x.com", "same")]
        )


def test_model_and_migrations_are_in_sync() -> None:
    call_command("makemigrations", "accounts", "--check", "--dry-run", verbosity=0)


def test_profile_is_normalized_on_save() -> None:
    pending = _pending(email="  Ana@X.com ")
    pending.name, pending.country = "  Ana García  ", " es "
    pending.save()

    stored = PendingRegistration.objects.get(pk=pending.pk)
    assert (stored.email, stored.name, stored.country) == ("ana@x.com", "Ana García", "ES")
    assert str(stored) == "ana@x.com"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("name", "Ana  García", id="name"),
        pytest.param("birthdate", date(2020, 1, 1), id="birthdate"),
        pytest.param("country", "XX", id="country"),
        pytest.param("country", "ZZ", id="placeholder-country"),
    ],
)
def test_invalid_profile_is_rejected(field: str, value: object) -> None:
    pending = _pending()
    setattr(pending, field, value)

    with pytest.raises(ValidationError) as excinfo:
        pending.save()
    assert field in excinfo.value.error_dict
    assert not PendingRegistration.objects.exists()


@pytest.mark.parametrize("is_active", [True, False])
def test_email_with_account_is_not_saved(is_active: bool) -> None:
    make_user(email="ana@x.com", is_active=is_active)

    with pytest.raises(ValidationError) as excinfo:
        _pending("ANA@x.com").save()
    assert "email" in excinfo.value.error_dict
    assert not PendingRegistration.objects.exists()


def test_partial_save_skips_unlisted_fields_and_account_check() -> None:
    pending = _pending()
    pending.save()
    make_user(email="ana@x.com")
    PendingRegistration.objects.filter(pk=pending.pk).update(name="Ana  García")
    pending.refresh_from_db()

    pending.failed_attempts = 1
    pending.save(update_fields=["failed_attempts"])

    pending.refresh_from_db()
    assert pending.failed_attempts == 1
