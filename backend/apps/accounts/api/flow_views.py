from typing import Any

from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import registration, throttling
from apps.accounts.api import messages
from apps.accounts.api.flow_serializers import VerifySerializer
from apps.accounts.api.language import request_language
from apps.accounts.api.views import _enforce_csrf, _limited, _read_body, _render, _unreadable
from apps.accounts.models import CodeProcess

_PUBLIC_ID_MAX_LENGTH = CodeProcess._meta.get_field("public_id").max_length or 0


class AppVerifyView(APIView):
    # Mismo reparto que el formulario (D-02 de registro-api): sin autenticación y solo JSON.
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request: Request) -> Response:
        body, readable = _read_body(request)
        field = body.get("language") if isinstance(body, dict) else None
        language = request_language(
            field if isinstance(field, str) else None, request.headers.get("Accept-Language")
        )
        # Toda petición cuenta para el límite por IP antes de evaluarse (RF-019).
        verdict = throttling.check_flow_ip(str(request.META.get("REMOTE_ADDR", "")))
        if not verdict.allowed:
            return _limited(verdict, language)
        if not readable:
            return _unreadable(language)
        serializer = VerifySerializer(data=body)
        if not serializer.is_valid():
            return Response(
                {"errors": _render(serializer.errors, language)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        public_id = serializer.validated_data["public_id"]
        if not _storable(public_id):
            return _not_found(language)
        result = registration.verify_code(
            public_id=public_id, code=serializer.validated_data["code"]
        )
        if result is registration.VerifyResult.VERIFIED:
            return Response({"result": "verified"})
        if result is registration.VerifyResult.NOT_FOUND:
            return _not_found(language)
        return Response(
            {"code": result.value, "message": messages.error_text(result.value, language)},
            status=status.HTTP_400_BAD_REQUEST,
        )


class BrowserVerifyView(AppVerifyView):
    def initial(self, request: Request, *args: Any, **kwargs: Any) -> None:
        _enforce_csrf(request._request)
        super().initial(request, *args, **kwargs)


def _storable(public_id: str) -> bool:
    # Lo que no cabe en la columna o Postgres no admite (nulo, sustituto suelto) no puede existir:
    # se responde "no encontrado" sin consultar, nunca con un error del servidor (RF-016).
    return (
        0 < len(public_id) <= _PUBLIC_ID_MAX_LENGTH
        and "\x00" not in public_id
        and not any(0xD800 <= ord(char) <= 0xDFFF for char in public_id)
    )


def _not_found(language: str) -> Response:
    return Response(
        {"code": "not_found", "message": messages.error_text("not_found", language)},
        status=status.HTTP_404_NOT_FOUND,
    )
