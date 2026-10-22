from datetime import date, timedelta
from typing import Any

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts import registration
from apps.accounts.api import messages
from apps.accounts.api.serializers import RegistrationSerializer
from apps.accounts.models import PendingRegistration
from apps.accounts.tests.factories import make_user
from apps.consents.models import Terms
from apps.consents.tests.factories import make_document, publish_version
from apps.emails.models import OutboundEmail

pytestmark = pytest.mark.django_db


def _data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": "  Ana García ",
        "birthdate": "1990-05-17",
        "email": " ana@example.com ",
        "country": "es",
        "terms": {"version": "1", "locale": "es", "accepted": True},
    }
    data.update(overrides)
    return data


def _codes(serializer: RegistrationSerializer) -> dict[str, list[str]]:
    assert not serializer.is_valid()
    return {field: [error.code for error in errors] for field, errors in serializer.errors.items()}


@pytest.fixture
def terms() -> dict[str, Terms]:
    return publish_version(version="1")


def test_valid_form_returns_normalized_data_and_document(terms: dict[str, Terms]) -> None:
    serializer = RegistrationSerializer(data=_data(language="pt_BR"))
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data == {
        "name": "Ana García",
        "birthdate": date(1990, 5, 17),
        "email": "ana@example.com",
        "country": "ES",
        "terms": {"version": "1", "locale": "es"},
        "language": "pt_BR",
    }


def test_language_is_optional(terms: dict[str, Terms]) -> None:
    serializer = RegistrationSerializer(data=_data())
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["language"] is None


@pytest.mark.parametrize("field", ["name", "birthdate", "email", "country", "terms"])
def test_missing_field_is_required(terms: dict[str, Terms], field: str) -> None:
    data = _data()
    del data[field]
    assert _codes(RegistrationSerializer(data=data)) == {field: ["required"]}


@pytest.mark.parametrize("field", ["name", "birthdate", "email", "country", "terms"])
def test_null_field_is_rejected(terms: dict[str, Terms], field: str) -> None:
    assert _codes(RegistrationSerializer(data=_data(**{field: None}))) == {field: ["null"]}


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"name": "   "}, {"name": ["blank"]}),
        (
            {"name": "Ana\tGarcía  " + "a" * 150},
            {"name": ["name_too_long", "name_control_char", "name_consecutive_spaces"]},
        ),
        ({"birthdate": "17/05/1990"}, {"birthdate": ["invalid"]}),
        (
            {"birthdate": (timezone.localdate() + timedelta(days=1)).isoformat()},
            {"birthdate": ["birthdate_in_future"]},
        ),
        (
            {"birthdate": (timezone.localdate() - timedelta(days=365 * 18)).isoformat()},
            {"birthdate": ["birthdate_under_minimum_age"]},
        ),
        ({"country": "XX"}, {"country": ["country_invalid"]}),
        ({"email": "ana"}, {"email": ["invalid"]}),
        ({"email": "ana@localhost"}, {"email": ["email_domain_without_dot"]}),
        ({"email": "ana@[192.0.2.1]"}, {"email": ["email_ip_domain"]}),
        ({"terms": "1"}, {"terms": ["invalid"]}),
    ],
)
def test_invalid_field_reports_its_codes(
    terms: dict[str, Terms], overrides: dict[str, Any], expected: dict[str, list[str]]
) -> None:
    assert _codes(RegistrationSerializer(data=_data(**overrides))) == expected


def test_every_invalid_field_is_reported_at_once(terms: dict[str, Terms]) -> None:
    data = _data(name="", birthdate="x", email="ana@localhost", country="XX", terms={})
    codes = _codes(RegistrationSerializer(data=data))
    assert set(codes) == {"name", "birthdate", "email", "country", "terms"}


@pytest.mark.parametrize("accepted", [None, False, "true", 1])
def test_terms_without_explicit_acceptance_are_rejected(
    terms: dict[str, Terms], accepted: object
) -> None:
    document: dict[str, object] = {"version": "1", "locale": "es"}
    if accepted is not None:
        document["accepted"] = accepted
    assert _codes(RegistrationSerializer(data=_data(terms=document))) == {
        "terms": ["terms_not_accepted"]
    }


@pytest.mark.parametrize("document", [{"accepted": True}, {"version": "1", "accepted": True}])
def test_terms_without_document_are_required(
    terms: dict[str, Terms], document: dict[str, object]
) -> None:
    assert _codes(RegistrationSerializer(data=_data(terms=document))) == {"terms": ["required"]}


def test_missing_acceptance_and_document_are_both_reported(terms: dict[str, Terms]) -> None:
    assert _codes(RegistrationSerializer(data=_data(terms={"accepted": False}))) == {
        "terms": ["terms_not_accepted", "required"]
    }


def test_each_document_mismatch_has_its_code() -> None:
    def terms_codes(version: str) -> list[str]:
        document = {"version": version, "locale": "es", "accepted": True}
        return _codes(RegistrationSerializer(data=_data(terms=document)))["terms"]

    assert terms_codes("9") == ["document_not_found"]
    publish_version(kind=Terms.Kind.MARKETING, version="m1")
    assert terms_codes("m1") == ["wrong_kind"]
    make_document(version="draft", locale="es")
    assert terms_codes("draft") == ["no_current_version"]
    publish_version(version="old", published_at=timezone.now() - timedelta(days=3))
    publish_version(version="new")
    assert terms_codes("old") == ["not_current_document"]


