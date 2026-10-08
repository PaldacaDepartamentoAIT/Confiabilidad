from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.admin.sites import site
from django.contrib.admin.templatetags.admin_list import results
from django.contrib.auth.models import Permission
from django.test import Client, RequestFactory
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import make_user
from apps.consents.models import PROTECTED_FIELDS, Terms, UserTerms
from apps.consents.tests.factories import make_document, publish_version

pytestmark = pytest.mark.django_db

TERMS_PERMISSIONS = ["view_terms", "add_terms", "change_terms", "delete_terms"]


def _staff(*codenames: str) -> User:
    user = make_user(is_staff=True)
    user.user_permissions.set(
        Permission.objects.filter(content_type__app_label="consents", codename__in=codenames)
    )
    return user


@pytest.fixture
def editor_client() -> Client:
    client = Client()
    client.force_login(_staff(*TERMS_PERMISSIONS))
    return client


def _form(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "kind": "terms",
        "content": "# Terms\n\nText.",
        "version": "1",
        "locale": "es",
        "requires_reacceptance": "on",
        "published_at_0": "2026-01-01",
        "published_at_1": "10:00:00",
    }
    data.update(overrides)
    return data


def _url(name: str, *args: object) -> str:
    return reverse(f"admin:consents_terms_{name}", args=args)


def _accept(document: Terms) -> None:
    UserTerms(user=make_user(), terms=document).save()


def test_staff_with_permissions_creates_a_document(editor_client: Client) -> None:
    response = editor_client.post(_url("add"), _form(locale="pt-BR", version="2.0"))

    assert response.status_code == 302
    document = Terms.objects.get()
    assert (document.version, document.locale, document.kind) == ("2.0", "pt-BR", "terms")
    assert document.published_at is not None


def test_invalid_document_is_rejected_with_the_form_errors(editor_client: Client) -> None:
    response = editor_client.post(_url("add"), _form(content="<p>Text</p>"))

    assert response.status_code == 200
    assert "content" in response.context["adminform"].form.errors
    assert not Terms.objects.exists()


def test_staff_with_permissions_edits_a_document(editor_client: Client) -> None:
    document = make_document(version="1")

    response = editor_client.post(
        _url("change", document.pk), _form(content="Edited.", published_at_0="", published_at_1="")
    )

    assert response.status_code == 302
    document.refresh_from_db()
    assert document.content == "Edited."
    assert document.published_at is None


def test_staff_with_permissions_deletes_a_document(editor_client: Client) -> None:
    document = make_document()

    response = editor_client.post(_url("delete", document.pk), {"post": "yes"})

    assert response.status_code == 302
    assert not Terms.objects.exists()


@pytest.mark.parametrize("name", ["changelist", "add"])
def test_staff_without_permissions_is_forbidden(name: str) -> None:
    client = Client()
    client.force_login(_staff())

    assert client.get(_url(name)).status_code == 403


def test_list_shows_which_documents_have_acceptances(editor_client: Client) -> None:
    accepted, free = publish_version(version="1"), publish_version(version="2")
    _accept(accepted["es"])

    response = editor_client.get(_url("changelist"))
    changelist = response.context["cl"]
    column = {
        document.pk: next(
            str(cell) for cell in row if 'class="field-has_acceptances_display"' in str(cell)
        )
        for document, row in zip(changelist.result_list, results(changelist), strict=True)
    }

    assert response.status_code == 200
    assert 'alt="True"' in column[accepted["en"].pk]
    assert 'alt="False"' in column[free["en"].pk]


def test_accepted_version_shows_protected_fields_as_read_only(editor_client: Client) -> None:
    documents = publish_version(version="1")
    _accept(documents["es"])
    request = RequestFactory().get("/")
    model_admin = site.get_model_admin(Terms)

    for document in documents.values():
        assert set(PROTECTED_FIELDS) <= set(model_admin.get_readonly_fields(request, document))
    assert set(PROTECTED_FIELDS).isdisjoint(model_admin.get_readonly_fields(request, None))


def test_posting_changes_to_an_accepted_version_does_not_change_it(
    editor_client: Client,
) -> None:
    documents = publish_version(version="1")
    _accept(documents["es"])

    response = editor_client.post(
        _url("change", documents["en"].pk), _form(content="Edited.", locale="en")
    )

    assert response.status_code == 302
    documents["en"].refresh_from_db()
    assert documents["en"].content != "Edited."


def test_accepted_version_cannot_be_deleted_one_by_one(editor_client: Client) -> None:
    documents = publish_version(version="1")
    _accept(documents["es"])

    response = editor_client.post(_url("delete", documents["en"].pk), {"post": "yes"})

    assert response.status_code == 403
    assert Terms.objects.count() == 3


def test_bulk_delete_action_with_an_accepted_version_deletes_nothing(
    editor_client: Client,
) -> None:
    accepted, free = publish_version(version="1"), publish_version(version="2")
    _accept(accepted["es"])
    selected = [accepted["en"].pk, free["es"].pk]

    response = editor_client.post(
        _url("changelist"),
        {"action": "delete_selected", "_selected_action": selected, "post": "yes"},
    )

    assert response.status_code == 403
    assert Terms.objects.count() == 6


def test_bulk_delete_action_deletes_documents_without_acceptances(editor_client: Client) -> None:
    free = publish_version(version="2")

    response = editor_client.post(
        _url("changelist"),
        {"action": "delete_selected", "_selected_action": [free["es"].pk], "post": "yes"},
    )

    assert response.status_code == 302
    assert Terms.objects.count() == 2


def test_bulk_delete_goes_through_the_model_and_skips_accepted_versions() -> None:
    accepted = publish_version(version="1")
    publish_version(version="2")
    _accept(accepted["es"])
    request = RequestFactory().post("/")
    request.user = _staff(*TERMS_PERMISSIONS)
    model_admin = site.get_model_admin(Terms)

    with patch.object(model_admin, "message_user") as message_user:
        model_admin.delete_queryset(request, Terms.objects.all())

    assert set(Terms.objects.values_list("version", flat=True)) == {"1"}
    assert Terms.objects.count() == 3
    assert "3 documents" in str(message_user.call_args.args[1])


def test_staff_without_delete_permission_cannot_delete() -> None:
    document = make_document()
    client = Client()
    client.force_login(_staff("view_terms", "change_terms"))

    response = client.post(_url("delete", document.pk), {"post": "yes"})

    assert response.status_code == 403
    assert Terms.objects.exists()
