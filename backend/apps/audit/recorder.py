from typing import Any

from django.http import HttpRequest

from apps.audit.models import EventType, SecurityEvent
from apps.core.fingerprints import audit_email_fingerprint, audit_session_fingerprint


def record_event(
    event_type: EventType,
    *,
    success: bool,
    request: HttpRequest | None = None,
    email: str = "",
    session_key: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> SecurityEvent:
    return SecurityEvent.objects.create(
        event_type=event_type,
        success=success,
        ip=request.META.get("REMOTE_ADDR") if request is not None else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request is not None else "",
        user_email_hash=audit_email_fingerprint(email) if email else "",
        session_key=audit_session_fingerprint(session_key) if session_key else "",
        metadata=metadata or {},
    )
