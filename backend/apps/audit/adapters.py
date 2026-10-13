from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpRequest

from apps.audit.models import EventType
from apps.audit.recorder import record_event


class AuditAccountAdapter(DefaultAccountAdapter):  # type: ignore[misc]  # allauth no publica tipos
    def authentication_failed(self, request: HttpRequest, **credentials: Any) -> None:
        super().authentication_failed(request, **credentials)
        record_event(
            EventType.LOGIN,
            success=False,
            request=request,
            email=str(credentials.get("email", "")),
            metadata={"reason": "invalid_credentials"},
        )
