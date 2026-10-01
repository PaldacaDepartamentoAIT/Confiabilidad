from datetime import date
from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest

SPIKE_PROFILE: dict[str, object] = {
    "name": "Spike User",
    "birthdate": date(1990, 1, 1),
    "country": "ES",
}


class ProfileFillingAdapter(DefaultAccountAdapter):  # type: ignore[misc]
    def new_user(self, request: HttpRequest) -> AbstractBaseUser:
        user: AbstractBaseUser = super().new_user(request)
        for field_name, value in SPIKE_PROFILE.items():
            setattr(user, field_name, value)
        return user


class DeferredSaveAdapter(ProfileFillingAdapter):
    def save_user(self, request: HttpRequest, user: Any, form: Any, commit: bool = True) -> Any:
        return super().save_user(request, user, form, commit=False)


class TrustedEmailAdapter(ProfileFillingAdapter):
    def is_email_verified(self, request: HttpRequest, email: str) -> bool:
        return True


FIXED_VERIFICATION_CODE = "SPIK-E000"


class FixedCodeAdapter(ProfileFillingAdapter):
    def generate_email_verification_code(self) -> str:
        return FIXED_VERIFICATION_CODE
