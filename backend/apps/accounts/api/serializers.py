from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.accounts.validators import (
    normalize_country,
    validate_birthdate,
    validate_country,
    validate_name,
    validate_registration_email,
)
from apps.consents.models import Terms
from apps.consents.services import current_document_shown


class RegistrationSerializer(serializers.Serializer[dict[str, Any]]):
    # Solo reglas que no consultan cuentas ni registros pendientes (RF-024 de procesos-pendientes).
    name = serializers.CharField(validators=[validate_name])
    birthdate = serializers.DateField(input_formats=["iso-8601"], validators=[validate_birthdate])
    email = serializers.CharField(validators=[validate_registration_email])
    country = serializers.CharField()
    terms = serializers.JSONField()
    language = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, default=None
    )

    def validate_country(self, value: str) -> str:
        country = normalize_country(value)
        validate_country(country)
        return country

    def validate_terms(self, value: object) -> dict[str, str]:
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Terms must be an object."), code="invalid")
        errors: list[serializers.ErrorDetail] = []
        if value.get("accepted") is not True:
            errors.append(
                serializers.ErrorDetail(
                    str(_("Terms must be accepted.")), code="terms_not_accepted"
                )
            )
        version, locale = value.get("version"), value.get("locale")
        if not isinstance(version, str) or not isinstance(locale, str):
            errors.append(
                serializers.ErrorDetail(str(_("Terms document is required.")), code="required")
            )
        else:
            try:
                document = current_document_shown(Terms.Kind.TERMS, version=version, locale=locale)
            except DjangoValidationError as error:
                errors.append(serializers.ErrorDetail(str(error.message), code=error.code))
        if errors:
            raise serializers.ValidationError(errors)
        return {"version": document.version, "locale": document.locale}
