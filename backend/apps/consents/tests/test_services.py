from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.tests.factories import make_user
from apps.consents import services
from apps.consents.hashing import email_fingerprint
from apps.consents.models import Terms, UserTerms
from apps.consents.tests.factories import make_document, publish_version

pytestmark = pytest.mark.django_db

DAY = timedelta(days=1)


def _error_code(error: pytest.ExceptionInfo[ValidationError]) -> str | None:
    return error.value.code


def test_accepting_terms_registers_the_current_document_shown() -> None:
    documents = publish_version(version="2")
    user = make_user(email="ana@x.com")
    before = timezone.now()

    acceptance = services.accept_terms(user, version="2", locale="pt-BR")

    assert acceptance.user == user
    assert acceptance.terms == documents["pt-BR"]
    assert acceptance.user_email_hash == email_fingerprint("ana@x.com")
    assert acceptance.terms_accepted_at >= before
    assert acceptance.revoked_at is None


def test_version_is_matched_ignoring_case() -> None:
    documents = publish_version(version="v2")

    acceptance = services.accept_terms(make_user(), version="V2", locale="es")

    assert acceptance.terms == documents["es"]


@pytest.mark.parametrize(
    ("version", "locale", "code"),
    [
        ("9", "es", "document_not_found"),
        ("1", "fr", "document_not_found"),
        ("m1", "es", "wrong_kind"),
        ("old", "es", "not_current_document"),
        ("next", "es", "not_current_document"),
        ("draft", "es", "not_current_document"),
    ],
)
def test_accepting_another_document_is_rejected(version: str, locale: str, code: str) -> None:
    now = timezone.now()
    publish_version(version="old", published_at=now - 3 * DAY)
    publish_version(version="1", published_at=now - DAY)
    publish_version(version="next", published_at=now + DAY)
    make_document(version="draft")
    publish_version(kind=Terms.Kind.MARKETING, version="m1")

    with pytest.raises(ValidationError) as error:
        services.accept_terms(make_user(), version=version, locale=locale)

    assert _error_code(error) == code
    assert not UserTerms.objects.exists()


def test_accepting_without_current_terms_is_rejected() -> None:
    make_document(version="1")

    with pytest.raises(ValidationError) as error:
        services.accept_terms(make_user(), version="1", locale="es")

    assert _error_code(error) == "no_current_version"
    assert not UserTerms.objects.exists()


def test_inactive_account_cannot_accept_terms() -> None:
    publish_version(version="1")

    with pytest.raises(ValidationError) as error:
        services.accept_terms(make_user(is_active=False), version="1", locale="es")

    assert _error_code(error) == "inactive_account"
    assert not UserTerms.objects.exists()


def test_accepting_the_same_document_again_returns_the_existing_acceptance() -> None:
    publish_version(version="1")
    user = make_user()
    first = services.accept_terms(user, version="1", locale="es")

    second = services.accept_terms(user, version="1", locale="es")

    assert second == first
    assert UserTerms.objects.count() == 1


def test_accepting_after_a_revocation_creates_a_new_acceptance() -> None:
    publish_version(version="1")
    user = make_user()
    first = services.accept_terms(user, version="1", locale="es")
    first.revoked_at = timezone.now()
    first.save()

    second = services.accept_terms(user, version="1", locale="es")

    assert second != first
    assert UserTerms.objects.filter(revoked_at__isnull=True).get() == second


def test_accepting_another_locale_of_the_same_version_is_a_new_acceptance() -> None:
    publish_version(version="1")
    user = make_user()
    services.accept_terms(user, version="1", locale="es")

    services.accept_terms(user, version="1", locale="en")

    assert UserTerms.objects.filter(user=user).count() == 2


def test_simultaneous_acceptance_returns_the_one_that_won(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documents = publish_version(version="1")
    user = make_user()
    winner = UserTerms(user=user, terms=documents["es"])
    winner.save()
    # El otro proceso aún no veía la aceptación cuando buscó la existente.
    monkeypatch.setattr(services, "_active_acceptance", lambda user, document: None)

    acceptance = services.accept_terms(user, version="1", locale="es")

    assert acceptance == winner
    assert UserTerms.objects.count() == 1


def test_a_database_error_without_a_winner_is_not_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publish_version(version="1")

    def fail(*args: object, **kwargs: object) -> None:
        raise IntegrityError("boom")

    monkeypatch.setattr(UserTerms, "save", fail)

    with pytest.raises(IntegrityError):
        services.accept_terms(make_user(), version="1", locale="es")


def test_simultaneous_acceptance_ignores_revoked_ones(monkeypatch: pytest.MonkeyPatch) -> None:
    documents = publish_version(version="1")
    user = make_user()
    UserTerms(user=user, terms=documents["es"], revoked_at=timezone.now()).save()
    winner = UserTerms(user=user, terms=documents["es"])
    winner.save()
    UserTerms(user=user, terms=documents["es"], revoked_at=timezone.now()).save()
    monkeypatch.setattr(services, "_active_acceptance", lambda user, document: None)

    assert services.accept_terms(user, version="1", locale="es") == winner
