import importlib
from typing import Any

import pytest
from django.apps import apps as global_apps
from django.contrib.auth.models import Group
from django.test import Client, RequestFactory
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import make_user
from apps.emails.admin import is_support
from apps.emails.models import EmailTemplate, OutboundEmail

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


def test_a_version_of_the_history_can_be_read(allowed_client: Client) -> None:
    template = _template()
    template.save()
    version = template.history.latest("history_date")
    version_url = reverse(
        "admin:emails_emailtemplate_simple_history", args=[template.pk, version.history_id]
    )

    assert allowed_client.get(version_url).status_code == 200


def test_a_support_member_without_staff_access_is_not_support() -> None:
    user = _support_member()
    user.is_staff = False
    user.save()
    request = RequestFactory().get("/")
    request.user = user

    assert is_support(request) is False

    response = _client(user).get(_url("changelist"))
    assert response.status_code == 302
    assert "/login/" in response["Location"]


def _outbound(status: str, recipient: str) -> OutboundEmail:
    return OutboundEmail.objects.create(
        kind="password_changed",
        locale="es",
        recipient=recipient,
        status=status,
        attempts=3,
        last_error="SMTPRecipientsRefused: 550 No such user",
    )


def _failed_url(name: str, *args: object) -> str:
    return reverse(f"admin:emails_failedemail_{name}", args=args)


def test_only_failed_emails_are_listed_with_their_details(allowed_client: Client) -> None:
    _outbound("failed", "fallo@example.com")
    _outbound("pending", "espera@example.com")

    content = allowed_client.get(_failed_url("changelist")).content.decode()

    assert "fallo@example.com" in content
    assert "espera@example.com" not in content
    assert "550 No such user" in content


def test_a_failed_email_can_be_viewed_and_deleted_but_not_edited(allowed_client: Client) -> None:
    failed = _outbound("failed", "fallo@example.com")

    page = allowed_client.get(_failed_url("change", failed.pk))
    edit = allowed_client.post(_failed_url("change", failed.pk), {"recipient": "otro@example.com"})
    added = allowed_client.get(_failed_url("add"))
    deleted = allowed_client.post(_failed_url("delete", failed.pk), {"post": "yes"})

    assert page.status_code == 200
    assert edit.status_code == 403
    assert added.status_code == 403
    assert deleted.status_code == 302
    assert not OutboundEmail.objects.filter(pk=failed.pk).exists()


def test_a_pending_email_is_not_reachable_from_the_failed_list(allowed_client: Client) -> None:
    pending = _outbound("pending", "espera@example.com")

    response = allowed_client.get(_failed_url("change", pending.pk))

    assert response.status_code == 302
    assert OutboundEmail.objects.filter(pk=pending.pk).exists()


def test_staff_outside_support_cannot_reach_the_failed_emails() -> None:
    client = _client(make_user(is_staff=True))

    assert client.get(_failed_url("changelist")).status_code == 403
