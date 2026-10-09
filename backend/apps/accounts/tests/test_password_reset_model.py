from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import PasswordResetRequest, User
from apps.accounts.tests.factories import make_user

pytestmark = pytest.mark.django_db


def _request(user: User, public_id: str = "pid-1") -> PasswordResetRequest:
    return PasswordResetRequest(
        user=user,
        public_id=public_id,
        code_hash="a" * 64,
        code_expires_at=timezone.now() + timedelta(minutes=15),
        account_stamp="b" * 64,
    )


def test_all_fields_are_stored() -> None:
    user = make_user()
    expires = timezone.now() + timedelta(minutes=15)
    request = _request(user)
    request.code_expires_at = expires
    request.save()

    stored = PasswordResetRequest.objects.get(pk=request.pk)
    assert (stored.user, stored.public_id, stored.code_hash, stored.account_stamp) == (
        user,
        "pid-1",
        "a" * 64,
        "b" * 64,
    )
    assert stored.code_expires_at == expires
    assert (stored.failed_attempts, stored.code_validated_at) == (0, None)
    assert stored.created_at is not None
    assert user.password_reset_request == stored


def test_one_request_per_account_even_in_bulk_create() -> None:
    user = make_user()
    _request(user).save()

    with pytest.raises(IntegrityError), transaction.atomic():
        PasswordResetRequest.objects.bulk_create([_request(user, public_id="pid-2")])


def test_public_id_is_unique() -> None:
    _request(make_user()).save()

    with pytest.raises(IntegrityError), transaction.atomic():
        PasswordResetRequest.objects.bulk_create([_request(make_user())])


def test_deleting_the_account_deletes_its_request() -> None:
    user = make_user()
    _request(user).save()
    other = make_user()
    _request(other, public_id="pid-2").save()

    user.delete()

    assert list(PasswordResetRequest.objects.values_list("public_id", flat=True)) == ["pid-2"]


def _expired_ids() -> set[str]:
    return set(PasswordResetRequest.objects.expired().values_list("public_id", flat=True))


def test_expired_requests_by_grace_or_lifetime() -> None:
    now = timezone.now()
    for public_id in ("alive", "grace", "lifetime"):
        _request(make_user(), public_id=public_id).save()
    PasswordResetRequest.objects.filter(public_id="grace").update(
        code_expires_at=now - timedelta(minutes=16)
    )
    PasswordResetRequest.objects.filter(public_id="lifetime").update(
        created_at=now - timedelta(minutes=61)
    )

    assert _expired_ids() == {"grace", "lifetime"}
    assert PasswordResetRequest.objects.get(public_id="grace").is_expired
    assert not PasswordResetRequest.objects.get(public_id="alive").is_expired


def test_str_is_the_account_email() -> None:
    assert str(_request(make_user(email="ana@x.com"))) == "ana@x.com"
