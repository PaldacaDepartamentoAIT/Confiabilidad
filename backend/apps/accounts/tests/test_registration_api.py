from typing import Any

import pytest
from django.test import Client
from rest_framework import serializers

from apps.accounts.api import messages
from apps.accounts.api.serializers import RegistrationSerializer
from apps.accounts.models import PhantomProcess
from apps.accounts.tests.factories import make_user
from apps.consents.models import Terms
from apps.consents.tests.factories import publish_version

pytestmark = pytest.mark.django_db

BROWSER = "/api/browser/v1/registration"
APP = "/api/app/v1/registration"


@pytest.fixture(autouse=True)
def terms() -> dict[str, Terms]:
    return publish_version(version="1")


def _form(**overrides: Any) -> dict[str, Any]:
    form: dict[str, Any] = {
        "name": "Ana García",
        "birthdate": "1990-05-17",
        "email": "ana@example.com",
        "country": "ES",
        "terms": {"version": "1", "locale": "es", "accepted": True},
    }
    form.update(overrides)
    return form


def _browser_post(client: Client, form: dict[str, Any], **headers: str) -> Any:
    client.get("/_allauth/browser/v1/auth/session")
    token = client.cookies["csrftoken"].value
    return client.post(
        BROWSER, form, content_type="application/json", headers={"X-CSRFToken": token, **headers}
    )


def _app_post(form: dict[str, Any], **headers: str) -> Any:
    return Client().post(APP, form, content_type="application/json", headers=headers)


def test_valid_form_from_the_app_starts_the_registration() -> None:
    response = _app_post(_form(language="pt-BR"))

    assert response.status_code == 202
    slot = PhantomProcess.objects.get()
    assert response.json() == {
        "public_id": slot.public_id,
        "message": messages.neutral_text("pt-BR"),
    }
    assert slot.email == "ana@example.com"
    assert slot.payload == {
        "name": "Ana García",
        "birthdate": "1990-05-17",
        "country": "ES",
        "language": "pt-BR",
        "terms_version": "1",
        "terms_locale": "es",
    }


def test_valid_form_from_the_browser_with_csrf_starts_the_registration(csrf_client: Client) -> None:
    response = _browser_post(csrf_client, _form())

    assert response.status_code == 202
    assert response.json()["public_id"] == PhantomProcess.objects.get().public_id


def test_browser_without_csrf_is_rejected_without_starting(csrf_client: Client) -> None:
    response = csrf_client.post(BROWSER, _form(), content_type="application/json")

    assert response.status_code == 403
    assert not PhantomProcess.objects.exists()


def test_app_needs_neither_csrf_nor_origin() -> None:
    response = Client(enforce_csrf_checks=True).post(APP, _form(), content_type="application/json")

    assert response.status_code == 202


def test_invalid_form_returns_every_error_with_code_and_text() -> None:
    response = _app_post(
        _form(name="", email="ana@localhost", country="XX", terms={"accepted": False})
    )

    assert response.status_code == 400
    assert response.json() == {
        "errors": {
            "name": [{"code": "blank", "message": messages.error_text("blank", "es")}],
            "email": [
                {
                    "code": "email_domain_without_dot",
                    "message": messages.error_text("email_domain_without_dot", "es"),
                }
            ],
            "country": [
                {"code": "country_invalid", "message": messages.error_text("country_invalid", "es")}
            ],
            "terms": [
                {
                    "code": "terms_not_accepted",
                    "message": messages.error_text("terms_not_accepted", "es"),
                },
                {"code": "required", "message": messages.error_text("required", "es")},
            ],
        }
    }
    assert not PhantomProcess.objects.exists()


def test_error_texts_follow_the_request_language() -> None:
    response = _app_post(_form(name="a" * 151, birthdate="x"), **{"Accept-Language": "en-GB"})

    errors = response.json()["errors"]
    assert errors["name"] == [
        {
            "code": "name_too_long",
            "message": messages.error_text("name_too_long", "en", params={"max": 150}),
        }
    ]
    assert errors["birthdate"] == [
        {"code": "invalid", "message": messages.error_text("invalid", "en", field="birthdate")}
    ]


def test_minimum_age_text_carries_its_parameters() -> None:
    response = _app_post(_form(birthdate="2020-01-01", language="es"))

    message = response.json()["errors"]["birthdate"][0]["message"]
    assert message == messages.error_text(
        "birthdate_under_minimum_age", "es", params={"years": 18, "days": 5}
    )


def test_non_object_body_is_rejected() -> None:
    response = Client().post(APP, ["x"], content_type="application/json")

    assert response.status_code == 400
    assert response.json()["errors"]["non_field_errors"][0]["code"] == "invalid"


def test_signed_in_session_does_not_change_the_response() -> None:
    client = Client()
    client.force_login(make_user(email="otra@example.com"))

    response = client.post(APP, _form(), content_type="application/json")

    assert response.status_code == 202
    assert set(response.json()) == {"public_id", "message"}
    assert PhantomProcess.objects.get().email == "ana@example.com"


@pytest.mark.parametrize("field", ["name", "email", "country"])
@pytest.mark.parametrize(
    ("character", "code"),
    [("\u0000", "null_characters_not_allowed"), ("\ud800", "surrogate_characters_not_allowed")],
)
@pytest.mark.parametrize("language", ["es", "pt-BR", "en"])
def test_forbidden_characters_are_reported_in_their_field(
    field: str, character: str, code: str, language: str
) -> None:
    value = {"name": "Ana", "email": "ana@example.com", "country": "ES"}[field]
    response = _app_post(_form(**{field: value + character}, language=language))

    assert response.status_code == 400
    errors = response.json()["errors"][field]
    assert {"code": code, "message": messages.error_text(code, language)} in errors


def test_unknown_error_code_gets_the_generic_text_instead_of_failing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def odd_country(self: RegistrationSerializer, value: str) -> str:
        raise serializers.ValidationError("odd", code="no_such_code")

    monkeypatch.setattr(RegistrationSerializer, "validate_country", odd_country)

    response = _app_post(_form())

    assert response.status_code == 400
    assert response.json()["errors"]["country"] == [
        {"code": "no_such_code", "message": messages.error_text("invalid", "es")}
    ]


NON_JSON_BODIES = [
    ("application/x-www-form-urlencoded", "name=Ana&email=ana%40example.com"),
    (
        "multipart/form-data; boundary=x",
        '--x\r\nContent-Disposition: form-data; name="name"\r\n\r\nAna\r\n--x--\r\n',
    ),
    ("text/plain", '{"name": "Ana"}'),
]


@pytest.mark.parametrize(("content_type", "body"), NON_JSON_BODIES)
def test_app_route_accepts_only_json(content_type: str, body: str) -> None:
    response = Client().post(APP, body, content_type=content_type)

    assert response.status_code == 400
    assert response.json()["errors"]["non_field_errors"][0]["code"] == "invalid"
    assert not PhantomProcess.objects.exists()


@pytest.mark.parametrize(("content_type", "body"), NON_JSON_BODIES)
def test_browser_route_accepts_only_json(csrf_client: Client, content_type: str, body: str) -> None:
    csrf_client.get("/_allauth/browser/v1/auth/session")
    token = csrf_client.cookies["csrftoken"].value
    response = csrf_client.post(
        BROWSER, body, content_type=content_type, headers={"X-CSRFToken": token}
    )

    assert response.status_code == 400
    assert response.json()["errors"]["non_field_errors"][0]["code"] == "invalid"
    assert not PhantomProcess.objects.exists()
