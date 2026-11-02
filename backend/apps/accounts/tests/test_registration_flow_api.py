from datetime import timedelta
from typing import Any

import pytest
from allauth.account.models import EmailAddress
from django.test import Client, override_settings
from django.utils import timezone

from apps.accounts.api import messages
from apps.accounts.models import PendingRegistration, User
from apps.accounts.tests.factories import StartedWithCode, make_pending
from apps.consents.models import Terms
from apps.consents.tests.factories import publish_version

pytestmark = pytest.mark.django_db

VERIFY = "/api/{client}/v1/registration/verify"
RESEND = "/api/{client}/v1/registration/resend"
STATUS = "/api/{client}/v1/registration/status"
OPTIONS = "/api/{client}/v1/registration/options"
COMPLETE = "/api/{client}/v1/registration/complete"
GOOD_PASSWORD = "Kq7#mZ2!vR9p"


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


def _ready_to_resend() -> None:
    PendingRegistration.objects.update(last_sent_at=timezone.now() - timedelta(seconds=61))


def test_resend_from_the_app_is_accepted(started: StartedWithCode) -> None:
    _ready_to_resend()

    response = _app(RESEND, {"public_id": started.public_id})

    assert response.status_code == 202
    assert response.json() == {"result": "resent"}
    assert PendingRegistration.objects.get().resend_count == 1


def test_resend_from_the_browser_needs_csrf(csrf_client: Client, started: StartedWithCode) -> None:
    _ready_to_resend()
    rejected = csrf_client.post(
        RESEND.format(client="browser"),
        {"public_id": started.public_id},
        content_type="application/json",
    )

    accepted = _browser(csrf_client, RESEND, {"public_id": started.public_id})

    assert (rejected.status_code, accepted.status_code) == (403, 202)


def test_resend_too_soon_is_unavailable(started: StartedWithCode) -> None:
    response = _app(RESEND, {"public_id": started.public_id, "language": "pt-BR"})

    assert response.status_code == 400
    assert response.json() == {
        "code": "resend_unavailable",
        "message": messages.error_text("resend_unavailable", "pt-BR"),
    }


def test_resend_of_an_unknown_public_id_is_not_found() -> None:
    assert _app(RESEND, {"public_id": "a\x00b"}).status_code == 404
    assert _app(RESEND, {"public_id": "unknown"}).status_code == 404


def test_resend_without_public_id_is_a_bad_request() -> None:
    assert _app(RESEND, {}).status_code == 400


@override_settings(REGISTRATION_RATE_FLOW_IP_PER_HOUR=2)
def test_resend_and_verify_share_the_ip_limit(started: StartedWithCode) -> None:
    _app(VERIFY, {"public_id": started.public_id, "code": _wrong(started.code)})
    _app(RESEND, {"public_id": started.public_id})
    _ready_to_resend()

    response = _app(RESEND, {"public_id": started.public_id})

    assert response.status_code == 429
    assert PendingRegistration.objects.get().resend_count == 0


def test_status_from_the_app_reports_the_timers(started: StartedWithCode) -> None:
    response = _app(STATUS, {"public_id": started.public_id})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"code_expires_in", "resend_in", "resends_left", "locked", "expired"}
    assert 0 < body["code_expires_in"] <= 900 and 0 < body["resend_in"] <= 60
    assert (body["resends_left"], body["locked"], body["expired"]) == (5, False, False)


def test_status_from_the_browser_needs_csrf(csrf_client: Client, started: StartedWithCode) -> None:
    rejected = csrf_client.post(
        STATUS.format(client="browser"),
        {"public_id": started.public_id},
        content_type="application/json",
    )

    accepted = _browser(csrf_client, STATUS, {"public_id": started.public_id})

    assert (rejected.status_code, accepted.status_code) == (403, 200)


def test_status_of_an_unknown_public_id_is_not_found() -> None:
    assert _app(STATUS, {"public_id": "unknown"}).status_code == 404
    assert _app(STATUS, {"public_id": "x" * 500}).status_code == 404


@override_settings(REGISTRATION_RATE_FLOW_IP_PER_HOUR=2)
def test_status_does_not_count_for_the_ip_limit(started: StartedWithCode) -> None:
    statuses = [_app(STATUS, {"public_id": started.public_id}).status_code for _ in range(5)]

    assert statuses == [200] * 5
    assert _app(VERIFY, {"public_id": started.public_id, "code": started.code}).status_code == 200


def _document(document: Terms) -> dict[str, str]:
    return {"version": document.version, "locale": document.locale, "content": document.content}


