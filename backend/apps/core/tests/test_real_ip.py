import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from apps.core.middleware import RealClientIPMiddleware

TRUSTED_PROXY = "10.0.0.5"


def _capture_remote_addr(remote_addr: str, xff: str | None = None) -> str:
    captured: dict[str, str] = {}

    def get_response(request: HttpRequest) -> HttpResponse:
        captured["remote_addr"] = request.META["REMOTE_ADDR"]
        return HttpResponse()

    request = RequestFactory().get("/", REMOTE_ADDR=remote_addr)
    if xff is not None:
        request.META["HTTP_X_FORWARDED_FOR"] = xff
    RealClientIPMiddleware(get_response)(request)
    return captured["remote_addr"]


@pytest.fixture
def trusted_proxy(settings: object) -> None:
    settings.TRUSTED_PROXY_IPS = [TRUSTED_PROXY]  # type: ignore[attr-defined]


def test_real_ip_uses_last_forwarded_entry_from_trusted_proxy(trusted_proxy: None) -> None:
    assert _capture_remote_addr(TRUSTED_PROXY, "1.1.1.1, 2.2.2.2") == "2.2.2.2"


def test_forwarded_header_from_untrusted_connection_is_ignored(trusted_proxy: None) -> None:
    assert _capture_remote_addr("203.0.113.9", "1.1.1.1") == "203.0.113.9"


def test_without_forwarded_header_keeps_remote_addr(trusted_proxy: None) -> None:
    assert _capture_remote_addr(TRUSTED_PROXY) == TRUSTED_PROXY


def test_empty_trusted_list_ignores_forwarded_header_even_from_proxy_like_address(
    settings: object,
) -> None:
    settings.TRUSTED_PROXY_IPS = []  # type: ignore[attr-defined]
    assert _capture_remote_addr(TRUSTED_PROXY, "1.1.1.1") == TRUSTED_PROXY


def test_similar_but_different_address_is_not_trusted(trusted_proxy: None) -> None:
    assert _capture_remote_addr("10.0.0.50", "1.1.1.1") == "10.0.0.50"
