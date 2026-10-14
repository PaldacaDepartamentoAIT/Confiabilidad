from datetime import date

import pytest
from allauth.account.forms import ChangePasswordForm
from allauth.account.signals import password_changed
from django.test import RequestFactory

from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user
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


def test_password_change_rejected_for_weak_password_leaves_no_change_or_failure_row(
    audit_key: None,
) -> None:
    user = make_user(email="ana@x.com", name="Ana García")
    form = ChangePasswordForm(
        data={
            "oldpassword": DEFAULT_PASSWORD,
            "password1": "12345678",
            "password2": "12345678",
        },
        user=user,
    )

    assert not form.is_valid()
    assert "password1" in form.errors
    assert not SecurityEvent.objects.filter(event_type=EventType.PASSWORD_CHANGE).exists()
    assert not SecurityEvent.objects.filter(success=False).exists()
