from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone

from apps.accounts.tests.factories import make_user
from apps.consents.models import Terms, UserTerms
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
    assert acceptance.user_email_hash == HASH
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
    assert acceptance.user_email_hash == HASH


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
