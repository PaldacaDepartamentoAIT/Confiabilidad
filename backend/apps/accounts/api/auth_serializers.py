from typing import Any

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


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
