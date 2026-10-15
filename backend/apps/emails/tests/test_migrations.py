import importlib
from collections.abc import Iterator

import pytest
from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Group, Permission
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from apps.emails import rendering
from apps.emails.models import EmailTemplate

INITIAL = ("emails", "0002_initial_templates")
BEFORE_HISTORY = ("emails", "0003_support_permissions")
HISTORY = ("emails", "0004_initial_template_history")
SCHEMA_ONLY = ("emails", "0001_initial")


def _migrate(target: tuple[str, str]) -> None:
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate([target])


def _latest() -> tuple[str, str]:
    executor = MigrationExecutor(connection)
    names: list[str] = [name for app, name in executor.loader.graph.leaf_nodes() if app == "emails"]
    return ("emails", names[0])


@pytest.fixture
def schema_only(transactional_db: None) -> Iterator[None]:
    _migrate(SCHEMA_ONLY)
    yield
    _migrate(_latest())


def test_the_initial_migration_creates_every_kind_in_every_language(schema_only: None) -> None:
    assert EmailTemplate.objects.count() == 0

    _migrate(INITIAL)

    pairs = set(EmailTemplate.objects.values_list("kind", "locale"))
    assert pairs == {
        (kind, locale)
        for kind in EmailTemplate.Kind.values
        for locale in EmailTemplate.Locale.values
    }


def test_every_initial_template_is_valid(schema_only: None, settings: object) -> None:
    settings.FRONTEND_BASE_URL = "https://app.ejemplo.com"  # type: ignore[attr-defined]
    _migrate(INITIAL)

    for template in EmailTemplate.objects.all():
        rendering.validate_template(template.kind, template.subject, template.body)


def test_rolling_back_deletes_the_initial_templates(schema_only: None) -> None:
    _migrate(INITIAL)

    _migrate(SCHEMA_ONLY)

    assert EmailTemplate.objects.count() == 0


def test_creating_the_initial_templates_keeps_edited_ones(schema_only: None) -> None:
    _migrate(INITIAL)
    template = EmailTemplate.objects.get(kind="password_changed", locale="en")
    template.body = "Edited, {{ name }}."
    template.save()
    migration = importlib.import_module("apps.emails.migrations.0002_initial_templates")

    migration.create_initial_templates(global_apps, None)

    template.refresh_from_db()
    assert template.body == "Edited, {{ name }}."
    assert EmailTemplate.objects.count() == 21


SUPPORT_GROUP = "Soporte técnico"
EMAIL_PERMISSIONS = {
    ("emails", "view_emailtemplate"),
    ("emails", "change_emailtemplate"),
    ("emails", "view_failedemail"),
    ("emails", "delete_failedemail"),
}
PERMISSIONS = ("emails", "0003_support_permissions")


def _group_permissions() -> set[tuple[str, str]]:
    group = Group.objects.get(name=SUPPORT_GROUP)
    return set(group.permissions.values_list("content_type__app_label", "codename"))


@pytest.fixture
def before_permissions(transactional_db: None) -> Iterator[None]:
    _migrate(INITIAL)
    # Otros tests transaccionales pueden haber vaciado el grupo que crea `consents.0002`.
    Group.objects.get_or_create(name=SUPPORT_GROUP)
    yield
    _migrate(_latest())


def test_support_gets_the_email_permissions_on_top_of_its_own(before_permissions: None) -> None:
    consents_before = {perm for perm in _group_permissions() if perm[0] == "consents"}

    _migrate(PERMISSIONS)

    permissions = _group_permissions()
    assert EMAIL_PERMISSIONS <= permissions
    assert {perm for perm in permissions if perm[0] == "consents"} == consents_before
    assert {perm for perm in permissions if perm[0] == "emails"} == EMAIL_PERMISSIONS


def test_rolling_back_removes_only_the_email_permissions(before_permissions: None) -> None:
    _migrate(PERMISSIONS)
    create_permissions(global_apps.get_app_config("consents"), verbosity=0)
    Group.objects.get(name=SUPPORT_GROUP).permissions.add(
        Permission.objects.get(content_type__app_label="consents", codename="view_userterms")
    )
    consents_permissions = {perm for perm in _group_permissions() if perm[0] == "consents"}

    _migrate(INITIAL)

    assert _group_permissions() == consents_permissions
    assert ("consents", "view_userterms") in consents_permissions


def _history() -> list[tuple[int, str, str, str, str]]:
    return list(
        EmailTemplate.history.order_by("id", "history_id").values_list(
            "id", "history_type", "subject", "body", "history_change_reason"
        )
    )


def test_every_initial_template_gets_its_text_in_the_history(schema_only: None) -> None:
    _migrate(HISTORY)

    expected = [
        (template.pk, "+", template.subject, template.body, "Initial text")
        for template in EmailTemplate.objects.order_by("id")
    ]
    assert len(expected) == 21
    assert _history() == expected


def test_recording_the_initial_history_again_adds_nothing(schema_only: None) -> None:
    _migrate(HISTORY)
    before = _history()
    migration = importlib.import_module("apps.emails.migrations.0004_initial_template_history")

    migration.record_initial_history(global_apps, None)

    assert _history() == before


def test_a_template_with_history_keeps_it_untouched(schema_only: None) -> None:
    _migrate(BEFORE_HISTORY)
    template = EmailTemplate.objects.get(kind="password_changed", locale="en")
    template.body = "Edited, {{ name }}."
    template.save()

    _migrate(HISTORY)

    assert list(
        EmailTemplate.history.filter(id=template.pk).values_list("history_type", "body")
    ) == [("~", "Edited, {{ name }}.")]


def test_rolling_back_removes_only_the_initial_history(schema_only: None) -> None:
    _migrate(HISTORY)
    template = EmailTemplate.objects.get(kind="password_changed", locale="en")
    template.body = "Edited, {{ name }}."
    template.save()

    _migrate(BEFORE_HISTORY)

    assert list(EmailTemplate.history.values_list("id", "history_type")) == [(template.pk, "~")]
