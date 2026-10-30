from typing import Any

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class _Text(serializers.Field):  # type: ignore[type-arg]
    # Sin los validadores de CharField: un identificador de cualquier forma debe llegar a la vista,
    # que responde "no encontrado" (RF-016), y no quedarse en un error de campo.
    default_error_messages = {"invalid": _("Not a valid string.")}

    def to_internal_value(self, data: Any) -> str:
        if not isinstance(data, str):
            self.fail("invalid")
        return data

    def to_representation(self, value: Any) -> str:
        return str(value)


class VerifySerializer(serializers.Serializer[dict[str, str]]):
    public_id = _Text()
    code = _Text()


class CompleteSerializer(VerifySerializer):
    password = _Text()
