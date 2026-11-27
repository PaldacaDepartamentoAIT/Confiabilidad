from typing import Any, ClassVar

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import disable, profile, throttling
from apps.accounts.api import messages
from apps.accounts.api.auth_views import _body_language, _BrowserCsrfMixin, _require_auth
from apps.accounts.api.flow_views import _password_params
from apps.accounts.api.language import request_language
from apps.accounts.api.profile_serializers import (
    AccountDisableSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer,
)
from apps.accounts.api.views import _known, _limited, _read_body, _render, _unreadable
from apps.accounts.models import User


def _profile_payload(data: profile.ProfileData, user: User) -> dict[str, Any]:
    block_reason = disable.disable_block_reason(user)
    verdict = throttling.check_account_disable(user.pk)
    return {
        "email": data.email,
        "name": data.name,
        "birthdate": data.birthdate.isoformat(),
        "country": data.country,
        "can_disable": block_reason is None,
        "disable_block_reason": block_reason.value if block_reason is not None else None,
        "disable_retry_after": 0 if verdict.allowed else verdict.retry_after,
    }


class AppProfileView(APIView):
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    client_kind: ClassVar[str] = "app"

    def get(self, request: Request) -> Response:
        language = request_language(
            request.query_params.get("language"), request.headers.get("Accept-Language")
        )
        auth = _require_auth(request, self.client_kind, language, require_terms=True)
        if isinstance(auth, Response):
            return auth
        user, _ = auth
        return Response(
            _profile_payload(profile.get_profile(user), user), status=status.HTTP_200_OK
        )

    def patch(self, request: Request) -> Response:
        body, readable = _read_body(request)
        language = _body_language(request, body, readable)
        auth = _require_auth(request, self.client_kind, language, require_terms=True)
        if isinstance(auth, Response):
            return auth
        if not readable:
            return _unreadable(language)
        user, _ = auth
        serializer = ProfileUpdateSerializer(data=body, context={"stored_country": user.country})
        if not serializer.is_valid():
            return Response(
                {"errors": _render(serializer.errors, language)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        updated = profile.update_profile(
            user,
            name=data["name"] if "name" in data else profile.UNSET,
            birthdate=data["birthdate"] if "birthdate" in data else profile.UNSET,
            country=data["country"] if "country" in data else profile.UNSET,
        )
        return Response(_profile_payload(updated, user), status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name="get")
class BrowserProfileView(_BrowserCsrfMixin, AppProfileView):
    pass


def _password_change_errors(
    result: profile.PasswordChangeInvalid,
    body: Any,
    raw_new: Any,
    language: str,
) -> dict[str, list[dict[str, str]]]:
    errors: dict[str, list[dict[str, str]]] = {}
    if result.current_password_incorrect:
        errors["current_password"] = [
            {
                "code": "current_password_incorrect",
                "message": messages.error_text("current_password_incorrect", language),
            }
        ]
    if raw_new is None:
        code = (
            "null"
            if isinstance(body, dict) and "new_password" in body and body["new_password"] is None
            else "required"
        )
        errors["new_password"] = [{"code": code, "message": messages.error_text(code, language)}]
    elif raw_new == "":
        errors["new_password"] = [
            {"code": "blank", "message": messages.error_text("blank", language)}
        ]
    elif result.new_password_codes:
        params = _password_params()
        errors["new_password"] = [
            {
                "code": code,
                "message": messages.error_text(_known(code), language, params=params),
            }
            for code in result.new_password_codes
        ]
    return errors


class AppPasswordChangeView(APIView):
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    client_kind: ClassVar[str] = "app"

    def post(self, request: Request) -> Response:
        body, readable = _read_body(request)
        language = _body_language(request, body, readable)
        auth = _require_auth(request, self.client_kind, language, require_terms=True)
        if isinstance(auth, Response):
            return auth
        user, raw_key = auth
        verdict = throttling.check_password_change(user.pk)
        if not verdict.allowed:
            return _limited(verdict, language)
        if not readable:
            return _unreadable(language)
        serializer = PasswordChangeSerializer(data=body)
        if not serializer.is_valid():
            return Response(
                {"errors": _render(serializer.errors, language)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        raw_new = serializer.validated_data.get("new_password")
        new_password = raw_new if isinstance(raw_new, str) else ""
        result = profile.change_password(
            user,
            current_password=serializer.validated_data["current_password"],
            new_password=new_password,
            current_session_key=raw_key,
            request=request._request,
            rotate_session_key=self.client_kind == "browser",
        )
        if isinstance(result, profile.PasswordChangeLocked):
            return _limited(
                throttling.Verdict(allowed=False, retry_after=result.retry_after), language
            )
        if isinstance(result, profile.PasswordChangeInvalid):
            return Response(
                {"errors": _password_change_errors(result, body, raw_new, language)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"result": "password_changed"}, status=status.HTTP_200_OK)


class BrowserPasswordChangeView(_BrowserCsrfMixin, AppPasswordChangeView):
    pass


class AppAccountDisableView(APIView):
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    client_kind: ClassVar[str] = "app"

    def post(self, request: Request) -> Response:
        body, readable = _read_body(request)
        language = _body_language(request, body, readable)
        auth = _require_auth(request, self.client_kind, language, require_terms=True)
        if isinstance(auth, Response):
            return auth
        user, _ = auth
        block_reason = disable.disable_block_reason(user)
        if block_reason is not None:
            return Response(
                {
                    "code": block_reason.value,
                    "message": messages.error_text(block_reason.value, language),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        verdict = throttling.check_account_disable(user.pk)
        if not verdict.allowed:
            return _limited(verdict, language)
        if not readable:
            return _unreadable(language)
        serializer = AccountDisableSerializer(data=body)
        if not serializer.is_valid():
            return Response(
                {"errors": _render(serializer.errors, language)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = disable.disable_account(
            user, current_password=serializer.validated_data["current_password"]
        )
        if isinstance(result, disable.DisableBlocked):
            return Response(
                {
                    "code": result.reason.value,
                    "message": messages.error_text(result.reason.value, language),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if isinstance(result, disable.DisableLocked):
            return _limited(
                throttling.Verdict(allowed=False, retry_after=result.retry_after), language
            )
        if isinstance(result, disable.DisableInvalid):
            return Response(
                {
                    "errors": {
                        "current_password": [
                            {
                                "code": "current_password_incorrect",
                                "message": messages.error_text(
                                    "current_password_incorrect", language
                                ),
                            }
                        ]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"result": "account_disabled"}, status=status.HTTP_200_OK)


class BrowserAccountDisableView(_BrowserCsrfMixin, AppAccountDisableView):
    pass
