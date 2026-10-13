from typing import Any

from allauth.account.signals import password_changed
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

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
