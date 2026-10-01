from collections.abc import Iterator
from datetime import date

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.state import StateApps

INITIAL = [("accounts", "0001_initial")]


def _latest() -> list[tuple[str, str]]:
    nodes: list[tuple[str, str]] = MigrationExecutor(connection).loader.graph.leaf_nodes("accounts")
    return nodes


def _migrate(targets: list[tuple[str, str]]) -> StateApps:
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps


def _stored_emails() -> list[str]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT email FROM accounts_user ORDER BY id")
        return [row[0] for row in cursor.fetchall()]


@pytest.fixture
def initial_apps(transactional_db: None) -> Iterator[StateApps]:
    yield _migrate(INITIAL)
    # Deja el esquema en la última migración aunque el test haya fallado a mitad.
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM accounts_user")
    _migrate(_latest())


def test_existing_accounts_are_kept_with_filler_and_lowercase_email(
    initial_apps: StateApps,
) -> None:
    old_user = initial_apps.get_model("accounts", "User")
    old_user.objects.create(email=" Old@Example.COM ", password="!")
    old_user.objects.create(email="other@example.com", password="!")

    apps = _migrate(_latest())

    user_model = apps.get_model("accounts", "User")
    assert user_model.objects.count() == 2
    migrated = user_model.objects.get(email="old@example.com")
    assert (migrated.name, migrated.birthdate, migrated.country) == (
        "Usuario sin nombre",
        date(1900, 1, 1),
        "ZZ",
    )
    assert not apps.get_model("accounts", "HistoricalUser").objects.exists()


def test_emails_differing_only_in_case_abort_the_migration(initial_apps: StateApps) -> None:
    old_user = initial_apps.get_model("accounts", "User")
    old_user.objects.create(email="ana@x.com", password="!")
    old_user.objects.create(email="Ana@X.com", password="!")

    with pytest.raises(RuntimeError, match="ana@x.com / Ana@X.com"):
        _migrate(_latest())

    assert _stored_emails() == ["ana@x.com", "Ana@X.com"]
