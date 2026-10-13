from datetime import timedelta
from typing import Any

import pytest
from django.utils import timezone

from apps.audit.models import EventType, SecurityEvent

pytestmark = pytest.mark.django_db


def test_event_types_are_exactly_the_eleven_from_rf_002() -> None:
    assert set(EventType.values) == {
        "account_registration",
        "pending_registration",
        "code_sent",
        "code_verified",
        "login",
        "lockout",
        "logout",
        "password_change",
        "password_reset",
        "profile_edit",
        "account_disable",
    }


def test_event_stores_rf_001_fields_without_user_reference() -> None:
    event = SecurityEvent.objects.create(
        event_type=EventType.LOGIN,
        success=True,
        ip="203.0.113.7",
        user_agent="pytest",
        user_email_hash="a" * 64,
        session_key="b" * 64,
        metadata={"client_version": "1.0"},
    )
    event.refresh_from_db()
    assert event.event_type == EventType.LOGIN
    assert event.success is True
    assert event.ip == "203.0.113.7"
    assert event.user_agent == "pytest"
    assert event.user_email_hash == "a" * 64
    assert event.session_key == "b" * 64
    assert event.metadata == {"client_version": "1.0"}
    assert not any(field.name == "user" for field in SecurityEvent._meta.get_fields())


def test_session_key_and_ip_may_be_empty() -> None:
    event = SecurityEvent.objects.create(event_type=EventType.LOGIN, success=False)
    event.refresh_from_db()
    assert event.session_key == ""
    assert event.ip is None


def test_created_at_defaults_to_utc_now() -> None:
    before = timezone.now()
    event = SecurityEvent.objects.create(event_type=EventType.LOGOUT, success=True)
    after = timezone.now()
    event.refresh_from_db()
    assert before <= event.created_at <= after
    assert event.created_at.utcoffset() == timedelta(0)


def test_created_at_and_event_type_are_indexed() -> None:
    fields: list[Any] = list(SecurityEvent._meta.fields)
    indexed = {field.name for field in fields if field.db_index}
    assert {"created_at", "event_type"} <= indexed
