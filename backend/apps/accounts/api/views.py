from typing import Any

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.authentication import CSRFCheck
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import registration, throttling
from apps.accounts.api import messages
from apps.accounts.api.language import request_language
from apps.accounts.api.serializers import RegistrationSerializer
from apps.accounts.validators import MINIMUM_AGE_EXTRA_DAYS, MINIMUM_AGE_YEARS, NAME_MAX_LENGTH

_PARAMS = {"max": NAME_MAX_LENGTH, "years": MINIMUM_AGE_YEARS, "days": MINIMUM_AGE_EXTRA_DAYS}


class AppRegistrationView(APIView):
    # Sin autenticación: la sesión de quien envía el formulario no influye (S-14).
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]
    # Solo JSON: otra web no puede enviarlo desde un navegador sin la comprobación previa de CORS
    # (D-16); un formulario HTML sí podría.
    parser_classes = [JSONParser]

    def post(self, request: Request) -> Response:
        header = request.headers.get("Accept-Language")
        # Orden de D-12: el límite por IP va antes de leer el cuerpo; solo cuenta lo que no
        # rechaza ningún límite (S-06).
        ip = str(request.META.get("REMOTE_ADDR", ""))
        verdict = throttling.check_ip(ip, record=False)
        if not verdict.allowed:
            return _limited(verdict, request_language(None, header))
        try:
            if request.content_type.split(";")[0].strip().lower() != "application/json":
                # En la ruta web, el CSRF ya ha leído un formulario y DRF lo vería vacío.
                raise exceptions.UnsupportedMediaType(request.content_type)
            body = request.data
        except Exception:
            # Cualquier fallo al leer el cuerpo (JSON muy anidado, codificación rara) es un cuerpo
            # ilegible: 400 que cuenta para la IP, nunca 500.
            throttling.record_ip(ip)
            return _unreadable(request_language(None, header))
        field = body.get("language") if isinstance(body, dict) else None
        language = request_language(field if isinstance(field, str) else None, header)
        serializer = RegistrationSerializer(data=body)
        if not serializer.is_valid():
            throttling.record_ip(ip)
            return Response(
                {"errors": _render(serializer.errors, language)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        verdict = throttling.check_email_ip(data["email"], ip)
        if not verdict.allowed:
            return _limited(verdict, language)
        throttling.record_ip(ip)
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


def _limited(verdict: throttling.Verdict, language: str) -> Response:
    return Response(
        {
            "message": messages.rate_limited_text(language, seconds=verdict.retry_after),
            "retry_after": verdict.retry_after,
        },
        status=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(verdict.retry_after)},
    )


def _unreadable(language: str) -> Response:
    error = {"code": "invalid", "message": messages.error_text("invalid", language)}
    return Response({"errors": {"non_field_errors": [error]}}, status=status.HTTP_400_BAD_REQUEST)


def _render(errors: Any, language: str) -> dict[str, list[dict[str, str]]]:
    return {
        field: [
            {
                "code": str(detail.code),
                "message": messages.error_text(
                    _known(str(detail.code)), language, field=field, params=_PARAMS
                ),
            }
            for detail in details
        ]
        for field, details in errors.items()
    }


def _known(code: str) -> str:
    # Un código sin texto propio (por ejemplo, uno nuevo de DRF) recibe el genérico, nunca un 500.
    return code if code in messages.ERRORS else "invalid"