def test_options_give_the_countries_and_the_documents_in_force_in_the_language() -> None:
    terms = publish_version(version="7")
    marketing = publish_version(kind=Terms.Kind.MARKETING, version="2")

    response = Client().get(OPTIONS.format(client="app"), {"language": "pt-BR"})

    assert response.status_code == 200
    body = response.json()
    assert "ES" in body["countries"] and body["countries"] == sorted(body["countries"])
    assert body["terms"] == _document(terms["pt-BR"])
    assert body["marketing"] == _document(marketing["pt-BR"])


def test_options_without_documents_in_force_give_null() -> None:
    body = Client().get(OPTIONS.format(client="app")).json()

    assert (body["terms"], body["marketing"]) == (None, None)


def test_options_language_falls_back_to_the_header() -> None:
    terms = publish_version(version="7")

    response = Client().get(OPTIONS.format(client="app"), headers={"Accept-Language": "en-US"})

    assert response.json()["terms"] == _document(terms["en"])


def test_browser_options_set_the_csrf_cookie_for_the_flow(csrf_client: Client) -> None:
    response = csrf_client.get(OPTIONS.format(client="browser"))

    assert response.status_code == 200
    assert "csrftoken" in response.cookies


def _validate(started: StartedWithCode) -> None:
    assert _app(VERIFY, {"public_id": started.public_id, "code": started.code}).status_code == 200


def _completion(started: StartedWithCode, **overrides: str) -> dict[str, str]:
    return {
        "public_id": started.public_id,
        "code": started.code,
        "password": GOOD_PASSWORD,
        **overrides,
    }


def test_complete_from_the_app_creates_the_account_with_a_verified_email(
    started: StartedWithCode,
) -> None:
    _validate(started)

    response = _app(COMPLETE, _completion(started))

    assert response.status_code == 201
    assert response.json() == {"result": "created"}
    user = User.objects.get(email="ana@example.com")
    assert user.check_password(GOOD_PASSWORD) and EmailAddress.objects.get(user=user).verified
    assert not PendingRegistration.objects.exists()


def test_complete_from_the_browser_needs_csrf(
    csrf_client: Client, started: StartedWithCode
) -> None:
    _validate(started)
    rejected = csrf_client.post(
        COMPLETE.format(client="browser"), _completion(started), content_type="application/json"
    )

    accepted = _browser(csrf_client, COMPLETE, _completion(started))

    assert (rejected.status_code, accepted.status_code) == (403, 201)


@pytest.mark.parametrize("validated", [True, False], ids=["validated", "not-validated"])
def test_complete_with_a_wrong_or_unvalidated_code_never_creates_the_account(
    started: StartedWithCode, validated: bool
) -> None:
    if validated:
        _validate(started)
    code = _wrong(started.code) if validated else started.code

    response = _app(COMPLETE, _completion(started, code=code))

    assert (response.status_code, response.json()["code"]) == (400, "wrong_code")
    assert not User.objects.filter(email="ana@example.com").exists()


def test_complete_without_the_code_is_a_bad_request(started: StartedWithCode) -> None:
    _validate(started)

    response = _app(COMPLETE, {"public_id": started.public_id, "password": GOOD_PASSWORD})

    assert response.status_code == 400 and "errors" in response.json()
    assert not User.objects.filter(email="ana@example.com").exists()


def test_a_weak_password_returns_each_rule_and_keeps_the_code(started: StartedWithCode) -> None:
    _validate(started)

    response = _app(COMPLETE, _completion(started, password="12345", language="en"))

    assert response.status_code == 400
    errors = response.json()["errors"]["password"]
    codes = {error["code"] for error in errors}
    assert {"password_too_short", "password_entirely_numeric"} <= codes
    short = next(error for error in errors if error["code"] == "password_too_short")
    assert short["message"] == messages.error_text(
        "password_too_short", "en", params={"min_length": 12}
    )
    assert _app(COMPLETE, _completion(started)).status_code == 201


def test_complete_with_an_unknown_public_id_is_not_found() -> None:
    body = {"public_id": "unknown", "code": "123456", "password": GOOD_PASSWORD}

    assert _app(COMPLETE, body).status_code == 404


@override_settings(REGISTRATION_RATE_FLOW_IP_PER_HOUR=1)
def test_complete_counts_for_the_ip_limit(started: StartedWithCode) -> None:
    _validate(started)

    response = _app(COMPLETE, _completion(started))

    assert response.status_code == 429
    assert not User.objects.filter(email="ana@example.com").exists()
