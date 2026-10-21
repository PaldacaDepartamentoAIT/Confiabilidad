from typing import Any

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.authentication import CSRFCheck
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import registration
from apps.accounts.api import messages
from apps.accounts.api.language import request_language
from apps.accounts.api.serializers import RegistrationSerializer
from apps.accounts.validators import MINIMUM_AGE_EXTRA_DAYS, MINIMUM_AGE_YEARS, NAME_MAX_LENGTH

_PARAMS = {"max": NAME_MAX_LENGTH, "years": MINIMUM_AGE_YEARS, "days": MINIMUM_AGE_EXTRA_DAYS}


class AppRegistrationView(APIView):
    # Sin autenticación: la sesión de quien envía el formulario no influye (S-14).
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        field = request.data.get("language") if isinstance(request.data, dict) else None
        language = request_language(
            field if isinstance(field, str) else None, request.headers.get("Accept-Language")
        )
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": _render(serializer.errors, language)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        started = registration.start(
            email=data["email"],
            name=data["name"],
            birthdate=data["birthdate"],
            country=data["country"],
            language=language,
            terms_version=data["terms"]["version"],
            terms_locale=data["terms"]["locale"],
        )
        return Response(
            {"public_id": started.public_id, "message": messages.neutral_text(language)},
            status=status.HTTP_202_ACCEPTED,
        )


class BrowserRegistrationView(AppRegistrationView):
    def initial(self, request: Request, *args: Any, **kwargs: Any) -> None:
        # DRF exime sus vistas de CSRF y solo lo exige con sesión: aquí se exige siempre (D-02).
        _enforce_csrf(request._request)
        super().initial(request, *args, **kwargs)


def _enforce_csrf(request: HttpRequest) -> None:
    check = CSRFCheck(lambda _request: HttpResponse())
    check.process_request(request)
    if check.process_view(request, lambda _request: HttpResponse(), (), {}) is not None:
        raise exceptions.PermissionDenied(_("CSRF verification failed."))


def _render(errors: Any, language: str) -> dict[str, list[dict[str, str]]]:
    return {
        field: [
            {
                "code": str(detail.code),
                "message": messages.error_text(
                    str(detail.code), language, field=field, params=_PARAMS
                ),
            }
            for detail in details
        ]
        for field, details in errors.items()
    }
