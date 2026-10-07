from typing import Any

import pytest
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import make_user
from apps.consents.models import MarketingConsent, Terms, UserTerms
from apps.consents.tests.factories import make_document

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user() -> User:
    user = make_user(is_staff=True, is_superuser=True)
    user.groups.add(Group.objects.get(name="Soporte técnico"))
    return user


@pytest.fixture
def admin_client(admin_user: User) -> Client:
    client = Client()
    client.force_login(admin_user)
    return client


def _records() -> list[models.Model]:
    acceptance = UserTerms(user=make_user(), terms=make_document())
    acceptance.save()
    consent = MarketingConsent(user=make_user(), terms=make_document(kind=Terms.Kind.MARKETING))
    consent.save()
    return [make_document(), acceptance, consent]


def _url(record: models.Model, name: str, *args: Any) -> str:
    opts = record._meta
    return reverse(f"admin:{opts.app_label}_{opts.model_name}_{name}", args=[record.pk, *args])


def test_revert_button_is_disabled() -> None:
    assert settings.SIMPLE_HISTORY_REVERT_DISABLED is True


def test_change_from_the_panel_records_its_author(admin_client: Client, admin_user: User) -> None:
    document = make_document(version="1")

    admin_client.post(
        _url(document, "change"),
        {
            "kind": "terms",
            "content": "Edited.",
            "version": "1",
            "locale": "es",
            "requires_reacceptance": "on",
            "published_at_0": "",
            "published_at_1": "",
        },
    )

    latest = Terms.history.filter(id=document.pk).latest("history_date")
    assert latest.content == "Edited."
    assert latest.history_user == admin_user


def test_revocation_from_the_panel_records_its_author(
    admin_client: Client, admin_user: User
) -> None:
    acceptance = UserTerms(user=make_user(), terms=make_document())
    acceptance.save()

    admin_client.post(
        reverse("admin:consents_userterms_changelist"),
        {"action": "revoke_selected", "_selected_action": [acceptance.pk]},
    )

    latest = UserTerms.history.filter(id=acceptance.pk).latest("history_date")
    assert latest.revoked_at is not None
    assert latest.history_user == admin_user


def test_history_views_open_for_the_three_tables(admin_client: Client) -> None:
    for record in _records():
        version = type(record).history.filter(id=record.pk).get()  # type: ignore[attr-defined]

        assert admin_client.get(_url(record, "history")).status_code == 200
        assert (
            admin_client.get(_url(record, "simple_history", version.history_id)).status_code == 200
        )


def test_reverting_from_the_history_is_forbidden(admin_client: Client) -> None:
    for record in _records():
        history = type(record).history  # type: ignore[attr-defined]
        first = history.filter(id=record.pk).get()
        record.save()

        response = admin_client.post(_url(record, "simple_history", first.history_id), {})

        assert response.status_code == 403
        assert history.filter(id=record.pk).count() == 2
