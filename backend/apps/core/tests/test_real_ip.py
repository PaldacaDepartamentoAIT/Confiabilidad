from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from apps.core.middleware import RealClientIPMiddleware


def _capture_remote_addr(xff: str | None = None) -> str:
    captured: dict[str, str] = {}

    def get_response(request: HttpRequest) -> HttpResponse:
        captured["remote_addr"] = request.META["REMOTE_ADDR"]
        return HttpResponse()

    request = RequestFactory().get("/")
    if xff is not None:
        request.META["HTTP_X_FORWARDED_FOR"] = xff
    RealClientIPMiddleware(get_response)(request)
    return captured["remote_addr"]


def test_real_ip_uses_last_forwarded_entry() -> None:
    assert _capture_remote_addr("1.1.1.1, 2.2.2.2") == "2.2.2.2"


def test_real_ip_without_forwarded_header_keeps_remote_addr() -> None:
    assert _capture_remote_addr() == "127.0.0.1"
