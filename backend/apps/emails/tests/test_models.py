from collections.abc import Iterator

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import RequestFactory
from simple_history.models import HistoricalRecords

from apps.accounts.tests.factories import make_user
from apps.emails.models import EmailTemplate

pytestmark = pytest.mark.django_db

KINDS = {
    "registration_code",
    "password_reset_code",
    "account_exists",
    "password_reset_done",
    "password_changed",
    "account_disabled",
    "sessions_closed",
}


def _template(**overrides: str) -> EmailTemplate:
    values = {"kind": "account_exists", "locale": "es", "subject": "Asunto", "body": "Cuerpo"}
    values.update(overrides)
    return EmailTemplate(**values)


def _existing() -> EmailTemplate:
    template, _ = EmailTemplate.objects.get_or_create(
        kind="account_exists", locale="es", defaults={"subject": "Asunto", "body": "Cuerpo"}
    )
    return template


def test_kinds_and_locales_are_closed() -> None:
    assert {value for value, _ in EmailTemplate.Kind.choices} == KINDS
    assert {value for value, _ in EmailTemplate.Locale.choices} == {"es", "pt-BR", "en"}


@pytest.mark.parametrize(("field", "value"), [("kind", "newsletter"), ("locale", "fr")])
def test_unknown_kind_or_locale_is_rejected(field: str, value: str) -> None:
    template = _template(**{field: value})

    with pytest.raises(ValidationError) as error:
        template.full_clean()

    assert field in error.value.error_dict


def test_one_template_per_kind_and_locale_in_the_database() -> None:
    _existing()

    with pytest.raises(IntegrityError), transaction.atomic():
        EmailTemplate.objects.bulk_create([_template(subject="Otro")])


@pytest.fixture
def support_request() -> Iterator[object]:
    request = RequestFactory().get("/")
    request.user = make_user(email="support@example.com")
    HistoricalRecords.context.request = request
    yield request
    del HistoricalRecords.context.request


def test_changing_a_template_records_its_author(support_request: object) -> None:
    template = _existing()
    template.body = "Nuevo cuerpo"
    template.save()

    last = template.history.latest("history_date")

    assert last.body == "Nuevo cuerpo"
    assert last.history_type == "~"
    assert last.history_user == support_request.user  # type: ignore[attr-defined]


def test_a_template_cannot_be_deleted() -> None:
    template = _existing()

    with pytest.raises(ValidationError):
        template.delete()

    assert EmailTemplate.objects.filter(pk=template.pk).exists()


def test_a_queryset_of_templates_cannot_be_deleted() -> None:
    _existing()
    before = EmailTemplate.objects.count()

    with pytest.raises(ValidationError):
        EmailTemplate.objects.all().delete()

    assert EmailTemplate.objects.count() == before


def test_a_template_reads_as_its_kind_and_locale() -> None:
    assert str(_template(kind="password_changed", locale="pt-BR")) == "password_changed (pt-BR)"
