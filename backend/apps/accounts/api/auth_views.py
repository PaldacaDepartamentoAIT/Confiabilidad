import secrets
from typing import Any, ClassVar

from allauth.account.adapter import get_adapter
from django.contrib.auth import HASH_SESSION_KEY, SESSION_KEY, get_user, login, logout
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import sessions, throttling
from apps.accounts.api import messages
from apps.accounts.api.auth_serializers import LoginSerializer
from apps.accounts.api.language import request_language
from apps.accounts.api.views import _enforce_csrf, _limited, _read_body, _render, _unreadable
from apps.accounts.models import User
from apps.consents.models import Terms
from apps.consents.services import TermsState, consent_status
from apps.consents.versions import current_document

_AUTH_BACKEND = "allauth.account.auth_backends.AuthenticationBackend"


def _err(code: str, language: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> Response:
    return Response(
        {"code": code, "message": messages.error_text(code, language)}, status=http_status
    )


def _terms_payload(terms_state: TermsState, language: str) -> dict[str, str] | None:
    if terms_state is not TermsState.NOT_ACCEPTED:
        return None
    doc = current_document(Terms.Kind.TERMS, language)
    if doc is None:
        return None
    return {"version": doc.version, "locale": doc.locale, "content": doc.content}


def _session_info_payload(user: User, language: str) -> dict[str, Any]:
    terms_state = consent_status(user).terms
    return {
        "user": {"email": user.email, "name": user.name},
        "terms_status": terms_state.value,
        "terms": _terms_payload(terms_state, language),
    }


def _verify_active_user(user: Any, raw_key: Any) -> tuple[User, str] | None:
    if not isinstance(user, User) or not user.is_authenticated:
        return None
    if not user.is_active:
        sessions.revoke_all_user_sessions(user)
        return None
    if not isinstance(raw_key, str) or not sessions.is_session_active(raw_key, user.pk):
        return None
    return user, raw_key


def _resolve_user_from_token(raw_key: str) -> tuple[User, str] | None:
    if not raw_key:
        return None
    store = sessions._session_store(raw_key)
    if not store.exists(raw_key):
        return None
    data = store.load()
    user_id, session_hash = data.get(SESSION_KEY), data.get(HASH_SESSION_KEY)
    if not user_id or not isinstance(session_hash, str):
        return None
    user = User.objects.filter(pk=user_id).first()
    if user is None or not secrets.compare_digest(session_hash, user.get_session_auth_hash()):
        return None
    return _verify_active_user(user, raw_key)


def _authenticated_session(request: Request, client_kind: str) -> tuple[User, str] | None:
    django_request = request._request
    if client_kind == "app":
        return _resolve_user_from_token(str(request.headers.get("X-Session-Token") or "").strip())
    raw_key = getattr(getattr(django_request, "session", None), "session_key", None)
    if not isinstance(raw_key, str) or not raw_key:
        return None
    # DRF sustituye request._request.user por AnonymousUser cuando authentication_classes=[].
    return _verify_active_user(get_user(django_request), raw_key)


def _body_language(request: Request, body: Any, readable: bool = True) -> str:
    field = body.get("language") if readable and isinstance(body, dict) else None
    return request_language(
        field if isinstance(field, str) else None, request.headers.get("Accept-Language")
    )


def _touch_request(django_request: HttpRequest, client_kind: str, raw_key: str) -> HttpRequest:
    if client_kind == "browser":
        return django_request
    copy = HttpRequest()
    copy.META = django_request.META
    copy.session = sessions._session_store(raw_key)
    return copy


class _BrowserCsrfMixin(APIView):
    client_kind: ClassVar[str] = "browser"

    def initial(self, request: Request, *args: Any, **kwargs: Any) -> None:
        _enforce_csrf(request._request)
        super().initial(request, *args, **kwargs)


class AppLoginView(APIView):
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    client_kind: ClassVar[str] = "app"

    def post(self, request: Request) -> Response:
        body, readable = _read_body(request)
        language = _body_language(request, body, readable)
        verdict = throttling.check_login_ip(str(request.META.get("REMOTE_ADDR", "")))
        if not verdict.allowed:
            return _limited(verdict, language)
        if _authenticated_session(request, self.client_kind) is not None:
            return _err("already_authenticated", language)
        if not readable:
            return _unreadable(language)
        serializer = LoginSerializer(data=body)
        if not serializer.is_valid():
            return Response(
                {"errors": _render(serializer.errors, language)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._authenticate(request._request, serializer.validated_data, language)

    def _authenticate(
        self, django_request: HttpRequest, data: dict[str, Any], language: str
    ) -> Response:
        adapter = get_adapter(django_request)
        credentials = {"email": data["email"], "password": data["password"]}
        try:
            user = adapter.authenticate(django_request, **credentials)
        except ValidationError as error:
            code = (
                "too_many_login_attempts"
                if error.code == "too_many_login_attempts"
                else "invalid_credentials"
            )
            return _err(code, language)
        if user is None:
            return _err("invalid_credentials", language)
        if not user.is_active:
            # No llamamos a super().pre_login porque accede a sesión/mensajes y añade Vary: Cookie.
            adapter.record_inactive_login_attempt(django_request, user)
            return _err("invalid_credentials", language)
        login(django_request, user, backend=_AUTH_BACKEND)
        payload = _session_info_payload(user, language)
        if self.client_kind == "app":
            payload["session_token"] = django_request.session.session_key
        return Response(payload, status=status.HTTP_200_OK)


class BrowserLoginView(_BrowserCsrfMixin, AppLoginView):
    pass


class AppSessionView(APIView):
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]
    client_kind: ClassVar[str] = "app"

    def get(self, request: Request) -> Response:
        language = request_language(
            request.query_params.get("language"), request.headers.get("Accept-Language")
        )
        auth = _authenticated_session(request, self.client_kind)
        if auth is None:
            return _err("unauthenticated", language, status.HTTP_401_UNAUTHORIZED)
        user, raw_key = auth
        sessions.touch_session(_touch_request(request._request, self.client_kind, raw_key), user)
        return Response(_session_info_payload(user, language), status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class BrowserSessionView(AppSessionView):
    client_kind = "browser"


class AppLogoutView(APIView):
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    client_kind: ClassVar[str] = "app"

    def post(self, request: Request) -> Response:
        body, readable = _read_body(request) if request.content_type else ({}, True)
        language = _body_language(request, body, readable)
        auth = _authenticated_session(request, self.client_kind)
        if auth is None:
            return _err("unauthenticated", language, status.HTTP_401_UNAUTHORIZED)
        user, raw_key = auth
        django_request = request._request
        django_request.user = user
        if self.client_kind == "app":
            django_request.session = sessions._session_store(raw_key)
        logout(django_request)
        sessions.close_current_session(user, raw_key)
        return Response({"result": "logged_out"}, status=status.HTTP_200_OK)


class BrowserLogoutView(_BrowserCsrfMixin, AppLogoutView):
    pass
