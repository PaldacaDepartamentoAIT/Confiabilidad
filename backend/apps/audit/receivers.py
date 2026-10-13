from typing import Any

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from apps.audit.models import EventType
from apps.audit.recorder import record_event


@receiver(user_logged_in)
def on_user_logged_in(sender: type, request: Any, user: Any, **kwargs: Any) -> None:
    session_key = request.session.session_key if request is not None else None
    record_event(
        EventType.LOGIN,
        success=True,
        request=request,
        email=user.email,
        session_key=session_key,
    )


@receiver(user_logged_out)
def on_user_logged_out(sender: type, request: Any, user: Any, **kwargs: Any) -> None:
    session_key = request.session.session_key if request is not None else None
    email = user.email if user is not None and user.is_authenticated else ""
    record_event(
        EventType.LOGOUT,
        success=True,
        request=request,
        email=email,
        session_key=session_key,
    )
