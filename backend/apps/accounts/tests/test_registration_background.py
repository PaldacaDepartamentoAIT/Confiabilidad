from datetime import date, timedelta
from typing import Any
from unittest import mock

import pytest
from celery.exceptions import Retry
from django.conf import settings
from django.test import override_settings
from django.utils import timezone

from apps.accounts import codes, conf, registration, tasks
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


@pytest.fixture
def send_task() -> Any:
    with mock.patch("celery.current_app.send_task") as patched:
        yield patched


def _age(slot: PhantomProcess, minutes: int) -> None:
    PhantomProcess.objects.filter(pk=slot.pk).update(
        created_at=timezone.now() - timedelta(minutes=minutes)
    )


@pytest.mark.parametrize("has_account", [False, True])
def test_an_older_slot_resolved_before_a_newer_one_does_nothing(has_account: bool) -> None:
    if has_account:
        make_user(email="ana@x.com")
    _slot("older")
    _slot("newer")

    registration.resolve_registration("older")

    assert list(PhantomProcess.objects.values_list("public_id", flat=True)) == ["newer"]
    assert not PendingRegistration.objects.exists()
    assert not OutboundEmail.objects.exists()


def test_only_older_slots_of_the_email_are_removed() -> None:
    _slot("older")
    resolved_later = _slot("resolved_later")
    _slot("current")
    PhantomProcess.objects.filter(pk=resolved_later.pk).update(payload=None)
    newer_resolved = _slot("newer_resolved")
    PhantomProcess.objects.filter(pk=newer_resolved.pk).update(payload=None)

    registration.resolve_registration("current")

    assert list(PhantomProcess.objects.values_list("public_id", flat=True)) == ["newer_resolved"]
    assert PendingRegistration.objects.get().public_id == "current"


def test_the_task_resolves_the_slot() -> None:
    _slot()

    result = tasks.resolve_registration.apply(args=["slot_1"])

    assert result.successful()
    assert PendingRegistration.objects.filter(public_id="slot_1").exists()


@pytest.fixture
def retry(monkeypatch: pytest.MonkeyPatch) -> mock.Mock:
    # En `apply()` Celery reintenta al momento; aquí basta con saber que pide el reintento.
    patched = mock.Mock(side_effect=Retry())
    monkeypatch.setattr(tasks.resolve_registration, "retry", patched)
    return patched


def test_a_failure_within_the_window_is_retried(
    monkeypatch: pytest.MonkeyPatch, retry: mock.Mock
) -> None:
    _slot()
    monkeypatch.setattr(registration, "resolve_registration", mock.Mock(side_effect=OSError("db")))

    result = tasks.resolve_registration.apply(args=["slot_1"])

    assert result.state == "RETRY"
    assert retry.call_args.kwargs["countdown"] == 15
    assert PhantomProcess.objects.get(public_id="slot_1").payload is not None


def test_a_failure_after_the_window_leaves_a_phantom_and_logs_it(
    monkeypatch: pytest.MonkeyPatch, caplog: Any
) -> None:
    slot = _slot()
    _age(slot, 6)
    monkeypatch.setattr(registration, "resolve_registration", mock.Mock(side_effect=OSError("db")))

    result = tasks.resolve_registration.apply(args=["slot_1"])

    assert result.successful()
    assert PhantomProcess.objects.get(public_id="slot_1").payload is None
    assert "slot_1" not in caplog.text
    assert "gave up" in caplog.text


@pytest.mark.parametrize("retries", [0, 2], ids=["first-attempt", "retry"])
def test_an_execution_after_the_window_does_not_resolve_and_logs_it(
    retries: int, caplog: Any
) -> None:
    slot = _slot()
    _age(slot, 6)

    result = tasks.resolve_registration.apply(args=["slot_1"], retries=retries)

    assert result.successful()
    assert not PendingRegistration.objects.exists()
    assert not OutboundEmail.objects.exists()
    assert PhantomProcess.objects.get(public_id="slot_1").payload is None
    assert "gave up" in caplog.text


def test_a_failure_when_the_window_ends_during_the_attempt_gives_up(
    monkeypatch: pytest.MonkeyPatch, caplog: Any
) -> None:
    slot = _slot()

    def fail_late(public_id: str) -> None:
        _age(slot, 6)
        raise OSError("db")

    monkeypatch.setattr(registration, "resolve_registration", fail_late)

    assert tasks.resolve_registration.apply(args=["slot_1"]).successful()
    assert PhantomProcess.objects.get(public_id="slot_1").payload is None
    assert "gave up: OSError('db')" in caplog.text


def test_an_execution_within_the_window_still_resolves() -> None:
    slot = _slot()
    _age(slot, 4)

    tasks.resolve_registration.apply(args=["slot_1"])

    assert PendingRegistration.objects.filter(public_id="slot_1").exists()


@pytest.mark.parametrize("public_id", ["unknown", "resolved"])
def test_an_execution_for_a_missing_or_resolved_slot_does_nothing(
    public_id: str, caplog: Any
) -> None:
    slot = _slot("resolved")
    PhantomProcess.objects.filter(pk=slot.pk).update(payload=None)
    _age(slot, 6)

    assert tasks.resolve_registration.apply(args=[public_id]).successful()

    assert "gave up" not in caplog.text
    assert not OutboundEmail.objects.exists()


def test_the_resolution_tasks_retry_with_no_limit_but_the_window() -> None:
    assert tasks.resolve_registration.max_retries is None
    assert tasks.resolve_password_reset.max_retries is None


@override_settings(REGISTRATION_START_RETRY_MINUTES=10)
def test_the_window_follows_the_settings(monkeypatch: pytest.MonkeyPatch, retry: mock.Mock) -> None:
    slot = _slot()
    _age(slot, 6)
    monkeypatch.setattr(registration, "resolve_registration", mock.Mock(side_effect=OSError("db")))

    assert tasks.resolve_registration.apply(args=["slot_1"]).state == "RETRY"


def test_the_sweep_queues_unresolved_slots_within_the_window_and_gives_up_on_the_rest(
    send_task: Any,
) -> None:
    _slot("fresh")
    stale = _slot("stale", email="vieja@x.com")
    _age(stale, 6)
    resolved = _slot("done", email="hecha@x.com")
    PhantomProcess.objects.filter(pk=resolved.pk).update(payload=None)

    queued = tasks.sweep_unresolved()

    assert queued == 1
    send_task.assert_called_once_with("apps.accounts.tasks.resolve_registration", args=["fresh"])
    assert PhantomProcess.objects.get(public_id="stale").payload is None


def test_the_sweep_runs_every_minute() -> None:
    entries = [
        entry
        for entry in settings.CELERY_BEAT_SCHEDULE.values()
        if entry["task"] == "apps.accounts.tasks.sweep_unresolved"
    ]

    assert [entry["schedule"] for entry in entries] == [60.0]
