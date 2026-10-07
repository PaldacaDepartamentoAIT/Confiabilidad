from datetime import timedelta
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone

from apps.accounts.tests.factories import make_user
from apps.consents.hashing import email_fingerprint
from apps.consents.models import MarketingConsent, Terms, UserTerms
from apps.consents.tests.factories import make_document

pytestmark = pytest.mark.django_db

HASH = "a" * 64


def test_terms_acceptance_keeps_every_field() -> None:
    user, document = make_user(), make_document()
    before = timezone.now()

    acceptance = UserTerms(user=user, terms=document, user_email_hash=HASH)
    acceptance.save()
    acceptance.refresh_from_db()

    assert acceptance.user == user
    assert acceptance.terms == document
    assert acceptance.user_email_hash == email_fingerprint(user.email)
    assert acceptance.terms_accepted_at >= before
    assert acceptance.revoked_at is None


def test_terms_acceptance_of_a_marketing_document_is_rejected() -> None:
    marketing = make_document(kind=Terms.Kind.MARKETING)

    with pytest.raises(ValidationError) as error:
        UserTerms(user=make_user(), terms=marketing, user_email_hash=HASH).save()

    assert "terms" in error.value.error_dict


def test_two_active_acceptances_of_the_same_document_are_rejected() -> None:
    user, document = make_user(), make_document()
    UserTerms(user=user, terms=document, user_email_hash=HASH).save()

    with pytest.raises(ValidationError):
        UserTerms(user=user, terms=document, user_email_hash=HASH).save()


def test_two_active_acceptances_of_the_same_document_are_rejected_in_bulk() -> None:
    user, document = make_user(), make_document()

    with pytest.raises(IntegrityError), transaction.atomic():
        UserTerms.objects.bulk_create(
            [UserTerms(user=user, terms=document, user_email_hash=HASH) for _ in range(2)]
        )


def test_a_revoked_acceptance_does_not_block_a_new_one() -> None:
    user, document = make_user(), make_document()
    UserTerms(user=user, terms=document, user_email_hash=HASH, revoked_at=timezone.now()).save()

    UserTerms(user=user, terms=document, user_email_hash=HASH).save()

    assert UserTerms.objects.count() == 2


def test_deleting_the_user_keeps_the_acceptance_without_user() -> None:
    user = make_user()
    acceptance = UserTerms(user=user, terms=make_document(), user_email_hash=HASH)
    acceptance.save()

    user.delete()
    acceptance.refresh_from_db()

    assert acceptance.user is None
    assert acceptance.user_email_hash == email_fingerprint(user.email)


def test_deleting_an_accepted_document_is_protected() -> None:
    document = make_document()
    UserTerms(user=make_user(), terms=document, user_email_hash=HASH).save()

    with pytest.raises(ProtectedError):
        Terms.objects.filter(pk=document.pk).delete()


def test_acceptance_date_can_be_set_explicitly() -> None:
    accepted_at = timezone.now() - timedelta(days=30)

    acceptance = UserTerms(
        user=make_user(), terms=make_document(), user_email_hash=HASH, terms_accepted_at=accepted_at
    )
    acceptance.save()

    assert UserTerms.objects.get().terms_accepted_at == accepted_at


def test_acceptance_text_shows_document_and_hash_prefix() -> None:
    acceptance = UserTerms(terms=make_document(version="3"), user_email_hash=HASH)

    assert str(acceptance) == f"terms 3 (es) · {HASH[:12]}"


def test_acceptance_without_document_is_rejected() -> None:
    with pytest.raises(ValidationError) as error:
        UserTerms(user=make_user(), user_email_hash=HASH).save()

    assert "terms" in error.value.error_dict


def test_a_user_can_accept_several_documents() -> None:
    user = make_user()
    UserTerms(user=user, terms=make_document(), user_email_hash=HASH).save()
    UserTerms(user=user, terms=make_document(), user_email_hash=HASH).save()

    assert UserTerms.objects.filter(user=user).count() == 2


def _marketing(**overrides: Any) -> MarketingConsent:
    fields: dict[str, Any] = {"user_email_hash": HASH, **overrides}
    if "user" not in fields:
        fields["user"] = make_user()
    if "terms" not in fields:
        fields["terms"] = make_document(kind=Terms.Kind.MARKETING)
    return MarketingConsent(**fields)


def test_marketing_consent_keeps_every_field() -> None:
    before = timezone.now()

    consent = _marketing()
    consent.save()
    consent.refresh_from_db()

    assert consent.user is not None
    assert consent.terms.kind == Terms.Kind.MARKETING
    assert consent.user_email_hash == email_fingerprint(consent.user.email)
    assert consent.granted is True
    assert consent.granted_at >= before
    assert consent.revoked_at is None


def test_marketing_consent_of_a_terms_document_is_rejected() -> None:
    with pytest.raises(ValidationError) as error:
        _marketing(terms=make_document()).save()

    assert "terms" in error.value.error_dict


def test_two_active_marketing_consents_of_a_user_are_rejected() -> None:
    user = make_user()
    _marketing(user=user).save()

    with pytest.raises(ValidationError):
        _marketing(user=user).save()


