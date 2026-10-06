from datetime import date, timedelta

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import PendingRegistration

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
