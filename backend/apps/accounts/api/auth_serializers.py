from typing import Any

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.accounts.api.serializers import RegistrationSerializer


def _reject_surrogates(value: str) -> None:
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise serializers.ValidationError(
            _("Surrogate characters are not allowed."),
            code="surrogate_characters_not_allowed",
        )


class LoginSerializer(serializers.Serializer[dict[str, Any]]):
    email = serializers.EmailField(max_length=254, validators=[_reject_surrogates])
    password = serializers.CharField(trim_whitespace=False, validators=[_reject_surrogates])

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class TermsAcceptSerializer(serializers.Serializer[dict[str, Any]]):
    # Reutiliza las reglas y códigos de RF-004 de registro-api sin duplicar la validación.
    def run_validation(self, data: Any = serializers.empty) -> dict[str, str]:
        try:
            return RegistrationSerializer().validate_terms(data)
        except serializers.ValidationError as error:
            detail = error.detail
            if isinstance(detail, dict):
                raise
            raise serializers.ValidationError({"non_field_errors": detail}) from error


class RevokeSessionSerializer(serializers.Serializer[dict[str, Any]]):
    session_id = serializers.IntegerField(min_value=1)
