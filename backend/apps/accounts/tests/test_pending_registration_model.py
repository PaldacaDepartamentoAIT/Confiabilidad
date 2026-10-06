from datetime import date, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import override_settings
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
        pytest.param("email", "not-an-email", id="email"),
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


def _ago(minutes: int) -> datetime:
    return timezone.now() - timedelta(minutes=minutes)


def _saved(email: str = "ana@x.com", **changes: object) -> PendingRegistration:
    pending = _pending(email, public_id=email)
    pending.save()
    if changes:
        PendingRegistration.objects.filter(pk=pending.pk).update(**changes)
    pending.refresh_from_db()
    return pending


def _is_expired_everywhere(pending: PendingRegistration) -> bool:
    in_queryset = PendingRegistration.objects.expired().filter(pk=pending.pk).exists()
    assert pending.is_expired is in_queryset
    return in_queryset


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        pytest.param({}, False, id="new"),
        pytest.param({"code_expires_at": 14}, False, id="within-grace"),
        pytest.param({"code_expires_at": 16}, True, id="after-grace"),
        pytest.param({"created_at": 59}, False, id="within-lifetime"),
        pytest.param({"created_at": 61}, True, id="after-lifetime-with-valid-code"),
    ],
)
def test_expiry_is_whichever_comes_first(changes: dict[str, int], expected: bool) -> None:
    pending = _saved("ana@x.com", **{field: _ago(minutes) for field, minutes in changes.items()})

    assert _is_expired_everywhere(pending) is expected


@override_settings(REGISTRATION_GRACE_MINUTES=5, REGISTRATION_MAX_LIFETIME_MINUTES=30)
def test_expiry_follows_settings() -> None:
    assert _is_expired_everywhere(_saved("a@x.com", code_expires_at=_ago(6)))
    assert not _is_expired_everywhere(_saved("b@x.com", code_expires_at=_ago(4)))
    assert _is_expired_everywhere(_saved("c@x.com", created_at=_ago(31)))
    assert not _is_expired_everywhere(_saved("d@x.com", created_at=_ago(29)))


def test_locked_at_max_failed_attempts() -> None:
    assert not _saved("a@x.com", failed_attempts=4).is_locked
    assert _saved("b@x.com", failed_attempts=5).is_locked


@override_settings(REGISTRATION_MAX_FAILED_ATTEMPTS=3)
def test_lock_follows_settings() -> None:
    assert not _saved("a@x.com", failed_attempts=2).is_locked
    assert _saved("b@x.com", failed_attempts=3).is_locked
