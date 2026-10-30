from typing import Any

import pytest
from django.test import Client, override_settings

from apps.accounts.api import messages
from apps.accounts.models import PendingRegistration
from apps.accounts.tests.factories import StartedWithCode, make_pending

pytestmark = pytest.mark.django_db

VERIFY = "/api/{client}/v1/registration/verify"


def _wrong(code: str) -> str:
    return "000000" if code != "000000" else "111111"


def _app(path: str, body: Any, **headers: str) -> Any:
    return Client().post(
        path.format(client="app"), body, content_type="application/json", headers=headers
    )


def _browser(client: Client, path: str, body: Any) -> Any:
    client.get("/_allauth/browser/v1/auth/session")
    token = client.cookies["csrftoken"].value
    return client.post(
        path.format(client="browser"),
        body,
        content_type="application/json",
        headers={"X-CSRFToken": token},
    )


@pytest.fixture
def started() -> StartedWithCode:
    return make_pending("ana@example.com")


def test_right_code_from_the_app_is_verified(started: StartedWithCode) -> None:
    response = _app(VERIFY, {"public_id": started.public_id, "code": started.code})

    assert response.status_code == 200
    assert response.json() == {"result": "verified"}
    assert PendingRegistration.objects.get().code_validated_at is not None


def test_right_code_from_the_browser_with_csrf_is_verified(
    csrf_client: Client, started: StartedWithCode
) -> None:
    response = _browser(csrf_client, VERIFY, {"public_id": started.public_id, "code": started.code})

    assert response.status_code == 200


def test_browser_without_csrf_is_rejected(csrf_client: Client, started: StartedWithCode) -> None:
    response = csrf_client.post(
        VERIFY.format(client="browser"),
        {"public_id": started.public_id, "code": started.code},
        content_type="application/json",
    )

    assert response.status_code == 403
    assert PendingRegistration.objects.get().code_validated_at is None


@pytest.mark.parametrize("language", ["es", "pt-BR", "en"])
def test_wrong_code_is_rejected_with_its_text(started: StartedWithCode, language: str) -> None:
    body = {"public_id": started.public_id, "code": _wrong(started.code), "language": language}

    response = _app(VERIFY, body)

    assert response.status_code == 400
    assert response.json() == {
        "code": "wrong_code",
        "message": messages.error_text("wrong_code", language),
    }
    assert PendingRegistration.objects.get().failed_attempts == 1


def test_language_falls_back_to_the_header(started: StartedWithCode) -> None:
    body = {"public_id": started.public_id, "code": _wrong(started.code)}

    response = _app(VERIFY, body, **{"Accept-Language": "en-GB"})

    assert response.json()["message"] == messages.error_text("wrong_code", "en")


def test_locked_registration_is_rejected(started: StartedWithCode) -> None:
    PendingRegistration.objects.update(failed_attempts=5)

    response = _app(VERIFY, {"public_id": started.public_id, "code": started.code})

    assert (response.status_code, response.json()["code"]) == (400, "locked")


@pytest.mark.parametrize(
    "public_id", ["unknown", "", "x" * 500, "a\x00b", "\ud800", "../../etc/passwd"]
)
def test_unknown_public_id_of_any_format_is_not_found(public_id: str) -> None:
    response = _app(VERIFY, {"public_id": public_id, "code": "123456"})

    assert response.status_code == 404
    assert response.json() == {
        "code": "not_found",
        "message": messages.error_text("not_found", "es"),
    }


@pytest.mark.parametrize(
    "body",
    [
        {"code": "123456"},
        {"public_id": "abc"},
        {"public_id": 1, "code": "123456"},
        {"public_id": "abc", "code": ["1"]},
        ["abc", "123456"],
    ],
)
def test_malformed_request_is_a_bad_request(body: Any) -> None:
    response = _app(VERIFY, body)

    assert response.status_code == 400
    assert "errors" in response.json()


def test_unreadable_body_is_a_bad_request_never_a_server_error() -> None:
    response = Client().post(
        VERIFY.format(client="app"), "[" * 100_000, content_type="application/json"
    )

    assert response.status_code == 400


@override_settings(REGISTRATION_RATE_FLOW_IP_PER_HOUR=2)
def test_too_many_requests_from_an_ip_are_rejected_without_evaluating(
    started: StartedWithCode,
) -> None:
    body = {"public_id": started.public_id, "code": _wrong(started.code)}
    for _ in range(2):
        assert _app(VERIFY, body).status_code == 400

    response = _app(VERIFY, {"public_id": started.public_id, "code": started.code})

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    assert response.json()["retry_after"] == int(response.headers["Retry-After"])
    assert PendingRegistration.objects.get().code_validated_at is None
