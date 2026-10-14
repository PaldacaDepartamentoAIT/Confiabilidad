from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse


class RealClientIPMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        trusted = {ip.strip() for ip in settings.TRUSTED_PROXY_IPS if ip.strip()}
        # Solo el proxy de entrada de confianza puede indicar la IP real (S-08, RF-015).
        if forwarded and request.META.get("REMOTE_ADDR") in trusted:
            request.META["REMOTE_ADDR"] = forwarded.split(",")[-1].strip()
        return self.get_response(request)
