from datetime import date
from typing import Any

import pytest
from django.utils import timezone

from apps.accounts import codes, conf, registration
from apps.accounts.models import PendingRegistration, PhantomProcess
from apps.accounts.tests.factories import make_user
from apps.core import fingerprints
from apps.emails.models import OutboundEmail

pytestmark = pytest.mark.django_db

PURPOSE = codes.Purpose.REGISTRATION
PAYLOAD = {"name": "Ana García", "birthdate": "1990-05-10", "country": "ES", "language": "pt-BR"}


def _slot(public_id: str = "slot_1", email: str = "ana@x.com", **payload: Any) -> PhantomProcess:
    slot = PhantomProcess(
        purpose=PURPOSE,
        email=email,
        public_id=public_id,
        code_hash="",
        code_expires_at=timezone.now() + conf.code_ttl(),
        payload={**PAYLOAD, **payload},
    )
    slot.save()
    return slot


def _code_of(email: OutboundEmail) -> str:
    assert email.masked_code is not None
    return fingerprints.unmask_code(email.masked_code, email.code_nonce)


def _pending(email: str = "ana@x.com", **fields: Any) -> PendingRegistration:
    pending = PendingRegistration(
        email=email,
        name="Eva Previa",
        birthdate=date(1980, 1, 1),
        country="PT",
        language="en",
        public_id="old_id",
        code_hash="h",
        code_expires_at=timezone.now() + conf.code_ttl(),
        **fields,
    )
    pending.save()
    return pending


def test_a_new_email_becomes_a_pending_registration_with_the_slot_id() -> None:
    _slot()

    registration.resolve_registration("slot_1")

    pending = PendingRegistration.objects.get()
    assert (pending.public_id, pending.email, pending.name, pending.country, pending.language) == (
        "slot_1",
        "ana@x.com",
        "Ana García",
        "ES",
        "pt-BR",
    )
    assert pending.birthdate == date(1990, 5, 10)
    assert not PhantomProcess.objects.exists()
    [email] = OutboundEmail.objects.all()
    assert (email.kind, email.recipient, email.locale, email.public_id, email.purpose) == (
        "registration_code",
        "ana@x.com",
        "pt-BR",
        "slot_1",
        "registration",
    )
    assert email.context == {"name": "Ana García"}
    assert fingerprints.code_matches(PURPOSE, "slot_1", _code_of(email), pending.code_hash)


def test_a_repeated_registration_keeps_the_data_and_takes_the_slot_id() -> None:
    pending = _pending(failed_attempts=3, code_validated_at=timezone.now())
    _slot()

    registration.resolve_registration("slot_1")

    pending.refresh_from_db()
    assert (pending.public_id, pending.name, pending.language) == ("slot_1", "Eva Previa", "en")
    assert (pending.failed_attempts, pending.code_validated_at) == (0, None)
    assert not PhantomProcess.objects.exists()
    [email] = OutboundEmail.objects.all()
    assert (email.recipient, email.locale, email.context) == (
        "ana@x.com",
        "pt-BR",
        {"name": "Eva Previa"},
    )
    assert fingerprints.code_matches(PURPOSE, "slot_1", _code_of(email), pending.code_hash)


def test_an_active_account_keeps_the_slot_and_gets_the_account_exists_notice() -> None:
    account = make_user(email="ana@x.com", name="Ana Titular", language="en")
    _slot(email="ANA@x.com")

    registration.resolve_registration("slot_1")

    slot = PhantomProcess.objects.get(public_id="slot_1")
    assert slot.payload is None
    assert not PendingRegistration.objects.exists()
    [email] = OutboundEmail.objects.all()
    assert (email.kind, email.recipient, email.locale, email.context) == (
        "account_exists",
        account.email,
        "en",
        {"name": "Ana Titular"},
    )
    assert email.masked_code is None


def test_an_inactive_account_keeps_the_slot_without_any_email() -> None:
    make_user(email="ana@x.com", is_active=False)
    _slot()

    registration.resolve_registration("slot_1")

    assert PhantomProcess.objects.get(public_id="slot_1").payload is None
    assert not OutboundEmail.objects.exists()


def test_expired_registrations_and_older_slots_of_the_email_are_removed_first() -> None:
    old = _pending()
    PendingRegistration.objects.filter(pk=old.pk).update(
        created_at=timezone.now() - conf.max_lifetime()
    )
    older = _slot("slot_0")
    PhantomProcess.objects.filter(pk=older.pk).update(payload=None)
    other_email = _slot("slot_x", email="otra@x.com")
    _slot()

    registration.resolve_registration("slot_1")

    assert set(PhantomProcess.objects.values_list("public_id", flat=True)) == {
        other_email.public_id
    }
    assert list(PendingRegistration.objects.values_list("public_id", flat=True)) == ["slot_1"]


@pytest.mark.parametrize("public_id", ["slot_1", "unknown"])
def test_a_resolved_or_unknown_slot_is_left_alone(public_id: str) -> None:
    slot = _slot()
    PhantomProcess.objects.filter(pk=slot.pk).update(payload=None)

    registration.resolve_registration(public_id)

    assert PhantomProcess.objects.filter(public_id="slot_1").exists()
    assert not PendingRegistration.objects.exists()
    assert not OutboundEmail.objects.exists()


def test_a_unique_email_collision_is_treated_as_a_repeated_registration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending = _pending()
    _slot()
    real_filter = PendingRegistration.objects.filter
    calls = {"n": 0}

    def hide_existing_once(*args: Any, **kwargs: Any) -> Any:
        # La primera búsqueda del registro vigente no lo ve, como si otro proceso lo creara justo
        # después; el alta choca con la unicidad del correo.
        if "email__iexact" in kwargs and calls["n"] == 0 and not args:
            calls["n"] += 1
            return real_filter(pk=-1)
        return real_filter(*args, **kwargs)

    monkeypatch.setattr(PendingRegistration.objects, "filter", hide_existing_once)

    registration.resolve_registration("slot_1")

    pending.refresh_from_db()
    assert pending.public_id == "slot_1"
    assert OutboundEmail.objects.count() == 1
