import inspect
from typing import Any

from allauth.account import app_settings as allauth_account_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.internal import ratelimit as allauth_ratelimit
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from apps.audit.models import EventType
from apps.audit.recorder import record_event

LOGIN_LIMIT_CODE = "too_many_login_attempts"
INACTIVE_ACCOUNT_CODE = "inactive_account"


class AuditAccountAdapter(DefaultAccountAdapter):  # type: ignore[misc]  # allauth no publica tipos
    def pre_authenticate(self, request: HttpRequest, **credentials: Any) -> None:
        try:
            super().pre_authenticate(request, **credentials)
        except ValidationError as error:
            if error.code == LOGIN_LIMIT_CODE:
                self._record_limit_rejection(request, credentials)
            raise

    def authentication_failed(self, request: HttpRequest, **credentials: Any) -> None:
        super().authentication_failed(request, **credentials)
        record_event(
            EventType.LOGIN,
            success=False,
            request=request,
            email=str(credentials.get("email", "")),
            metadata={"reason": "invalid_credentials"},
        )

    def _record_limit_rejection(self, request: HttpRequest, credentials: dict[str, Any]) -> None:
        email = str(credentials.get("email", ""))
        record_event(
            EventType.LOGIN,
            success=False,
            request=request,
            email=email,
            metadata={"reason": LOGIN_LIMIT_CODE},
        )
        record_event(
            EventType.LOCKOUT,
            success=False,
            request=request,
            email=email,
            metadata={"reason": LOGIN_LIMIT_CODE},
        )

    def record_inactive_login_attempt(self, request: HttpRequest, user: Any) -> None:
        # Cuenta para el límite de allauth igual que una contraseña errónea (D-03, C-02).
        key = self._get_login_attempts_cache_key(request, email=user.email)
        _consume_login_failed(request, key)
        record_event(
            EventType.LOGIN,
            success=False,
            request=request,
            email=user.email,
            metadata={"reason": INACTIVE_ACCOUNT_CODE},
        )

    def pre_login(self, request: HttpRequest, user: Any, **kwargs: Any) -> Any:
        if not user.is_active:
            self.record_inactive_login_attempt(request, user)
        return super().pre_login(request, user, **kwargs)


def _consume_login_failed(request: HttpRequest, key: str) -> None:
    kwargs: dict[str, Any] = {}
    params = inspect.signature(allauth_ratelimit.consume).parameters
    if "app" in params:
        kwargs["app"] = "allauth.account"
    if "config" in params:
        kwargs["config"] = allauth_account_settings.RATE_LIMITS
    allauth_ratelimit.consume(request, action="login_failed", key=key, **kwargs)
