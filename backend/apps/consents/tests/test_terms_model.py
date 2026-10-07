from datetime import timedelta
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.consents.models import Terms

pytestmark = pytest.mark.django_db


def _document(**overrides: Any) -> Terms:
    fields: dict[str, Any] = {
        "kind": Terms.Kind.TERMS,
        "content": "# Terms\n\nText.",
        "version": "1",
        "locale": "es",
    }
    fields.update(overrides)
    return Terms(**fields)


def test_document_keeps_every_field() -> None:
    published_at = timezone.now() - timedelta(days=1)
    before = timezone.now()

    document = _document(
        kind=Terms.Kind.MARKETING,
        content="Marketing **text**.",
        version="2.1",
        locale="pt-BR",
        published_at=published_at,
    )
    document.save()
    document.refresh_from_db()

    assert document.kind == "marketing"
    assert document.content == "Marketing **text**."
    assert document.version == "2.1"
    assert document.locale == "pt-BR"
    assert document.published_at == published_at
    assert document.created_at >= before


def test_publication_date_is_optional() -> None:
    document = _document()
    document.save()

    assert document.published_at is None


def test_kinds_are_terms_and_marketing() -> None:
    assert set(Terms.Kind.values) == {"terms", "marketing"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("locale", "fr"),
        ("locale", "pt"),
        ("version", "1 0"),
        ("version", ""),
        ("content", "<p>Text</p>"),
        ("content", "  "),
        ("kind", "privacy"),
    ],
)
def test_invalid_field_is_rejected_on_save(field: str, value: str) -> None:
    with pytest.raises(ValidationError) as error:
        _document(**{field: value}).save()

    assert field in error.value.error_dict
    assert not Terms.objects.exists()


@pytest.mark.parametrize("version", ["v1", "V1"])
def test_same_version_ignoring_case_is_rejected(version: str) -> None:
    _document(version="V1").save()

    with pytest.raises(ValidationError):
        _document(version=version).save()


def test_same_version_ignoring_case_is_rejected_in_bulk() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Terms.objects.bulk_create([_document(version="V1"), _document(version="v1")])


@pytest.mark.parametrize(
    "other",
    [{"locale": "en"}, {"kind": Terms.Kind.MARKETING}, {"version": "2"}],
)
def test_same_version_in_another_locale_or_kind_is_allowed(other: dict[str, str]) -> None:
    _document().save()
    _document(**other).save()

    assert Terms.objects.count() == 2


def test_document_text_shows_kind_version_and_locale() -> None:
    assert str(_document(version="2", locale="en")) == "terms 2 (en)"


def test_terms_document_requires_reacceptance_by_default() -> None:
    document = _document()
    document.save()

    assert document.requires_reacceptance is True


def test_marketing_document_never_requires_reacceptance() -> None:
    document = _document(kind=Terms.Kind.MARKETING, requires_reacceptance=True)
    document.save()
    document.refresh_from_db()

    assert document.requires_reacceptance is False


def test_terms_document_with_another_reacceptance_than_its_version_is_rejected() -> None:
    _document(version="V2", locale="es", requires_reacceptance=False).save()

    with pytest.raises(ValidationError) as error:
        _document(version="v2", locale="en", requires_reacceptance=True).save()

    assert "requires_reacceptance" in error.value.error_dict


def test_changing_reacceptance_against_its_version_is_rejected() -> None:
    _document(locale="es").save()
    english = _document(locale="en")
    english.save()

    english.requires_reacceptance = False
    with pytest.raises(ValidationError):
        english.save()


def test_same_reacceptance_in_every_locale_is_allowed() -> None:
    for locale in ("es", "pt-BR", "en"):
        _document(locale=locale, requires_reacceptance=False).save()

    assert Terms.objects.filter(requires_reacceptance=False).count() == 3


def test_other_versions_and_marketing_do_not_constrain_reacceptance() -> None:
    _document(version="1", requires_reacceptance=False).save()
    _document(kind=Terms.Kind.MARKETING, version="2", locale="en").save()

    _document(version="2", locale="en", requires_reacceptance=True).save()

    assert Terms.objects.count() == 3


def test_changing_reacceptance_of_a_document_without_other_languages_is_allowed() -> None:
    document = _document()
    document.save()

    document.requires_reacceptance = False
    document.save()

    assert Terms.objects.get().requires_reacceptance is False
