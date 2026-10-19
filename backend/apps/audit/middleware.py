from collections.abc import Callable
from contextvars import ContextVar

from django.http import HttpRequest, HttpResponse

_current_request: ContextVar[HttpRequest | None] = ContextVar("audit_current_request", default=None)


def current_request() -> HttpRequest | None:
    return _current_request.get()


class CurrentRequestMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        token = _current_request.set(request)
        try:
            return self.get_response(request)
        finally:
            _current_request.reset(token)
