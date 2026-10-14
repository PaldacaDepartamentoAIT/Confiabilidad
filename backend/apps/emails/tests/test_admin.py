import importlib
from typing import Any

import pytest
from django.apps import apps as global_apps
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import make_user
from apps.emails.models import EmailTemplate

pytestmark = pytest.mark.django_db

SUPPORT_GROUP = "Soporte técnico"


@pytest.fixture(autouse=True)
def _templates(settings: Any) -> None:
    settings.FRONTEND_BASE_URL = "https://app.ejemplo.com"
    migration = importlib.import_module("apps.emails.migrations.0002_initial_templates")
    migration.create_initial_templates(global_apps, None)


def _client(user: User) -> Client:
    client = Client()
    client.force_login(user)
    return client


def _support_member() -> User:
    user = make_user(is_staff=True)
    group, _ = Group.objects.get_or_create(name=SUPPORT_GROUP)
    user.groups.add(group)
    return user


@pytest.fixture(params=["support", "superuser"])
def allowed_client(request: pytest.FixtureRequest) -> Client:
    if request.param == "support":
        return _client(_support_member())
    return _client(make_user(is_staff=True, is_superuser=True))


def _template() -> EmailTemplate:
    return EmailTemplate.objects.get(kind="registration_code", locale="es")


def _url(name: str, *args: object) -> str:
    return reverse(f"admin:emails_emailtemplate_{name}", args=args)


def test_support_and_superusers_list_and_open_the_templates(allowed_client: Client) -> None:
    assert allowed_client.get(_url("changelist")).status_code == 200
    assert allowed_client.get(_url("change", _template().pk)).status_code == 200


def test_support_and_superusers_edit_subject_and_body(allowed_client: Client) -> None:
    template = _template()
    body = "Código {{ code }}, vence en {{ expires_in }}: {{ link }}"

    response = allowed_client.post(
        _url("change", template.pk), {"subject": "Nuevo asunto", "body": body}
    )

    assert response.status_code == 302
    template.refresh_from_db()
    assert (template.subject, template.body) == ("Nuevo asunto", body)
    assert (template.kind, template.locale) == ("registration_code", "es")


def test_an_invalid_template_shows_every_problem_and_is_not_saved(allowed_client: Client) -> None:
    template = _template()
    before = (template.subject, template.body)

    response = allowed_client.post(
        _url("change", template.pk), {"subject": "Asunto", "body": "Sin código https://otro.com"}
    )

    assert response.status_code == 200
    content = response.content.decode()
    for problem in ("code", "link", "expires_in", "https://otro.com"):
        assert problem in content
    template.refresh_from_db()
    assert (template.subject, template.body) == before


def test_templates_cannot_be_added_or_deleted(allowed_client: Client) -> None:
    template = _template()

    assert allowed_client.get(_url("add")).status_code == 403
    assert allowed_client.get(_url("delete", template.pk)).status_code == 403
    assert allowed_client.post(_url("delete", template.pk), {"post": "yes"}).status_code == 403
    assert EmailTemplate.objects.filter(pk=template.pk).exists()


def test_the_history_is_visible_but_cannot_be_reverted(allowed_client: Client) -> None:
    template = _template()
    template.body = template.body + "\n"
    template.save()
    version = template.history.latest("history_date")

    history_url = _url("history", template.pk)
    version_url = reverse(
        "admin:emails_emailtemplate_simple_history", args=[template.pk, version.history_id]
    )

    assert allowed_client.get(history_url).status_code == 200
    assert allowed_client.post(version_url, {"subject": "x", "body": "y"}).status_code == 403


def test_staff_outside_support_cannot_reach_the_templates() -> None:
    client = _client(make_user(is_staff=True))

    assert client.get(_url("changelist")).status_code == 403
    assert client.get(_url("change", _template().pk)).status_code == 403
