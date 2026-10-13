from datetime import date

import pytest
from allauth.account.signals import password_changed
from django.test import RequestFactory

from apps.accounts.models import User
from apps.audit.models import EventType, SecurityEvent
from apps.core.fingerprints import audit_email_fingerprint

pytestmark = pytest.mark.django_db


@pytest.fixture
def audit_key(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = "test-audit-key"  # type: ignore[attr-defined]


def test_password_changed_signal_records_password_change_row(audit_key: None) -> None:
    user = User.objects.create_user(
        "ana@x.com", "Clave-segura-2026!", name="Ana", birthdate=date(1990, 1, 1), country="ES"
    )
    request = RequestFactory().post("/", REMOTE_ADDR="203.0.113.7")

    password_changed.send(sender=User, request=request, user=user)

    event = SecurityEvent.objects.get(event_type=EventType.PASSWORD_CHANGE)
    assert event.success is True
    assert event.ip == "203.0.113.7"
    assert event.user_email_hash == audit_email_fingerprint("ana@x.com")
    assert event.session_key == ""
