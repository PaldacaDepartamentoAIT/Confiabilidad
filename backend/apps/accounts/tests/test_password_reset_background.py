from collections.abc import Iterator
from datetime import timedelta
from typing import Any
from unittest import mock

import pytest
from celery.exceptions import Retry
from django.test import override_settings
from django.utils import timezone

from apps.accounts import codes, conf, password_reset, tasks
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
    assert request.language == "pt-BR"
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
    _slot(language="en")

    password_reset.resolve_password_reset("slot_1")

    request = PasswordResetRequest.objects.get()
    assert (request.pk, request.language) == (old.pk, "en")
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


@pytest.mark.parametrize("has_account", [False, True])
def test_an_older_slot_resolved_before_a_newer_one_does_nothing(has_account: bool) -> None:
    if has_account:
        make_user(email="eva@x.com")
    _slot("older")
    _slot("newer")

    password_reset.resolve_password_reset("older")

    assert list(PhantomProcess.objects.values_list("public_id", flat=True)) == ["newer"]
    assert not PasswordResetRequest.objects.exists()
    assert not OutboundEmail.objects.exists()


def test_only_older_slots_of_the_email_are_removed() -> None:
    make_user(email="eva@x.com")
    _slot("older")
    _slot("current")
    newer_resolved = _slot("newer_resolved")
    PhantomProcess.objects.filter(pk=newer_resolved.pk).update(payload=None)

    password_reset.resolve_password_reset("current")

    assert list(PhantomProcess.objects.values_list("public_id", flat=True)) == ["newer_resolved"]
    assert PasswordResetRequest.objects.get().public_id == "current"


def test_an_unsupported_language_falls_back_to_the_default() -> None:
    make_user(email="eva@x.com")
    _slot(language="fr")

    password_reset.resolve_password_reset("slot_1")

    assert OutboundEmail.objects.get().locale == "es"
    assert PasswordResetRequest.objects.get().language == "es"


def _age(slot: PhantomProcess, minutes: int) -> None:
    PhantomProcess.objects.filter(pk=slot.pk).update(
        created_at=timezone.now() - timedelta(minutes=minutes)
    )


def _broken(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        password_reset, "resolve_password_reset", mock.Mock(side_effect=OSError("db"))
    )


def test_the_task_resolves_the_slot() -> None:
    make_user(email="eva@x.com")
    _slot()

    result = tasks.resolve_password_reset.apply(args=["slot_1"])

    assert result.successful()
    assert PasswordResetRequest.objects.filter(public_id="slot_1").exists()


def test_a_failure_within_the_window_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    # En `apply()` Celery reintenta al momento; aquí basta con saber que pide el reintento.
    retry = mock.Mock(side_effect=Retry())
    monkeypatch.setattr(tasks.resolve_password_reset, "retry", retry)
    slot = _slot()
    _age(slot, 4)
    _broken(monkeypatch)

    result = tasks.resolve_password_reset.apply(args=["slot_1"])

    assert result.state == "RETRY"
    assert retry.call_args.kwargs["countdown"] == 15
    assert PhantomProcess.objects.get(public_id="slot_1").payload is not None


def test_a_failure_after_the_window_leaves_the_slot_without_request_and_logs_it(
    monkeypatch: pytest.MonkeyPatch, caplog: Any
) -> None:
    slot = _slot()
    _age(slot, 6)
    _broken(monkeypatch)

    result = tasks.resolve_password_reset.apply(args=["slot_1"])

    assert result.successful()
    assert PhantomProcess.objects.get(public_id="slot_1").payload is None
    assert "gave up" in caplog.text


@pytest.fixture
def send_task() -> Iterator[mock.Mock]:
    with mock.patch("apps.accounts.tasks.current_app.send_task") as patched:
        yield patched


def test_the_sweep_also_queues_unresolved_password_reset_slots(send_task: mock.Mock) -> None:
    _slot("reset_slot")
    _slot("registration_slot", email="bea@x.com", purpose="registration", name="Bea")
    tombstone = _slot("tombstone", email="")
    PhantomProcess.objects.filter(pk=tombstone.pk).update(payload=None, answers_expired=True)

    assert tasks.sweep_unresolved() == 2

    assert sorted(call.args[0] for call in send_task.call_args_list) == [
        "apps.accounts.tasks.resolve_password_reset",
        "apps.accounts.tasks.resolve_registration",
    ]
    send_task.assert_any_call("apps.accounts.tasks.resolve_password_reset", args=["reset_slot"])


@override_settings(REGISTRATION_START_RETRY_MINUTES=10)
def test_the_shared_window_setting_also_rules_the_password_reset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    retry = mock.Mock(side_effect=Retry())
    monkeypatch.setattr(tasks.resolve_password_reset, "retry", retry)
    slot = _slot()
    _age(slot, 6)
    _broken(monkeypatch)

    assert tasks.resolve_password_reset.apply(args=["slot_1"]).state == "RETRY"


def test_an_execution_after_the_window_does_not_resolve(caplog: Any) -> None:
    make_user(email="eva@x.com")
    slot = _slot()
    _age(slot, 6)

    assert tasks.resolve_password_reset.apply(args=["slot_1"]).successful()

    assert not PasswordResetRequest.objects.exists()
    assert not OutboundEmail.objects.exists()
    assert PhantomProcess.objects.get(public_id="slot_1").payload is None
    assert "gave up" in caplog.text
