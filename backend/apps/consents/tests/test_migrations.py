from collections.abc import Iterator

import pytest
from django.contrib.auth.models import Group
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

SUPPORT_GROUP = "Soporte técnico"
SUPPORT_PERMISSIONS = {
    f"{action}_{model}"
    for action in ("view", "add", "change", "delete")
    for model in ("userterms", "marketingconsent")
}


def _migrate(target: tuple[str, str]) -> None:
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate([target])


@pytest.mark.django_db
def test_support_group_has_the_acceptance_and_consent_permissions() -> None:
    group = Group.objects.get(name=SUPPORT_GROUP)

    codenames = set(group.permissions.values_list("codename", flat=True))
    app_labels = set(group.permissions.values_list("content_type__app_label", flat=True))

    assert codenames == SUPPORT_PERMISSIONS
    assert app_labels == {"consents"}


@pytest.fixture
def rolled_back(transactional_db: None) -> Iterator[None]:
    _migrate(("consents", "0001_initial"))
    yield
    _migrate(("consents", "0002_support_group"))


def test_rolling_back_the_migration_deletes_the_group(rolled_back: None) -> None:
    assert not Group.objects.filter(name=SUPPORT_GROUP).exists()


def test_migrating_again_recreates_the_group(rolled_back: None) -> None:
    _migrate(("consents", "0002_support_group"))

    group = Group.objects.get(name=SUPPORT_GROUP)
    assert set(group.permissions.values_list("codename", flat=True)) == SUPPORT_PERMISSIONS
