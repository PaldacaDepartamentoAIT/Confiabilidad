from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.tests.factories import make_user
from apps.consents import services
from apps.consents.hashing import email_fingerprint
from apps.consents.models import MarketingConsent, Terms, UserTerms
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


def test_granting_marketing_registers_an_active_consent_of_the_document_shown() -> None:
    documents = publish_version(kind=Terms.Kind.MARKETING, version="m1")
    user = make_user(email="ana@x.com")
    before = timezone.now()

    consent = services.grant_marketing(user, version="m1", locale="en")

    assert consent.user == user
    assert consent.terms == documents["en"]
    assert consent.user_email_hash == email_fingerprint("ana@x.com")
    assert consent.granted is True
    assert consent.granted_at >= before
    assert consent.revoked_at is None


@pytest.mark.parametrize(
    ("version", "code"),
    [
        ("9", "document_not_found"),
        ("t1", "wrong_kind"),
        ("old", "not_current_document"),
        ("draft", "not_current_document"),
    ],
)
def test_granting_another_document_is_rejected(version: str, code: str) -> None:
    publish_version(kind=Terms.Kind.MARKETING, version="old", published_at=timezone.now() - 3 * DAY)
    publish_version(kind=Terms.Kind.MARKETING, version="m1")
    make_document(kind=Terms.Kind.MARKETING, version="draft")
    publish_version(version="t1")

    with pytest.raises(ValidationError) as error:
        services.grant_marketing(make_user(), version=version, locale="es")

    assert _error_code(error) == code
    assert not MarketingConsent.objects.exists()


def test_granting_without_current_marketing_is_rejected() -> None:
    make_document(kind=Terms.Kind.MARKETING, version="m1")

    with pytest.raises(ValidationError) as error:
        services.grant_marketing(make_user(), version="m1", locale="es")

    assert _error_code(error) == "no_current_version"


def test_inactive_account_cannot_grant_marketing() -> None:
    publish_version(kind=Terms.Kind.MARKETING, version="m1")

    with pytest.raises(ValidationError) as error:
        services.grant_marketing(make_user(is_active=False), version="m1", locale="es")

    assert _error_code(error) == "inactive_account"
    assert not MarketingConsent.objects.exists()


def test_granting_the_same_document_again_returns_the_active_consent() -> None:
    publish_version(kind=Terms.Kind.MARKETING, version="m1")
    user = make_user()
    first = services.grant_marketing(user, version="m1", locale="es")

    second = services.grant_marketing(user, version="m1", locale="es")

    assert second == first
    assert MarketingConsent.objects.count() == 1


@pytest.mark.parametrize("new_locale", ["es", "en"])
def test_granting_another_document_replaces_the_active_consent(new_locale: str) -> None:
    now = timezone.now()
    publish_version(kind=Terms.Kind.MARKETING, version="m1", published_at=now - 3 * DAY)
    user = make_user()
    old = services.grant_marketing(user, version="m1", locale="es")
    new_documents = publish_version(kind=Terms.Kind.MARKETING, version="m2", published_at=now - DAY)

    new = services.grant_marketing(user, version="m2", locale=new_locale)
    old.refresh_from_db()

    assert new.terms == new_documents[new_locale]
    assert new.granted is True
    assert old.granted is False
    assert old.revoked_at is not None
    assert MarketingConsent.objects.filter(user=user, granted=True).get() == new


def test_a_failed_replacement_keeps_the_previous_consent_active(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = timezone.now()
    publish_version(kind=Terms.Kind.MARKETING, version="m1", published_at=now - 3 * DAY)
    user = make_user()
    old = services.grant_marketing(user, version="m1", locale="es")
    publish_version(kind=Terms.Kind.MARKETING, version="m2", published_at=now - DAY)
    original_save = MarketingConsent.save

    def fail_on_create(self: MarketingConsent, *args: object, **kwargs: object) -> None:
        if self._state.adding:
            raise IntegrityError("boom")
        original_save(self, *args, **kwargs)

    monkeypatch.setattr(MarketingConsent, "save", fail_on_create)

    with pytest.raises(IntegrityError):
        services.grant_marketing(user, version="m2", locale="es")
    old.refresh_from_db()

    assert old.granted is True
    assert old.revoked_at is None


def test_simultaneous_grant_returns_the_one_that_won(monkeypatch: pytest.MonkeyPatch) -> None:
    documents = publish_version(kind=Terms.Kind.MARKETING, version="m1")
    user = make_user()
    winner = MarketingConsent(user=user, terms=documents["es"])
    winner.save()
    monkeypatch.setattr(services, "_active_consent", lambda user: None)

    consent = services.grant_marketing(user, version="m1", locale="es")

    assert consent == winner
    assert MarketingConsent.objects.count() == 1


def test_granting_again_after_a_revocation_creates_a_new_active_consent() -> None:
    publish_version(kind=Terms.Kind.MARKETING, version="m1")
    user = make_user()
    first = services.grant_marketing(user, version="m1", locale="es")
    first.granted, first.revoked_at = False, timezone.now()
    first.save()

    second = services.grant_marketing(user, version="m1", locale="es")

    assert second != first
    assert second.granted is True


def test_simultaneous_grant_of_another_document_is_not_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = timezone.now()
    old = publish_version(kind=Terms.Kind.MARKETING, version="m1", published_at=now - 3 * DAY)
    publish_version(kind=Terms.Kind.MARKETING, version="m2", published_at=now - DAY)
    user = make_user()
    MarketingConsent(user=user, terms=old["es"]).save()
    monkeypatch.setattr(services, "_active_consent", lambda user: None)

    with pytest.raises(ValidationError):
        services.grant_marketing(user, version="m2", locale="es")


def test_revoking_marketing_closes_the_active_consent_and_keeps_the_row() -> None:
    publish_version(kind=Terms.Kind.MARKETING, version="m1")
    user = make_user()
    consent = services.grant_marketing(user, version="m1", locale="es")
    before = timezone.now()

    revoked = services.revoke_marketing(user)
    consent.refresh_from_db()

    assert revoked == consent
    assert consent.granted is False
    assert consent.revoked_at is not None and consent.revoked_at >= before
    assert MarketingConsent.objects.count() == 1


def test_revoking_without_an_active_consent_changes_nothing() -> None:
    publish_version(kind=Terms.Kind.MARKETING, version="m1")
    user = make_user()
    consent = services.grant_marketing(user, version="m1", locale="es")
    services.revoke_marketing(user)
    consent.refresh_from_db()
    first_revocation = consent.revoked_at

    assert services.revoke_marketing(user) is None
    assert services.revoke_marketing(make_user()) is None
    consent.refresh_from_db()
    assert consent.revoked_at == first_revocation


def test_inactive_account_can_revoke_marketing() -> None:
    publish_version(kind=Terms.Kind.MARKETING, version="m1")
    user = make_user()
    services.grant_marketing(user, version="m1", locale="es")
    user.is_active = False
    user.save()

    revoked = services.revoke_marketing(user)

    assert revoked is not None and revoked.granted is False


def test_revoking_only_touches_the_users_consent() -> None:
    publish_version(kind=Terms.Kind.MARKETING, version="m1")
    user, other = make_user(), make_user()
    services.grant_marketing(user, version="m1", locale="es")
    kept = services.grant_marketing(other, version="m1", locale="es")

    services.revoke_marketing(user)
    kept.refresh_from_db()

    assert kept.granted is True
