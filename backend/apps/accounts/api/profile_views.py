from typing import Any, ClassVar

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import profile
from apps.accounts.api.auth_views import _body_language, _BrowserCsrfMixin, _require_auth
from apps.accounts.api.language import request_language
from apps.accounts.api.profile_serializers import ProfileUpdateSerializer
from apps.accounts.api.views import _read_body, _render, _unreadable


def _profile_payload(data: profile.ProfileData) -> dict[str, str]:
    return {
        "email": data.email,
        "name": data.name,
        "birthdate": data.birthdate.isoformat(),
        "country": data.country,
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
        return Response(_profile_payload(profile.get_profile(user)), status=status.HTTP_200_OK)

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
        return Response(_profile_payload(updated), status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name="get")
class BrowserProfileView(_BrowserCsrfMixin, AppProfileView):
    pass
