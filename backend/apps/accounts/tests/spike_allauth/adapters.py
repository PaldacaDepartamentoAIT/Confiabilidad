from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpRequest


class DeferredSaveAdapter(DefaultAccountAdapter):  # type: ignore[misc]
    def save_user(self, request: HttpRequest, user: Any, form: Any, commit: bool = True) -> Any:
        return super().save_user(request, user, form, commit=False)


class TrustedEmailAdapter(DefaultAccountAdapter):  # type: ignore[misc]
    def is_email_verified(self, request: HttpRequest, email: str) -> bool:
        return True


FIXED_VERIFICATION_CODE = "SPIK-E000"


class FixedCodeAdapter(DefaultAccountAdapter):  # type: ignore[misc]
    def generate_email_verification_code(self) -> str:
        return FIXED_VERIFICATION_CODE