def test_document_in_another_language_is_accepted(terms: dict[str, Terms]) -> None:
    document = {"version": "1", "locale": "en", "accepted": True}
    serializer = RegistrationSerializer(data=_data(terms=document, language="pt-BR"))
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["terms"] == {"version": "1", "locale": "en"}


def test_validation_does_not_look_at_accounts_or_pending_registrations(
    terms: dict[str, Terms],
) -> None:
    with CaptureQueriesContext(connection) as queries:
        assert RegistrationSerializer(data=_data()).is_valid()
    tables = " ".join(query["sql"] for query in queries.captured_queries)
    assert "accounts_" not in tables


def test_every_emitted_code_is_in_the_catalog() -> None:
    publish_version(version="1")
    data = _data(name="", birthdate="x", email="ana@[1.2.3.4]", country="XX", terms={})
    del data["name"]
    serializer = RegistrationSerializer(data=data)
    assert not serializer.is_valid()
    emitted = {error.code for errors in serializer.errors.values() for error in errors}
    assert emitted <= set(messages.ERRORS)


def test_email_longer_than_254_characters_is_rejected_in_its_field(
    terms: dict[str, Terms],
) -> None:
    for email in (
        "a" * 250 + "@example.com",
        "a" * 64 + "@" + "b" * 63 + "." + "c" * 63 + "." + "d" * 58 + ".com",
    ):
        assert _codes(RegistrationSerializer(data=_data(email=email))) == {"email": ["max_length"]}
    assert "max_length" in messages.ERRORS


def test_email_of_254_characters_is_accepted(terms: dict[str, Terms]) -> None:
    email = "a" * 64 + "@" + "b" * 63 + "." + "c" * 63 + "." + "d" * 57 + ".com"
    assert len(email) == 254
    serializer = RegistrationSerializer(data=_data(email=email))
    assert serializer.is_valid(), serializer.errors


def test_email_with_dotted_capital_i_is_rejected_in_its_field(terms: dict[str, Terms]) -> None:
    codes = _codes(RegistrationSerializer(data=_data(email="İnci@example.com")))
    assert list(codes) == ["email"]
    assert set(codes["email"]) <= set(messages.ERRORS)


def test_email_length_is_checked_after_lowercasing(terms: dict[str, Terms]) -> None:
    email = "a" * 64 + "@" + "İ" + "b" * 62 + "." + "c" * 63 + "." + "d" * 57 + ".com"
    assert len(email) == 254
    codes = _codes(RegistrationSerializer(data=_data(email=email)))
    assert "max_length" in codes["email"]


def test_validated_email_is_the_normalized_one(terms: dict[str, Terms]) -> None:
    serializer = RegistrationSerializer(data=_data(email="  Ana@Example.COM "))
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["email"] == "ana@example.com"


@pytest.mark.parametrize("key", ["version", "locale"])
@pytest.mark.parametrize(
    ("character", "code"),
    [("\u0000", "null_characters_not_allowed"), ("\ud800", "surrogate_characters_not_allowed")],
)
def test_forbidden_characters_in_the_terms_document_are_rejected(
    terms: dict[str, Terms], key: str, character: str, code: str
) -> None:
    document: dict[str, object] = {"version": "1", "locale": "es", "accepted": True}
    document[key] = f"{document[key]}{character}"
    assert _codes(RegistrationSerializer(data=_data(terms=document))) == {"terms": [code]}


@pytest.mark.parametrize(
    ("email", "canonical"),
    [
        ("ana@ｅxample.com", "ana@example.com"),
        ('"ana"@example.com', "ana@example.com"),
        ('"Ana.Lopez"@Example.com', "ana.lopez@example.com"),
        ("ana@xn--espaa-rta.es", "ana@españa.es"),
        ('"a..b"@example.com', '"a..b"@example.com'),
        ('"\\ana"@example.com', "ana@example.com"),
        ('"an\\a"@example.com', "ana@example.com"),
        ('"a\\ b"@example.com', '"a\\ b"@example.com'),
        ("ana@example.com", "ana@example.com"),
        ("ana+etiqueta@españa.es", "ana+etiqueta@españa.es"),
    ],
)
def test_email_is_turned_into_its_canonical_form(
    terms: dict[str, Terms], email: str, canonical: str
) -> None:
    serializer = RegistrationSerializer(data=_data(email=email))
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["email"] == canonical


def test_variant_of_an_email_with_an_account_gets_the_account_notice(
    terms: dict[str, Terms],
) -> None:
    make_user(email="ana@example.com")
    serializer = RegistrationSerializer(data=_data(email="ana@ｅxample.com"))
    assert serializer.is_valid(), serializer.errors
    data = serializer.validated_data

    started = registration.start(
        email=data["email"], name=data["name"], birthdate=data["birthdate"], country=data["country"]
    )
    registration.resolve_registration(started.public_id)

    assert not PendingRegistration.objects.exists()
    assert (
        OutboundEmail.objects.filter(kind="account_exists", recipient="ana@example.com").count()
        == 1
    )


def test_escaped_variant_of_an_email_with_an_account_gets_the_account_notice(
    terms: dict[str, Terms],
) -> None:
    make_user(email="ana@example.com")
    serializer = RegistrationSerializer(data=_data(email='"\\ana"@example.com'))
    assert serializer.is_valid(), serializer.errors
    data = serializer.validated_data

    started = registration.start(
        email=data["email"], name=data["name"], birthdate=data["birthdate"], country=data["country"]
    )
    registration.resolve_registration(started.public_id)

    assert not PendingRegistration.objects.exists()
    assert (
        OutboundEmail.objects.filter(kind="account_exists", recipient="ana@example.com").count()
        == 1
    )
