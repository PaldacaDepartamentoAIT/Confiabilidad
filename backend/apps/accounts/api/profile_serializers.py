from typing import Any, cast

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.accounts.api.auth_serializers import _reject_surrogates
from apps.accounts.validators import (
    normalize_country,
    normalize_name,
    validate_birthdate,
    validate_country,
    validate_name,
)

_EDITABLE_FIELDS = frozenset({"name", "birthdate", "country"})
_ALLOWED_BODY_KEYS = _EDITABLE_FIELDS | {"language"}


class ProfileUpdateSerializer(serializers.Serializer[dict[str, Any]]):
    name = serializers.CharField(required=False, validators=[_reject_surrogates, validate_name])
    birthdate = serializers.DateField(
        required=False, input_formats=["iso-8601"], validators=[validate_birthdate]
    )
    country = serializers.CharField(required=False, validators=[_reject_surrogates])

    def validate_name(self, value: str) -> str:
        normalized = normalize_name(value)
        validate_name(normalized)
        return normalized

    def validate_country(self, value: str) -> str:
        normalized = normalize_country(value)
        stored_country = self.context.get("stored_country")
        validate_country(
            normalized,
            stored_value=stored_country if isinstance(stored_country, str) else None,
        )
        return normalized

    def to_internal_value(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            return cast(dict[str, Any], super().to_internal_value(data))

        extra_errors: dict[str, list[serializers.ErrorDetail]] = {}
        for key in data:
            if key == "email":
                extra_errors["email"] = [
                    serializers.ErrorDetail(
                        str(_("The email address cannot be changed.")),
                        code="email_immutable",
                    )
                ]
            elif key not in _ALLOWED_BODY_KEYS:
                extra_errors[str(key)] = [
                    serializers.ErrorDetail(
                        str(_("This field is not allowed.")),
                        code="unknown_field",
                    )
                ]

        editable_data = {key: value for key, value in data.items() if key in _EDITABLE_FIELDS}
        if not editable_data and not extra_errors:
            extra_errors["non_field_errors"] = [
                serializers.ErrorDetail(
                    str(_("Provide at least one profile field to update.")),
                    code="no_profile_fields",
                )
            ]

        try:
            parsed = cast(dict[str, Any], super().to_internal_value(editable_data))
        except serializers.ValidationError as error:
            detail = error.detail
            merged: dict[str, Any] = (
                {**detail, **extra_errors}
                if isinstance(detail, dict)
                else {**extra_errors, "non_field_errors": detail}
            )
            raise serializers.ValidationError(merged) from error

        if extra_errors:
            raise serializers.ValidationError(extra_errors)
        return parsed
