import importlib
from collections.abc import Iterator

import pytest
from django.apps import apps as global_apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from apps.emails import rendering
from apps.emails.models import EmailTemplate

INITIAL = ("emails", "0002_initial_templates")
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
