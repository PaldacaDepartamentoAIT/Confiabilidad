from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from apps.accounts.models import PasswordResetRequest, PhantomProcess, User
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


def test_the_request_language_defaults_to_spanish_and_admits_the_three_languages() -> None:
    request = _request(make_user())
    request.save()

    assert PasswordResetRequest.objects.get(pk=request.pk).language == "es"
    for language in ("es", "pt-BR", "en"):
        request.language = language
        request.full_clean()
    request.language = "fr"
    with pytest.raises(ValidationError):
        request.full_clean()


@pytest.mark.django_db(transaction=True)
def test_existing_requests_get_spanish_when_migrating() -> None:
    before, after = [("accounts", "0009_phantom_answers_expired")], [
        ("accounts", "0010_passwordresetrequest_language")
    ]
    _request(make_user()).save()
    executor = MigrationExecutor(connection)
    executor.migrate(before)
    try:
        executor = MigrationExecutor(connection)
        executor.migrate(after)
        old_model = executor.loader.project_state(after).apps.get_model(
            "accounts", "PasswordResetRequest"
        )
        assert list(old_model.objects.values_list("language", flat=True)) == ["es"]
    finally:
        MigrationExecutor(connection).migrate(
            MigrationExecutor(connection).loader.graph.leaf_nodes()
        )


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


def test_deleting_the_account_leaves_a_tombstone_that_answers_expired() -> None:
    user = make_user()
    request = _request(user)
    request.save()
    PasswordResetRequest.objects.update(created_at=timezone.now() - timedelta(minutes=20))
    request.refresh_from_db()

    user.delete()

    tombstone = PhantomProcess.objects.get()
    assert (tombstone.purpose, tombstone.public_id, tombstone.answers_expired) == (
        "password_reset",
        "pid-1",
        True,
    )
    assert (tombstone.code_expires_at, tombstone.created_at) == (
        request.code_expires_at,
        request.created_at,
    )
    assert (tombstone.email, tombstone.code_hash, tombstone.payload) == ("", "", None)
    assert not PasswordResetRequest.objects.exists()


def test_a_bulk_delete_leaves_a_tombstone_per_request() -> None:
    _request(make_user(email="a@x.com")).save()
    _request(make_user(email="b@x.com"), public_id="pid-2").save()
    make_user(email="c@x.com")

    User.objects.all().delete()

    assert set(PhantomProcess.objects.values_list("public_id", flat=True)) == {"pid-1", "pid-2"}
    assert PhantomProcess.objects.filter(answers_expired=True).count() == 2


def test_an_account_without_request_leaves_no_tombstone() -> None:
    make_user().delete()

    assert not PhantomProcess.objects.exists()


def test_a_slot_does_not_answer_expired_by_default() -> None:
    slot = PhantomProcess.objects.create(
        purpose="password_reset",
        email="ana@x.com",
        public_id="pid-9",
        code_hash="",
        code_expires_at=timezone.now(),
    )

    assert PhantomProcess.objects.get(pk=slot.pk).answers_expired is False


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
