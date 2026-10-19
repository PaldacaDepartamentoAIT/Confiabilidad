import pytest
from django.test import RequestFactory

from apps.audit.models import EventType, SecurityEvent
from apps.audit.recorder import record_event
from apps.core.fingerprints import audit_email_fingerprint, audit_session_fingerprint

pytestmark = pytest.mark.django_db


@pytest.fixture
def audit_key(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = "test-audit-key"  # type: ignore[attr-defined]


def _request(remote_addr: str = "203.0.113.7", user_agent: str = "pytest-agent"):  # type: ignore[no-untyped-def]
    return RequestFactory().get("/", REMOTE_ADDR=remote_addr, HTTP_USER_AGENT=user_agent)


def test_record_event_stores_ip_user_agent_and_success(audit_key: None) -> None:
    event = record_event(EventType.LOGIN, success=True, request=_request())
    event.refresh_from_db()
    assert event.ip == "203.0.113.7"
    assert event.user_agent == "pytest-agent"
    assert event.success is True
    assert event.event_type == EventType.LOGIN


def test_email_is_stored_only_as_normalized_fingerprint(audit_key: None) -> None:
    event = record_event(EventType.LOGIN, success=False, request=_request(), email=" Ana@X.com ")
    event.refresh_from_db()
    assert event.user_email_hash == audit_email_fingerprint("ana@x.com")
    stored = " ".join(
        str(value) for value in (event.user_agent, event.user_email_hash, event.metadata)
    )
    assert "ana@x.com" not in stored.lower()


def test_session_key_is_stored_only_as_fingerprint(audit_key: None) -> None:
    event = record_event(EventType.LOGOUT, success=True, request=_request(), session_key="sess-123")
    event.refresh_from_db()
    assert event.session_key == audit_session_fingerprint("sess-123")
    assert event.session_key != "sess-123"


def test_missing_session_and_email_are_stored_empty(audit_key: None) -> None:
    event = record_event(EventType.LOGIN, success=False, request=_request())
    event.refresh_from_db()
    assert event.session_key == ""
    assert event.user_email_hash == ""


def test_metadata_is_stored(audit_key: None) -> None:
    event = record_event(
        EventType.LOGIN, success=False, request=_request(), metadata={"reason": "bad_password"}
    )
    event.refresh_from_db()
    assert event.metadata == {"reason": "bad_password"}


def test_without_request_ip_is_empty(audit_key: None) -> None:
    event = record_event(EventType.CODE_SENT, success=True)
    event.refresh_from_db()
    assert event.ip is None
    assert SecurityEvent.objects.filter(pk=event.pk).exists()
