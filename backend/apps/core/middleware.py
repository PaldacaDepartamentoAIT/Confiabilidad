from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class RealClientIPMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            # Un único proxy de confianza: la última entrada es la IP real del cliente (S-08).
            request.META["REMOTE_ADDR"] = forwarded.split(",")[-1].strip()
        return self.get_response(request)
