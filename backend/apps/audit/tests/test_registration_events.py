from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone

from apps.accounts import registration, signals
from apps.accounts.models import PendingRegistration
from apps.accounts.processes import VerifyResult
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
    started = registration.start(
        email=EMAIL, name="Ana García", birthdate=date(1990, 1, 1), country="ES"
    )
    assert isinstance(started, registration.Started)
    PendingRegistration.objects.update(code_expires_at=timezone.now() - timedelta(minutes=1))

    result = registration.verify(public_id=started.public_id, code=started.code)

    assert result is VerifyResult.CODE_EXPIRED
    event = SecurityEvent.objects.get(event_type=EventType.CODE_VERIFIED)
    assert event.success is False
    assert event.user_email_hash == audit_email_fingerprint(EMAIL)
