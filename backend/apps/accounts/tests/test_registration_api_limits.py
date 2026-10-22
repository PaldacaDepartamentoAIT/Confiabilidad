from typing import Any

import pytest
from django.test import Client, override_settings

from apps.accounts.api import messages
from apps.accounts.models import PhantomProcess
from apps.consents.models import Terms
from apps.consents.tests.factories import publish_version

pytestmark = pytest.mark.django_db

APP = "/api/app/v1/registration"
BROWSER = "/api/browser/v1/registration"


@pytest.fixture(autouse=True)
def terms() -> dict[str, Terms]:
    return publish_version(version="1")


def _form(email: str = "ana@example.com", **overrides: Any) -> dict[str, Any]:
    form: dict[str, Any] = {
        "name": "Ana García",
        "birthdate": "1990-05-17",
        "email": email,
        "country": "ES",
        "terms": {"version": "1", "locale": "es", "accepted": True},
    }
    form.update(overrides)
    return form


def _post(form: Any, ip: str = "192.0.2.1", **headers: str) -> Any:
    return Client(REMOTE_ADDR=ip).post(APP, form, content_type="application/json", headers=headers)


def _assert_limited(response: Any, language: str = "es") -> None:
    assert response.status_code == 429
    body = response.json()
    assert set(body) == {"message", "retry_after"}
    assert body["retry_after"] > 0
    assert response.headers["Retry-After"] == str(body["retry_after"])
    assert body["message"] == messages.rate_limited_text(language, seconds=body["retry_after"])


@override_settings(REGISTRATION_RATE_IP_PER_HOUR=2)
def test_ip_over_its_limit_is_rejected_before_validating() -> None:
    assert _post(_form("a@example.com")).status_code == 202
    assert _post(_form(country="XX")).status_code == 400

    _assert_limited(_post(_form("b@example.com")))
    _assert_limited(_post(["not", "a", "form"]))
    assert PhantomProcess.objects.count() == 1
    assert _post(_form("b@example.com"), ip="198.51.100.7").status_code == 202


def test_same_email_and_ip_within_the_interval_is_rejected_after_validating() -> None:
    assert _post(_form()).status_code == 202

    assert _post(_form(country="XX")).status_code == 400
    _assert_limited(_post(_form(), **{"Accept-Language": "en"}), language="en")
    assert PhantomProcess.objects.count() == 1


def test_invalid_request_does_not_count_for_the_email() -> None:
    assert _post(_form(country="XX")).status_code == 400
    assert _post(_form()).status_code == 202


@override_settings(REGISTRATION_RATE_IP_PER_HOUR=2)
def test_request_rejected_by_the_email_limit_does_not_count_for_the_ip() -> None:
    assert _post(_form()).status_code == 202
    for _attempt in range(5):
        _assert_limited(_post(_form()))
    assert _post(_form("b@example.com")).status_code == 202


@override_settings(REGISTRATION_RATE_IP_PER_HOUR=1)
def test_request_rejected_for_csrf_does_not_count() -> None:
    browser = Client(enforce_csrf_checks=True, REMOTE_ADDR="192.0.2.1")
    assert browser.post(BROWSER, _form(), content_type="application/json").status_code == 403
    assert _post(_form()).status_code == 202


@override_settings(REGISTRATION_RATE_IP_PER_HOUR=1)
@pytest.mark.parametrize(
    ("body", "content_type"),
    [("{not json", "application/json"), ("name=Ana", "text/plain")],
)
def test_unreadable_body_over_the_ip_limit_gets_the_same_429(body: str, content_type: str) -> None:
    assert _post(_form()).status_code == 202

    response = Client(REMOTE_ADDR="192.0.2.1").post(
        APP, body, content_type=content_type, headers={"Accept-Language": "en"}
    )

    _assert_limited(response, language="en")


@override_settings(REGISTRATION_RATE_IP_PER_HOUR=1)
@pytest.mark.parametrize(
    ("body", "content_type"),
    [("{not json", "application/json"), ("name=Ana", "text/plain")],
)
def test_unreadable_body_counts_for_the_ip_and_reports_an_invalid_body(
    body: str, content_type: str
) -> None:
    response = Client(REMOTE_ADDR="192.0.2.1").post(
        APP, body, content_type=content_type, headers={"Accept-Language": "pt-BR"}
    )

    assert response.status_code == 400
    assert response.json() == {
        "errors": {
            "non_field_errors": [
                {"code": "invalid", "message": messages.error_text("invalid", "pt-BR")}
            ]
        }
    }
    _assert_limited(_post(_form()))
