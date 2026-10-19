from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone

from apps.accounts import conf, registration, signals
from apps.accounts.models import PendingRegistration
from apps.accounts.processes import VerifyResult
from apps.accounts.tests.factories import (
    StartedWithCode,
    make_pending,
    make_user,
)
from apps.audit.middleware import CurrentRequestMiddleware, current_request
from apps.audit.models import EventType, SecurityEvent
from apps.core.fingerprints import audit_email_fingerprint

pytestmark = pytest.mark.django_db

EMAIL = "ana@x.com"


@pytest.fixture
def audit_key(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = "test-audit-key"  # type: ignore[attr-defined]


def _inside_request(send: Callable[[], object], remote_addr: str = "203.0.113.7") -> None:
    request = RequestFactory().post("/", REMOTE_ADDR=remote_addr, HTTP_USER_AGENT="pytest-agent")

    def get_response(_request: Any) -> HttpResponse:
        send()
        return HttpResponse()

    CurrentRequestMiddleware(get_response)(request)


def test_middleware_exposes_current_request_only_during_the_request() -> None:
    seen: list[object] = []
    request = RequestFactory().get("/")

    def get_response(_request: Any) -> HttpResponse:
        seen.append(current_request())
        return HttpResponse()

    CurrentRequestMiddleware(get_response)(request)
    assert seen == [request]
    assert current_request() is None


def test_pending_request_event_is_recorded_with_ip(audit_key: None) -> None:
    _inside_request(
        lambda: signals.pending_registration_requested.send(
            sender=object, email=EMAIL, success=True
        )
    )
    event = SecurityEvent.objects.get(event_type=EventType.PENDING_REGISTRATION)
    assert event.success is True
    assert event.ip == "203.0.113.7"
    assert event.user_email_hash == audit_email_fingerprint(EMAIL)


@pytest.mark.parametrize(
    ("signal_name", "event_type"),
    [
        ("registration_code_sent", EventType.CODE_SENT),
        ("registration_code_verified", EventType.CODE_VERIFIED),
        ("account_created", EventType.ACCOUNT_REGISTRATION),
    ],
)
def test_registration_signals_map_to_their_event_type(
    audit_key: None, signal_name: str, event_type: str
) -> None:
    signal = getattr(signals, signal_name)
    _inside_request(lambda: signal.send(sender=object, email=EMAIL, success=False))
    event = SecurityEvent.objects.get(event_type=event_type)
    assert event.success is False
    assert event.ip == "203.0.113.7"


def test_code_expired_within_grace_is_recorded_as_failed_verification(audit_key: None) -> None:
    started = make_pending(EMAIL, name="Ana García", birthdate=date(1990, 1, 1), country="ES")
    PendingRegistration.objects.update(code_expires_at=timezone.now() - timedelta(minutes=1))

    result = registration.verify(public_id=started.public_id, code=started.code)

    assert result is VerifyResult.CODE_EXPIRED
    event = SecurityEvent.objects.get(event_type=EventType.CODE_VERIFIED)
    assert event.success is False
    assert event.user_email_hash == audit_email_fingerprint(EMAIL)


def _started_registration() -> StartedWithCode:
    started = make_pending(EMAIL, name="Ana García", birthdate=date(1990, 1, 1), country="ES")
    return started


def _wrong(code: str) -> str:
    return "1" * len(code) if code == "0" * len(code) else "0" * len(code)


def _verifications() -> list[bool]:
    return list(
        SecurityEvent.objects.filter(event_type=EventType.CODE_VERIFIED)
        .order_by("id")
        .values_list("success", flat=True)
    )


def test_locked_code_is_recorded_as_failed_verification(audit_key: None) -> None:
    started = _started_registration()
    limit = conf.max_failed_attempts()
    for _ in range(limit):
        registration.verify(public_id=started.public_id, code=_wrong(started.code))

    result = registration.verify(public_id=started.public_id, code=started.code)

    assert result is VerifyResult.LOCKED
    assert _verifications() == [False] * (limit + 1)


def test_already_verified_code_is_recorded_as_failed_verification(audit_key: None) -> None:
    started = _started_registration()
    registration.verify(public_id=started.public_id, code=started.code)

    result = registration.verify(public_id=started.public_id, code=started.code)

    assert result is VerifyResult.ALREADY_VERIFIED
    assert _verifications() == [True, False]


def test_unknown_registration_leaves_no_verification_row(audit_key: None) -> None:
    result = registration.verify(public_id="unknown", code="000000")

    assert result is VerifyResult.NOT_FOUND
    assert _verifications() == []


def _verified_registration() -> StartedWithCode:
    started = _started_registration()
    assert registration.verify(public_id=started.public_id, code=started.code) is (
        VerifyResult.VERIFIED
    )
    return started


def _registrations() -> int:
    return SecurityEvent.objects.filter(event_type=EventType.ACCOUNT_REGISTRATION).count()


def test_complete_refused_for_existing_account_leaves_no_registration_row(audit_key: None) -> None:
    started = _verified_registration()
    make_user(email=EMAIL, name="Ana García")

    result = registration.complete(public_id=started.public_id, password="Kq7#mZ2!vR9p")

    assert result is registration.CompleteRefusal.ACCOUNT_EXISTS
    assert _registrations() == 0


def test_complete_refused_for_expired_process_leaves_no_registration_row(audit_key: None) -> None:
    started = _verified_registration()
    PendingRegistration.objects.update(code_expires_at=timezone.now() - timedelta(hours=1))

    result = registration.complete(public_id=started.public_id, password="Kq7#mZ2!vR9p")

    assert result is registration.CompleteRefusal.EXPIRED
    assert _registrations() == 0


def test_complete_refused_for_weak_password_leaves_no_registration_row(audit_key: None) -> None:
    started = _verified_registration()

    with pytest.raises(ValidationError):
        registration.complete(public_id=started.public_id, password="12345678")

    assert _registrations() == 0
