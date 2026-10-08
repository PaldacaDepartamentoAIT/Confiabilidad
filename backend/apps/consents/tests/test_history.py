from collections.abc import Callable, Iterator

import pytest
from django.db import models
from django.test import RequestFactory
from django.utils import timezone
from simple_history.models import HistoricalRecords

from apps.accounts.models import User
from apps.accounts.tests.factories import make_user
from apps.consents.models import MarketingConsent, Terms, UserTerms
from apps.consents.tests.factories import make_document

RECORD_MODELS = [UserTerms, MarketingConsent]


def _record(
    model: type[UserTerms | MarketingConsent], *, user: User
) -> UserTerms | MarketingConsent:
    kind = Terms.Kind.TERMS if model is UserTerms else Terms.Kind.MARKETING
    return model(user=user, terms=make_document(kind=kind))


pytestmark = pytest.mark.django_db

HISTORY_METADATA = {
    "history_id",
    "history_date",
    "history_change_reason",
    "history_type",
    "history_user",
}


@pytest.mark.parametrize(
    ("model", "excluded"),
    [(Terms, set()), (UserTerms, {"user"}), (MarketingConsent, {"user"})],
)
def test_history_tracks_every_field_except_the_user_of_records(
    model: type[models.Model], excluded: set[str]
) -> None:
    history_model = model.history.model  # type: ignore[attr-defined]
    tracked = {field.name for field in history_model._meta.concrete_fields}
    expected = {field.name for field in model._meta.concrete_fields} - excluded

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


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_deleting_the_account_adds_no_version_and_keeps_no_user(
    model: type[UserTerms | MarketingConsent],
) -> None:
    user = make_user()
    record = _record(model, user=user)
    record.save()

    user.delete()

    versions = model.history.filter(id=record.pk)
    assert versions.count() == 1
    assert not hasattr(versions.get(), "user_id")


@pytest.fixture
def as_request_user() -> Iterator[Callable[[User], None]]:
    def set_user(user: User) -> None:
        request = RequestFactory().post("/")
        request.user = user
        HistoricalRecords.context.request = request

    yield set_user
    if hasattr(HistoricalRecords.context, "request"):
        del HistoricalRecords.context.request


def _last_author(record: UserTerms | MarketingConsent) -> User | None:
    author: User | None = (
        type(record).history.filter(id=record.pk).latest("history_date").history_user
    )
    return author


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_staff_other_than_the_owner_is_recorded_as_author(
    model: type[UserTerms | MarketingConsent], as_request_user: Callable[[User], None]
) -> None:
    support = make_user(is_staff=True)
    as_request_user(support)

    record = _record(model, user=make_user())
    record.save()

    assert _last_author(record) == support


@pytest.mark.parametrize("model", RECORD_MODELS)
@pytest.mark.parametrize("is_staff", [False, True])
def test_the_owner_is_never_recorded_as_author(
    model: type[UserTerms | MarketingConsent],
    is_staff: bool,
    as_request_user: Callable[[User], None],
) -> None:
    owner = make_user(is_staff=is_staff)
    as_request_user(owner)

    record = _record(model, user=owner)
    record.save()
    record_id = record.pk
    record.delete()

    authors = model.history.filter(id=record_id).values_list("history_user", flat=True)
    assert list(authors) == [None, None]


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_a_user_who_is_not_staff_is_not_recorded_as_author(
    model: type[UserTerms | MarketingConsent], as_request_user: Callable[[User], None]
) -> None:
    as_request_user(make_user())

    record = _record(model, user=make_user())
    record.save()

    assert _last_author(record) is None


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_an_inactive_staff_member_is_not_recorded_as_author(
    model: type[UserTerms | MarketingConsent], as_request_user: Callable[[User], None]
) -> None:
    as_request_user(make_user(is_staff=True, is_active=False))

    record = _record(model, user=make_user())
    record.save()

    assert _last_author(record) is None


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_an_explicit_author_is_filtered_too(
    model: type[UserTerms | MarketingConsent],
) -> None:
    owner = make_user(is_staff=True)
    record = _record(model, user=owner)
    record._history_user = owner  # type: ignore[union-attr]
    record.save()

    support = make_user(is_staff=True)
    record._history_user = support  # type: ignore[union-attr]
    record.save()

    authors = model.history.filter(id=record.pk).order_by("history_date")
    assert [version.history_user for version in authors] == [None, support]


@pytest.mark.parametrize("model", RECORD_MODELS)
@pytest.mark.parametrize("explicit", [False, True])
def test_the_owner_clearing_their_own_user_is_not_recorded_as_author(
    model: type[UserTerms | MarketingConsent],
    explicit: bool,
    as_request_user: Callable[[User], None],
) -> None:
    owner = make_user(is_staff=True)
    record = _record(model, user=owner)
    record.save()

    record.user = None
    if explicit:
        record._history_user = owner  # type: ignore[union-attr]
    else:
        as_request_user(owner)
    record.save()

    assert _last_author(record) is None


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_another_staff_clearing_the_user_is_recorded_as_author(
    model: type[UserTerms | MarketingConsent], as_request_user: Callable[[User], None]
) -> None:
    record = _record(model, user=make_user(is_staff=True))
    record.save()
    support = make_user(is_staff=True)
    as_request_user(support)

    record.user = None
    record.save()

    assert _last_author(record) == support


@pytest.mark.parametrize("model", RECORD_MODELS)
@pytest.mark.parametrize("author_kind", ["owner", "not_staff", "inactive_staff"])
def test_an_explicit_author_is_filtered_on_delete(
    model: type[UserTerms | MarketingConsent], author_kind: str
) -> None:
    owner = make_user(is_staff=True)
    record = _record(model, user=owner)
    record.save()
    record_id = record.pk
    authors = {
        "owner": owner,
        "not_staff": make_user(),
        "inactive_staff": make_user(is_staff=True, is_active=False),
    }

    record._history_user = authors[author_kind]  # type: ignore[union-attr]
    record.delete()

    deletion = model.history.get(id=record_id, history_type="-")
    assert deletion.history_user is None


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_another_staff_deleting_explicitly_is_recorded_as_author(
    model: type[UserTerms | MarketingConsent],
) -> None:
    record = _record(model, user=make_user(is_staff=True))
    record.save()
    record_id = record.pk
    support = make_user(is_staff=True)

    record._history_user = support  # type: ignore[union-attr]
    record.delete()

    deletion = model.history.get(id=record_id, history_type="-")
    assert deletion.history_user == support


@pytest.mark.parametrize("model", RECORD_MODELS)
@pytest.mark.parametrize("explicit", [False, True])
def test_the_owner_deleting_a_row_cleared_in_memory_is_not_recorded_as_author(
    model: type[UserTerms | MarketingConsent],
    explicit: bool,
    as_request_user: Callable[[User], None],
) -> None:
    owner = make_user(is_staff=True)
    record = _record(model, user=owner)
    record.save()
    record_id = record.pk

    record.user = None
    if explicit:
        record._history_user = owner  # type: ignore[union-attr]
    else:
        as_request_user(owner)
    record.delete()

    deletion = model.history.get(id=record_id, history_type="-")
    assert deletion.history_user is None


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_another_staff_deleting_a_row_cleared_in_memory_is_recorded_as_author(
    model: type[UserTerms | MarketingConsent], as_request_user: Callable[[User], None]
) -> None:
    record = _record(model, user=make_user(is_staff=True))
    record.save()
    record_id = record.pk
    support = make_user(is_staff=True)
    as_request_user(support)

    record.user = None
    record.delete()

    deletion = model.history.get(id=record_id, history_type="-")
    assert deletion.history_user == support
