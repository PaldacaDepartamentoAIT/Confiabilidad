from datetime import timedelta

import pytest
from django.utils import timezone

from apps.consents.models import Terms
from apps.consents.tests.factories import make_document, publish_version
from apps.consents.versions import current_document, current_version, in_force_versions

pytestmark = pytest.mark.django_db

DAY = timedelta(days=1)


def test_without_documents_there_is_no_current_version() -> None:
    assert current_version(Terms.Kind.TERMS) is None
    assert current_document(Terms.Kind.TERMS, "es") is None


def test_version_with_every_locale_published_is_in_force_since_the_latest_date() -> None:
    now = timezone.now()
    make_document(version="1", locale="es", published_at=now - 3 * DAY)
    make_document(version="1", locale="pt-BR", published_at=now - 2 * DAY)
    make_document(version="1", locale="en", published_at=now - 5 * DAY)

    current = current_version(Terms.Kind.TERMS)

    assert current is not None
    assert current.version == "1"
    assert current.in_force_at == now - 2 * DAY


def test_version_missing_a_locale_is_not_in_force() -> None:
    make_document(version="1", locale="es", published_at=timezone.now() - DAY)
    make_document(version="1", locale="en", published_at=timezone.now() - DAY)

    assert current_version(Terms.Kind.TERMS) is None


@pytest.mark.parametrize("published_at", [None, "future"])
def test_version_with_a_draft_locale_is_not_in_force(published_at: str | None) -> None:
    documents = publish_version(version="1")
    documents["en"].published_at = timezone.now() + DAY if published_at == "future" else None
    documents["en"].save()

    assert current_version(Terms.Kind.TERMS) is None
    assert current_document(Terms.Kind.TERMS, "es") is None


def test_current_version_is_the_latest_in_force() -> None:
    now = timezone.now()
    publish_version(version="1", published_at=now - 3 * DAY)
    publish_version(version="2", published_at=now - DAY)
    publish_version(version="3", published_at=now + DAY)

    current = current_version(Terms.Kind.TERMS)

    assert current is not None
    assert current.version == "2"


def test_on_the_same_date_the_version_created_later_wins() -> None:
    published_at = timezone.now() - DAY
    publish_version(version="b", published_at=published_at)
    publish_version(version="a", published_at=published_at)

    current = current_version(Terms.Kind.TERMS)

    assert current is not None
    assert current.version == "a"


def test_kinds_have_independent_current_versions() -> None:
    publish_version(kind=Terms.Kind.TERMS, version="1")
    publish_version(kind=Terms.Kind.MARKETING, version="7")

    terms, marketing = current_version(Terms.Kind.TERMS), current_version(Terms.Kind.MARKETING)

    assert terms is not None and terms.version == "1"
    assert marketing is not None and marketing.version == "7"


def test_versions_differing_only_in_case_across_locales_are_the_same_version() -> None:
    published_at = timezone.now() - DAY
    make_document(version="V1", locale="es", published_at=published_at)
    make_document(version="v1", locale="pt-BR", published_at=published_at)
    make_document(version="v1", locale="en", published_at=published_at)

    assert current_version(Terms.Kind.TERMS) is not None


def test_current_document_is_the_one_of_the_current_version_in_that_locale() -> None:
    now = timezone.now()
    publish_version(version="1", published_at=now - 3 * DAY)
    current = publish_version(version="2", published_at=now - DAY)

    assert current_document(Terms.Kind.TERMS, "pt-BR") == current["pt-BR"]


def test_in_force_versions_are_listed_from_newest_to_oldest() -> None:
    now = timezone.now()
    publish_version(version="1", published_at=now - 3 * DAY)
    publish_version(version="2", published_at=now - DAY)
    publish_version(version="3", published_at=now + DAY)

    versions = in_force_versions(Terms.Kind.TERMS)

    assert [v.version for v in versions] == ["2", "1"]
    assert [v.in_force_at for v in versions] == [now - DAY, now - 3 * DAY]


def test_entry_into_force_wins_over_creation_order() -> None:
    now = timezone.now()
    publish_version(version="2", published_at=now - DAY)
    publish_version(version="1", published_at=now - 3 * DAY)

    current = current_version(Terms.Kind.TERMS)

    assert current is not None
    assert current.version == "2"


def test_current_document_belongs_to_the_requested_kind() -> None:
    publish_version(kind=Terms.Kind.TERMS, version="1")
    marketing = publish_version(kind=Terms.Kind.MARKETING, version="1")

    assert current_document(Terms.Kind.MARKETING, "es") == marketing["es"]


def test_on_the_same_date_creation_order_wins_over_alphabetical_order() -> None:
    published_at = timezone.now() - DAY
    publish_version(version="a", published_at=published_at)
    publish_version(version="b", published_at=published_at)

    current = current_version(Terms.Kind.TERMS)

    assert current is not None
    assert current.version == "b"
