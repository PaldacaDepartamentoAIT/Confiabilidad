import dataclasses
from typing import Any, ClassVar

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import serializers, status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import registration, throttling
from apps.accounts.api import messages
from apps.accounts.api.flow_serializers import VerifySerializer, _Text
from apps.accounts.api.language import request_language
from apps.accounts.api.views import _enforce_csrf, _limited, _read_body, _render, _unreadable
from apps.accounts.models import CodeProcess
from apps.accounts.validators import COUNTRY_CODES
from apps.consents.models import Terms
from apps.consents.versions import current_document

_PUBLIC_ID_MAX_LENGTH = CodeProcess._meta.get_field("public_id").max_length or 0


class PublicIdSerializer(serializers.Serializer[dict[str, str]]):
    public_id = _Text()


class _FlowView(APIView):
    # Mismo reparto que el formulario (D-02 de registro-api): sin autenticación y solo JSON.
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    serializer_class: ClassVar[type[serializers.Serializer[dict[str, str]]]]
    counts_for_limit: ClassVar[bool] = True

    def post(self, request: Request) -> Response:
        body, readable = _read_body(request)
        field = body.get("language") if isinstance(body, dict) else None
        language = request_language(
            field if isinstance(field, str) else None, request.headers.get("Accept-Language")
        )
        # Toda petición cuenta para el límite por IP antes de evaluarse, salvo la consulta del
        # estado, que solo lee (RF-019).
        if self.counts_for_limit:
            verdict = throttling.check_flow_ip(str(request.META.get("REMOTE_ADDR", "")))
            if not verdict.allowed:
                return _limited(verdict, language)
        if not readable:
            return _unreadable(language)
        serializer = self.serializer_class(data=body)
        if not serializer.is_valid():
            return Response(
                {"errors": _render(serializer.errors, language)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        if not _storable(data["public_id"]):
            return _not_found(language)
        return self.act(data, language)

    def act(self, data: dict[str, str], language: str) -> Response:
        raise NotImplementedError


class _BrowserMixin(APIView):
    def initial(self, request: Request, *args: Any, **kwargs: Any) -> None:
        _enforce_csrf(request._request)
        super().initial(request, *args, **kwargs)


class AppVerifyView(_FlowView):
    serializer_class = VerifySerializer

    def act(self, data: dict[str, str], language: str) -> Response:
        result = registration.verify_code(public_id=data["public_id"], code=data["code"])
        if result is registration.VerifyResult.VERIFIED:
            return Response({"result": "verified"})
        return _refused(result.value, language)


class BrowserVerifyView(_BrowserMixin, AppVerifyView):
    pass


class AppResendView(_FlowView):
    serializer_class = PublicIdSerializer

    def act(self, data: dict[str, str], language: str) -> Response:
        result = registration.resend_code(public_id=data["public_id"])
        if isinstance(result, registration.Resent):
            return Response({"result": "resent"}, status=status.HTTP_202_ACCEPTED)
        return _refused(result.value, language)


class BrowserResendView(_BrowserMixin, AppResendView):
    pass


class AppStatusView(_FlowView):
    serializer_class = PublicIdSerializer
    counts_for_limit = False

    def act(self, data: dict[str, str], language: str) -> Response:
        current = registration.status(public_id=data["public_id"])
        if current is None:
            return _not_found(language)
        return Response(dataclasses.asdict(current))


class BrowserStatusView(_BrowserMixin, AppStatusView):
    pass


class AppOptionsView(APIView):
    # Datos públicos del formulario: no lee procesos ni cuenta para ningún límite.
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        field = request.query_params.get("language")
        language = request_language(field, request.headers.get("Accept-Language"))
        return Response(
            {
                "countries": list(COUNTRY_CODES),
                "terms": _document(Terms.Kind.TERMS, language),
                "marketing": _document(Terms.Kind.MARKETING, language),
            }
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class BrowserOptionsView(AppOptionsView):
    # Da al navegador la cookie que exigen los POST del flujo (D-09).
    pass


def _document(kind: str, language: str) -> dict[str, str] | None:
    document = current_document(kind, language)
    if document is None:
        return None
    return {"version": document.version, "locale": document.locale, "content": document.content}


def _storable(public_id: str) -> bool:
    # Lo que no cabe en la columna o Postgres no admite (nulo, sustituto suelto) no puede existir:
    # se responde "no encontrado" sin consultar, nunca con un error del servidor (RF-016).
    return (
        0 < len(public_id) <= _PUBLIC_ID_MAX_LENGTH
        and "\x00" not in public_id
        and not any(0xD800 <= ord(char) <= 0xDFFF for char in public_id)
    )


def _refused(code: str, language: str) -> Response:
    if code == "not_found":
        return _not_found(language)
    return Response(
        {"code": code, "message": messages.error_text(code, language)},
        status=status.HTTP_400_BAD_REQUEST,
    )


def _not_found(language: str) -> Response:
    return Response(
        {"code": "not_found", "message": messages.error_text("not_found", language)},
        status=status.HTTP_404_NOT_FOUND,
    )
