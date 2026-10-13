from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from apps.audit.models import EventType
from apps.audit.recorder import record_event

LOGIN_LIMIT_CODE = "too_many_login_attempts"


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
