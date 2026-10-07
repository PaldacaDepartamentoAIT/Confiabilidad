import pytest
from django.db import models
from django.utils import timezone

from apps.accounts.tests.factories import make_user
from apps.consents.models import MarketingConsent, Terms, UserTerms
from apps.consents.tests.factories import make_document

pytestmark = pytest.mark.django_db

HISTORY_METADATA = {
    "history_id",
    "history_date",
    "history_change_reason",
    "history_type",
    "history_user",
}


@pytest.mark.parametrize("model", [Terms, UserTerms, MarketingConsent])
def test_history_tracks_every_field(model: type[models.Model]) -> None:
    history_model = model.history.model  # type: ignore[attr-defined]
    tracked = {field.name for field in history_model._meta.concrete_fields}
    expected = {field.name for field in model._meta.concrete_fields}

    assert tracked == expected | HISTORY_METADATA


def _history_types(model: type[models.Model], pk: int) -> list[str]:
    return list(
        model.history.filter(id=pk)  # type: ignore[attr-defined]
        .order_by("history_date")
        .values_list("history_type", flat=True)
    )


def test_document_history_records_create_change_and_delete() -> None:
    document = make_document(content="First.")
    document.content = "Second."
    document.save()
    pk = document.pk

    document.delete()

    assert _history_types(Terms, pk) == ["+", "~", "-"]
    contents = (
        Terms.history.filter(id=pk).order_by("history_date").values_list("content", flat=True)
    )
    assert list(contents) == ["First.", "Second.", "Second."]


def test_acceptance_history_records_create_change_and_delete() -> None:
    acceptance = UserTerms(user=make_user(), terms=make_document())
    acceptance.save()
    acceptance.revoked_at = timezone.now()
    acceptance.save()
    pk = acceptance.pk

    acceptance.delete()

    assert _history_types(UserTerms, pk) == ["+", "~", "-"]
    last = UserTerms.history.filter(id=pk).latest("history_date")
    assert last.revoked_at is not None
    assert last.user_email_hash == acceptance.user_email_hash


def test_marketing_history_records_create_change_and_delete() -> None:
    consent = MarketingConsent(user=make_user(), terms=make_document(kind=Terms.Kind.MARKETING))
    consent.save()
    consent.granted, consent.revoked_at = False, timezone.now()
    consent.save()
    pk = consent.pk

    consent.delete()

    assert _history_types(MarketingConsent, pk) == ["+", "~", "-"]
    assert MarketingConsent.history.filter(id=pk, granted=False).count() == 2


def test_history_survives_deleting_the_user() -> None:
    user = make_user()
    acceptance = UserTerms(user=user, terms=make_document())
    acceptance.save()
    user_id = user.pk

    user.delete()

    # SET_NULL lo aplica la base de datos sin pasar por save(): no añade una versión.
    versions = UserTerms.history.filter(id=acceptance.pk)
    assert versions.count() == 1
    assert versions.get().user_id == user_id
