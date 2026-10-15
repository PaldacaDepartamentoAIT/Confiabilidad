from datetime import timedelta
from typing import Any

import pytest
from django.utils import timezone

from apps.accounts import codes, conf, password_reset
from apps.accounts.models import PasswordResetRequest, PhantomProcess, User
from apps.accounts.tests.factories import make_user
from apps.core import fingerprints
from apps.emails.models import OutboundEmail

pytestmark = pytest.mark.django_db

PURPOSE = codes.Purpose.PASSWORD_RESET


def _slot(
    public_id: str = "slot_1",
    email: str = "eva@x.com",
    purpose: str = "password_reset",
    **payload: Any,
) -> PhantomProcess:
    slot = PhantomProcess(
        purpose=purpose,
        email=email,
        public_id=public_id,
        code_hash="",
        code_expires_at=timezone.now() + conf.code_ttl(),
        payload={"language": "pt-BR", **payload},
    )
    slot.save()
    return slot


def _code_of(email: OutboundEmail) -> str:
    assert email.masked_code is not None
    return fingerprints.unmask_code(email.masked_code, email.code_nonce)


def _old_request(user: User) -> PasswordResetRequest:
    request = PasswordResetRequest(
        user=user,
        public_id="old_id",
        code_hash="h",
        code_expires_at=timezone.now() + conf.code_ttl(),
        account_stamp="stale",
        failed_attempts=3,
        code_validated_at=timezone.now(),
    )
    request.save()
    PasswordResetRequest.objects.update(created_at=timezone.now() - timedelta(minutes=30))
    return request


def test_an_active_account_gets_a_request_with_the_slot_id_and_the_code_email() -> None:
    user = make_user(email="eva@x.com", name="Eva Titular", language="en")
    _slot(email="EVA@x.com")

    password_reset.resolve_password_reset("slot_1")

    request = PasswordResetRequest.objects.get()
    assert (request.user, request.public_id, request.failed_attempts) == (user, "slot_1", 0)
    assert request.code_validated_at is None
    assert fingerprints.account_stamp_matches(request.account_stamp, user.email, user.password)
    assert not PhantomProcess.objects.exists()
    [email] = OutboundEmail.objects.all()
    assert (email.kind, email.recipient, email.locale, email.public_id, email.purpose) == (
        "password_reset_code",
        "eva@x.com",
        "pt-BR",
        "slot_1",
        "password_reset",
    )
    assert email.context == {"name": "Eva Titular"}
    assert fingerprints.code_matches(PURPOSE, "slot_1", _code_of(email), request.code_hash)


def test_a_previous_request_is_replaced_with_a_new_life_and_stamp() -> None:
    user = make_user(email="eva@x.com")
    old = _old_request(user)
    _slot()

    password_reset.resolve_password_reset("slot_1")

    request = PasswordResetRequest.objects.get()
    assert request.pk == old.pk
    assert (request.public_id, request.failed_attempts, request.code_validated_at) == (
        "slot_1",
        0,
        None,
    )
    assert request.created_at > timezone.now() - timedelta(minutes=1)
    assert fingerprints.account_stamp_matches(request.account_stamp, user.email, user.password)
    [email] = OutboundEmail.objects.all()
    assert fingerprints.code_matches(PURPOSE, "slot_1", _code_of(email), request.code_hash)


@pytest.mark.parametrize("has_account", [False, True], ids=["no-account", "inactive-account"])
def test_without_an_eligible_account_the_slot_stays_without_any_email(has_account: bool) -> None:
    if has_account:
        user = make_user(email="eva@x.com", is_active=False)
        _old_request(user)
    _slot()

    password_reset.resolve_password_reset("slot_1")

    assert PhantomProcess.objects.get(public_id="slot_1").payload is None
    assert not OutboundEmail.objects.exists()
    assert list(PasswordResetRequest.objects.values_list("public_id", flat=True)) == (
        ["old_id"] if has_account else []
    )


def test_older_slots_of_the_same_email_are_removed_first() -> None:
    _slot("older", email="eva@x.com")
    _slot("other_email", email="bea@x.com")
    _slot("registration_slot", email="eva@x.com", purpose="registration")
    _slot()

    password_reset.resolve_password_reset("slot_1")

    assert set(PhantomProcess.objects.values_list("public_id", flat=True)) == {
        "slot_1",
        "other_email",
        "registration_slot",
    }


@pytest.mark.parametrize("public_id", ["resolved", "unknown", "registration_slot"])
def test_a_resolved_unknown_or_foreign_slot_is_left_alone(public_id: str) -> None:
    make_user(email="eva@x.com")
    resolved = _slot("resolved")
    PhantomProcess.objects.filter(pk=resolved.pk).update(payload=None)
    _slot("registration_slot", purpose="registration")

    password_reset.resolve_password_reset(public_id)

    assert not PasswordResetRequest.objects.exists()
    assert not OutboundEmail.objects.exists()
    assert PhantomProcess.objects.count() == 2


def test_an_unsupported_language_falls_back_to_the_default() -> None:
    make_user(email="eva@x.com")
    _slot(language="fr")

    password_reset.resolve_password_reset("slot_1")

    assert OutboundEmail.objects.get().locale == "es"
