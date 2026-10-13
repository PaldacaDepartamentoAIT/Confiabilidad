from collections.abc import Callable
from typing import Any

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from apps.accounts import signals
from apps.audit.middleware import CurrentRequestMiddleware
from apps.audit.models import EventType, SecurityEvent

pytestmark = pytest.mark.django_db

EMAIL = "ana@x.com"


@pytest.fixture
def audit_key(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = "test-audit-key"  # type: ignore[attr-defined]


def _inside_request(send: Callable[[], object]) -> None:
    request = RequestFactory().post("/", REMOTE_ADDR="203.0.113.7")

    def get_response(_request: Any) -> HttpResponse:
        send()
        return HttpResponse()

    CurrentRequestMiddleware(get_response)(request)


@pytest.mark.parametrize(
    ("signal_name", "event_type"),
    [
        ("profile_edited", EventType.PROFILE_EDIT),
        ("account_disabled", EventType.ACCOUNT_DISABLE),
    ],
)
def test_profile_signals_record_their_event_type(
    audit_key: None, signal_name: str, event_type: str
) -> None:
    signal = getattr(signals, signal_name)
    _inside_request(lambda: signal.send(sender=object, email=EMAIL, success=True))
    event = SecurityEvent.objects.get(event_type=event_type)
    assert event.success is True
    assert event.ip == "203.0.113.7"