def test_two_active_marketing_consents_of_a_user_are_rejected_in_bulk() -> None:
    user = make_user()

    with pytest.raises(IntegrityError), transaction.atomic():
        MarketingConsent.objects.bulk_create([_marketing(user=user), _marketing(user=user)])


def test_a_revoked_consent_does_not_block_a_new_active_one() -> None:
    user = make_user()
    _marketing(user=user, granted=False, revoked_at=timezone.now()).save()

    _marketing(user=user).save()

    assert MarketingConsent.objects.filter(user=user).count() == 2


def test_two_active_consents_of_different_users_are_allowed() -> None:
    _marketing().save()
    _marketing().save()

    assert MarketingConsent.objects.filter(granted=True).count() == 2


def test_two_active_consents_without_user_do_not_collide() -> None:
    first, second = _marketing(), _marketing()
    MarketingConsent.objects.bulk_create([first, second])

    MarketingConsent.objects.update(user=None)

    assert MarketingConsent.objects.filter(user=None, granted=True).count() == 2


@pytest.mark.parametrize(
    ("granted", "revoked"),
    [(True, True), (False, False)],
)
def test_granted_must_match_the_revocation_date(granted: bool, revoked: bool) -> None:
    consent = _marketing(granted=granted, revoked_at=timezone.now() if revoked else None)

    with pytest.raises(ValidationError):
        consent.save()
    with pytest.raises(IntegrityError), transaction.atomic():
        MarketingConsent.objects.bulk_create([consent])


def test_deleting_the_user_keeps_the_active_consent_without_user() -> None:
    user = make_user()
    consent = _marketing(user=user)
    consent.save()

    user.delete()
    consent.refresh_from_db()

    assert consent.user is None
    assert consent.granted is True
    assert consent.user_email_hash == email_fingerprint(user.email)


def test_deleting_a_consented_document_is_protected() -> None:
    consent = _marketing()
    consent.save()

    with pytest.raises(ProtectedError):
        Terms.objects.filter(pk=consent.terms_id).delete()


def test_marketing_consent_text_shows_document_and_hash_prefix() -> None:
    consent = _marketing(terms=make_document(kind=Terms.Kind.MARKETING, version="4"))

    assert str(consent) == f"marketing 4 (es) · {HASH[:12]}"


def _record(
    model: type[UserTerms | MarketingConsent], **fields: Any
) -> UserTerms | MarketingConsent:
    kind = Terms.Kind.TERMS if model is UserTerms else Terms.Kind.MARKETING
    fields.setdefault("terms", make_document(kind=kind))
    return model(**fields)


RECORD_MODELS = [UserTerms, MarketingConsent]


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_hash_of_the_user_email_is_stored_on_create(
    model: type[UserTerms | MarketingConsent],
) -> None:
    user = make_user(email="Ana@X.com")

    record = _record(model, user=user, user_email_hash="typed-by-hand")
    record.save()

    assert record.user_email_hash == email_fingerprint("ana@x.com")


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_changing_the_user_email_keeps_the_stored_hash(
    model: type[UserTerms | MarketingConsent],
) -> None:
    user = make_user(email="ana@x.com")
    record = _record(model, user=user)
    record.save()

    user.email = "ana@y.com"
    user.save()
    record.refresh_from_db()
    record.save()

    assert record.user_email_hash == email_fingerprint("ana@x.com")


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_changing_the_user_of_a_record_recalculates_the_hash(
    model: type[UserTerms | MarketingConsent],
) -> None:
    record = _record(model, user=make_user(email="ana@x.com"))
    record.save()

    record.user = make_user(email="bea@x.com")
    record.save()

    assert record.user_email_hash == email_fingerprint("bea@x.com")


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_saving_again_ignores_a_hash_typed_by_hand(
    model: type[UserTerms | MarketingConsent],
) -> None:
    record = _record(model, user=make_user(email="ana@x.com"))
    record.save()

    record.user_email_hash = "typed-by-hand"
    record.save()
    record.refresh_from_db()

    assert record.user_email_hash == email_fingerprint("ana@x.com")


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_creating_a_record_without_user_is_rejected(
    model: type[UserTerms | MarketingConsent],
) -> None:
    with pytest.raises(ValidationError) as error:
        _record(model).save()

    assert "user" in error.value.error_dict
    assert not model.objects.exists()


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_saving_a_record_of_a_deleted_account_keeps_its_hash(
    model: type[UserTerms | MarketingConsent],
) -> None:
    user = make_user(email="ana@x.com")
    record = _record(model, user=user)
    record.save()
    user.delete()
    record.refresh_from_db()

    record.save()
    record.refresh_from_db()

    assert record.user is None
    assert record.user_email_hash == email_fingerprint("ana@x.com")


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_clearing_the_user_of_a_record_keeps_its_hash(
    model: type[UserTerms | MarketingConsent],
) -> None:
    record = _record(model, user=make_user(email="ana@x.com"))
    record.save()

    record.user = None
    record.save()
    record.refresh_from_db()

    assert record.user_email_hash == email_fingerprint("ana@x.com")
