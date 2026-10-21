from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from apps.accounts import codes, conf, processes
from apps.accounts.models import CodeProcess, PhantomProcess

pytestmark = pytest.mark.django_db

PURPOSE = codes.Purpose.REGISTRATION


def _phantom(**fields: object) -> PhantomProcess:
    values: dict[str, object] = {
        "purpose": PURPOSE,
        "email": " Ana@Example.COM ",
        "public_id": "ph_1",
        "code_hash": "",
        "code_expires_at": timezone.now() + conf.code_ttl(),
    }
    values.update(fields)
    phantom = PhantomProcess(**values)
    phantom.save()
    return phantom


def test_a_phantom_is_a_code_process_with_purpose_email_and_payload() -> None:
    phantom = _phantom(payload={"name": "Ana"})

    stored = PhantomProcess.objects.get(pk=phantom.pk)
    assert isinstance(stored, CodeProcess)
    assert (stored.purpose, stored.email, stored.payload) == (
        PURPOSE,
        "ana@example.com",
        {"name": "Ana"},
    )
    assert stored.failed_attempts == 0
    assert stored.code_validated_at is None
    assert _phantom(public_id="ph_2", email="b@example.com").payload is None


def test_only_the_two_process_purposes_are_accepted() -> None:
    with pytest.raises(ValidationError) as error:
        _phantom(purpose="newsletter")

    assert "purpose" in error.value.error_dict
    assert {value for value, _ in PhantomProcess.Purpose.choices} == {
        "registration",
        "password_reset",
    }


def test_the_public_id_is_unique_in_the_database() -> None:
    _phantom()

    with pytest.raises(IntegrityError), transaction.atomic():
        PhantomProcess.objects.bulk_create(
            [
                PhantomProcess(
                    purpose=PURPOSE,
                    email="otra@example.com",
                    public_id="ph_1",
                    code_hash="",
                    code_expires_at=timezone.now(),
                )
            ]
        )


@pytest.mark.parametrize("code", ["000000", "123456", "999999"])
def test_a_phantom_never_accepts_a_code(code: str) -> None:
    phantom = _phantom()

    assert processes.check_code(phantom, PURPOSE, code) is processes.VerifyResult.WRONG_CODE
    assert phantom.failed_attempts == 1


def test_a_phantom_locks_and_expires_like_any_process() -> None:
    phantom = _phantom()
    for _ in range(conf.max_failed_attempts()):
        processes.check_code(phantom, PURPOSE, "123456")

    assert processes.check_code(phantom, PURPOSE, "123456") is processes.VerifyResult.LOCKED

    PhantomProcess.objects.filter(pk=phantom.pk).update(
        failed_attempts=0, code_expires_at=timezone.now() - timedelta(seconds=1)
    )
    phantom.refresh_from_db()
    assert processes.check_code(phantom, PURPOSE, "123456") is processes.VerifyResult.CODE_EXPIRED

    PhantomProcess.objects.filter(pk=phantom.pk).update(
        created_at=timezone.now() - conf.max_lifetime()
    )
    phantom.refresh_from_db()
    assert phantom.is_expired
    assert PhantomProcess.objects.expired().filter(pk=phantom.pk).exists()


def test_a_phantom_reads_as_its_purpose_and_public_id() -> None:
    assert str(_phantom()) == "registration:ph_1"


def test_a_slot_has_no_resolution_time_until_it_is_resolved() -> None:
    slot = _phantom()

    assert PhantomProcess.objects.get(pk=slot.pk).resolved_at is None
    now = timezone.now()
    PhantomProcess.objects.filter(pk=slot.pk).update(resolved_at=now)
    assert PhantomProcess.objects.get(pk=slot.pk).resolved_at == now


@pytest.mark.django_db(transaction=True)
def test_existing_slots_have_no_resolution_time_after_migrating() -> None:
    before = [("accounts", "0010_passwordresetrequest_language")]
    after = [("accounts", "0011_phantomprocess_resolved_at")]
    _phantom()
    MigrationExecutor(connection).migrate(before)
    try:
        executor = MigrationExecutor(connection)
        executor.migrate(after)
        model = executor.loader.project_state(after).apps.get_model("accounts", "PhantomProcess")
        assert list(model.objects.values_list("resolved_at", flat=True)) == [None]
    finally:
        MigrationExecutor(connection).migrate(
            MigrationExecutor(connection).loader.graph.leaf_nodes()
        )
