from typing import Any

from allauth.account.signals import password_changed
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from apps.accounts.signals import (
    account_created,
    account_disabled,
    password_reset_code_sent,
    password_reset_code_verified,
    password_reset_completed,
    pending_registration_requested,
    profile_edited,
    registration_code_sent,
    registration_code_verified,
)
from apps.audit.middleware import current_request
from apps.audit.models import EventType
from apps.audit.recorder import record_event


def _session_key(request: Any) -> str | None:
    session = getattr(request, "session", None)
    return session.session_key if session is not None else None


@receiver(user_logged_in)
def on_user_logged_in(sender: type, request: Any, user: Any, **kwargs: Any) -> None:
    session_key = _session_key(request)
    record_event(
        EventType.LOGIN,
        success=True,
        request=request,
        email=user.email,
        session_key=session_key,
    )


@receiver(user_logged_out)
def on_user_logged_out(sender: type, request: Any, user: Any, **kwargs: Any) -> None:
    session_key = _session_key(request)
    email = user.email if user is not None and user.is_authenticated else ""
    record_event(
        EventType.LOGOUT,
        success=True,
        request=request,
        email=email,
        session_key=session_key,
    )


@receiver(password_changed)
def on_password_changed(sender: type, request: Any, user: Any, **kwargs: Any) -> None:
    record_event(
        EventType.PASSWORD_CHANGE,
        success=True,
        request=request,
        email=user.email,
        session_key=_session_key(request),
    )


@receiver(pending_registration_requested)
def on_pending_registration_requested(
    sender: type, email: str, success: bool, **kwargs: Any
) -> None:
    _record_account_signal(EventType.PENDING_REGISTRATION, email, success)


@receiver(registration_code_sent)
def on_registration_code_sent(sender: type, email: str, success: bool, **kwargs: Any) -> None:
    _record_account_signal(EventType.CODE_SENT, email, success)


@receiver(registration_code_verified)
def on_registration_code_verified(sender: type, email: str, success: bool, **kwargs: Any) -> None:
    _record_account_signal(EventType.CODE_VERIFIED, email, success)


@receiver(account_created)
def on_account_created(sender: type, email: str, success: bool, **kwargs: Any) -> None:
    _record_account_signal(EventType.ACCOUNT_REGISTRATION, email, success)


def _record_account_signal(event_type: EventType, email: str, success: bool) -> None:
    request = current_request()
    record_event(
        event_type,
        success=success,
        request=request,
        email=email,
        session_key=_session_key(request),
    )


@receiver(password_reset_code_sent)
def on_password_reset_code_sent(sender: type, email: str, success: bool, **kwargs: Any) -> None:
    _record_account_signal(EventType.CODE_SENT, email, success)


@receiver(password_reset_code_verified)
def on_password_reset_code_verified(sender: type, email: str, success: bool, **kwargs: Any) -> None:
    _record_account_signal(EventType.CODE_VERIFIED, email, success)


@receiver(password_reset_completed)
def on_password_reset_completed(sender: type, email: str, success: bool, **kwargs: Any) -> None:
    _record_account_signal(EventType.PASSWORD_RESET, email, success)


@receiver(profile_edited)
def on_profile_edited(sender: type, email: str, success: bool, **kwargs: Any) -> None:
    _record_account_signal(EventType.PROFILE_EDIT, email, success)


@receiver(account_disabled)
def on_account_disabled(sender: type, email: str, success: bool, **kwargs: Any) -> None:
    _record_account_signal(EventType.ACCOUNT_DISABLE, email, success)
