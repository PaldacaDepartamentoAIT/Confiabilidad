from datetime import timedelta
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.tests.factories import make_user
from apps.consents.models import MarketingConsent, Terms, UserTerms
from apps.consents.tests.factories import publish_version

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


def _accept(document: Terms, *, revoked: bool = False) -> None:
    revoked_at = timezone.now() if revoked else None
    if document.kind == Terms.Kind.TERMS:
        UserTerms(user=make_user(), terms=document, revoked_at=revoked_at).save()
    else:
        MarketingConsent(
            user=make_user(), terms=document, granted=not revoked, revoked_at=revoked_at
        ).save()


PROTECTED_CHANGES = [
    ("content", "Another text."),
    ("version", "9"),
    ("locale", "en"),
    ("kind", Terms.Kind.MARKETING),
    ("published_at", None),
    ("requires_reacceptance", False),
]


@pytest.mark.parametrize(("field", "value"), PROTECTED_CHANGES)
@pytest.mark.parametrize("kind", [Terms.Kind.TERMS, Terms.Kind.MARKETING])
def test_protected_fields_of_an_accepted_document_cannot_change(
    kind: str, field: str, value: object
) -> None:
    if field == "kind":
        value = Terms.Kind.TERMS if kind == Terms.Kind.MARKETING else Terms.Kind.MARKETING
    if field == "requires_reacceptance" and kind == Terms.Kind.MARKETING:
        pytest.skip("marketing documents never require re-acceptance")
    documents = publish_version(kind=kind)
    _accept(documents["es"])

    document = Terms.objects.get(pk=documents["es"].pk)
    setattr(document, field, value)
    with pytest.raises(ValidationError) as error:
        document.save()

    assert error.value.messages == [
        "This version has acceptances; its documents cannot be changed or deleted."
    ]


@pytest.mark.parametrize(("field", "value"), PROTECTED_CHANGES)
def test_every_document_of_an_accepted_version_is_locked(field: str, value: object) -> None:
    documents = publish_version()
    _accept(documents["es"])

    sibling = Terms.objects.get(pk=documents["pt-BR"].pk)
    setattr(sibling, field, value)
    with pytest.raises(ValidationError):
        sibling.save()


def test_a_revoked_acceptance_also_locks_the_version() -> None:
    documents = publish_version(kind=Terms.Kind.MARKETING)
    _accept(documents["en"], revoked=True)

    documents["en"].content = "Changed."
    with pytest.raises(ValidationError):
        documents["en"].save()


@pytest.mark.parametrize("locale", ["es", "en"])
def test_documents_of_an_accepted_version_cannot_be_deleted(locale: str) -> None:
    documents = publish_version()
    _accept(documents["es"])

    with pytest.raises(ValidationError):
        documents[locale].delete()

    assert Terms.objects.count() == 3


def test_saving_an_accepted_document_without_changes_is_allowed() -> None:
    documents = publish_version()
    _accept(documents["es"])

    Terms.objects.get(pk=documents["es"].pk).save()


def test_a_version_without_acceptances_can_be_edited_and_deleted() -> None:
    documents = publish_version()
    _accept(publish_version()["es"])

    documents["es"].content = "Changed."
    documents["es"].save()
    documents["en"].delete()

    assert Terms.objects.get(pk=documents["es"].pk).content == "Changed."
    assert not Terms.objects.filter(pk=documents["en"].pk).exists()


def test_accepted_version_reports_its_lock() -> None:
    accepted, free = publish_version(), publish_version()
    _accept(accepted["es"])

    assert accepted["en"].has_acceptances() is True
    assert free["en"].has_acceptances() is False


def test_an_accepted_version_of_another_kind_does_not_lock() -> None:
    terms = publish_version(version="1")
    _accept(publish_version(kind=Terms.Kind.MARKETING, version="1")["es"])

    terms["es"].content = "Changed."
    terms["es"].save()

    assert terms["es"].has_acceptances() is False


def test_versions_differing_only_in_case_share_the_lock() -> None:
    published_at = timezone.now() - timedelta(days=1)
    upper = _document(version="V1", locale="es", published_at=published_at)
    upper.save()
    lower = _document(version="v1", locale="en", published_at=published_at)
    lower.save()
    _accept(upper)

    lower.content = "Changed."
    with pytest.raises(ValidationError):
        lower.save()
