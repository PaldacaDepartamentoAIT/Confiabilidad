from collections.abc import Callable
from datetime import timedelta
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone

from apps.accounts import conf, password_reset, signals
from apps.accounts.models import PasswordResetRequest, User
from apps.accounts.processes import VerifyResult
from apps.accounts.tests.factories import (
    StartedWithCode,
    make_reset_request,
    make_user,
)
from apps.audit.middleware import CurrentRequestMiddleware
from apps.audit.models import EventType, SecurityEvent
from apps.core.fingerprints import audit_email_fingerprint

pytestmark = pytest.mark.django_db

EMAIL = "ana@x.com"
WEAK_PASSWORD = "12345678"


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
        ("password_reset_code_sent", EventType.CODE_SENT),
        ("password_reset_code_verified", EventType.CODE_VERIFIED),
        ("password_reset_completed", EventType.PASSWORD_RESET),
    ],
)
def test_password_reset_signals_map_to_their_event_type(
    audit_key: None, signal_name: str, event_type: str
) -> None:
    signal = getattr(signals, signal_name)
    _inside_request(lambda: signal.send(sender=object, email=EMAIL, success=True))
    event = SecurityEvent.objects.get(event_type=event_type)
    assert event.success is True
    assert event.ip == "203.0.113.7"
    assert event.user_email_hash == audit_email_fingerprint(EMAIL)


def test_rejected_reset_code_is_recorded_as_failed_verification(audit_key: None) -> None:
    _inside_request(
        lambda: signals.password_reset_code_verified.send(sender=object, email=EMAIL, success=False)
    )
    event = SecurityEvent.objects.get(event_type=EventType.CODE_VERIFIED)
    assert event.success is False


def test_reset_code_expired_within_grace_is_recorded_as_failed_verification(
    audit_key: None,
) -> None:
    make_user(email=EMAIL, name="Ana García")
    started = make_reset_request(EMAIL)
    PasswordResetRequest.objects.update(code_expires_at=timezone.now() - timedelta(minutes=1))

    result = password_reset.verify(public_id=started.public_id, code=started.code)

    assert result is VerifyResult.CODE_EXPIRED
    event = SecurityEvent.objects.get(event_type=EventType.CODE_VERIFIED)
    assert event.success is False
    assert event.user_email_hash == audit_email_fingerprint(EMAIL)


def test_reset_rejected_for_weak_password_leaves_no_reset_or_failure_row(audit_key: None) -> None:
    make_user(email=EMAIL, name="Ana García")
    started = make_reset_request(EMAIL)
    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        password_reset.VerifyResult.VERIFIED
    )
    with pytest.raises(ValidationError):
        _inside_request(
            lambda: password_reset.complete(public_id=started.public_id, password=WEAK_PASSWORD)
        )
    assert not SecurityEvent.objects.filter(event_type=EventType.PASSWORD_RESET).exists()
    assert not SecurityEvent.objects.filter(success=False).exists()


def _started_reset() -> StartedWithCode:
    make_user(email=EMAIL, name="Ana García")
    return make_reset_request(EMAIL)


def _wrong(code: str) -> str:
    return "1" * len(code) if code == "0" * len(code) else "0" * len(code)


def _verifications() -> list[bool]:
    return list(
        SecurityEvent.objects.filter(event_type=EventType.CODE_VERIFIED)
        .order_by("id")
        .values_list("success", flat=True)
    )


def test_locked_reset_code_is_recorded_as_failed_verification(audit_key: None) -> None:
    started = _started_reset()
    limit = conf.max_failed_attempts()
    for _ in range(limit):
        password_reset.verify(public_id=started.public_id, code=_wrong(started.code))

    result = password_reset.verify(public_id=started.public_id, code=started.code)

    assert result is VerifyResult.LOCKED
    assert _verifications() == [False] * (limit + 1)


def test_already_verified_reset_code_is_recorded_as_failed_verification(audit_key: None) -> None:
    started = _started_reset()
    password_reset.verify(public_id=started.public_id, code=started.code)

    result = password_reset.verify(public_id=started.public_id, code=started.code)

    assert result is VerifyResult.ALREADY_VERIFIED
    assert _verifications() == [True, False]


def test_unknown_reset_leaves_no_verification_row(audit_key: None) -> None:
    result = password_reset.verify(public_id="unknown", code="000000")

    assert result is VerifyResult.NOT_FOUND
    assert _verifications() == []


def _deactivate(user: User) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)


def _change_email(user: User) -> None:
    User.objects.filter(pk=user.pk).update(email="nueva@x.com")


def _change_password(user: User) -> None:
    user.set_password("another-long-passw0rd")
    user.save()


@pytest.mark.parametrize("change", [_deactivate, _change_email, _change_password])
def test_account_change_is_answered_as_expired_and_recorded_as_failed(
    audit_key: None, change: Callable[[User], None]
) -> None:
    started = _started_reset()
    change(User.objects.get(email=EMAIL))

    result = password_reset.verify(public_id=started.public_id, code=started.code)

    assert result is VerifyResult.EXPIRED
    assert _verifications() == [False]


@pytest.mark.parametrize("change", [_deactivate, _change_email, _change_password])
def test_expired_process_is_recorded_as_failed_even_if_the_account_changed(
    audit_key: None, change: Callable[[User], None]
) -> None:
    started = _started_reset()
    change(User.objects.get(email=EMAIL))
    PasswordResetRequest.objects.update(code_expires_at=timezone.now() - timedelta(hours=1))

    result = password_reset.verify(public_id=started.public_id, code=started.code)

    assert result is VerifyResult.EXPIRED
    assert _verifications() == [False]
