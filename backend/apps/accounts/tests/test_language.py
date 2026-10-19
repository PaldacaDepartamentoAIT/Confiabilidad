from collections.abc import Iterator
from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.state import StateApps

from apps.accounts.models import PendingRegistration, User
from apps.accounts.tests.factories import make_user

BEFORE_LANGUAGE = [("accounts", "0006_passwordresetrequest")]


@pytest.mark.parametrize("model", [User, PendingRegistration])
def test_language_admits_the_three_languages_and_defaults_to_spanish(
    model: type[User | PendingRegistration],
) -> None:
    field = model._meta.get_field("language")

    assert [value for value, _ in field.choices] == ["es", "pt-BR", "en"]  # type: ignore[union-attr]
    assert field.default == "es"


@pytest.mark.django_db
def test_an_account_rejects_an_unsupported_language() -> None:
    with pytest.raises(ValidationError) as error:
        make_user(language="fr")

    assert "language" in error.value.error_dict


@pytest.mark.django_db
def test_a_pending_registration_rejects_an_unsupported_language() -> None:
    pending = PendingRegistration(
        email="nueva@example.com",
        name="Ana",
        birthdate=date(1990, 1, 1),
        country="ES",
        language="fr",
        public_id="x",
        code_hash="h",
        code_expires_at="2030-01-01T00:00:00Z",
    )

    with pytest.raises(ValidationError) as error:
        pending.save()

    assert "language" in error.value.error_dict


@pytest.mark.django_db
def test_a_language_change_is_kept_in_the_account_history() -> None:
    user = make_user()
    user.language = "pt-BR"
    user.save()

    assert user.history.latest("history_date").language == "pt-BR"


def _migrate(targets: list[tuple[str, str]]) -> StateApps:
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps


@pytest.fixture
def before_language(transactional_db: None) -> Iterator[StateApps]:
    yield _migrate(BEFORE_LANGUAGE)
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM accounts_user")
    _migrate(MigrationExecutor(connection).loader.graph.leaf_nodes("accounts"))


def test_an_existing_account_is_left_in_spanish(before_language: StateApps) -> None:
    old_user = before_language.get_model("accounts", "User")
    old_user.objects.create(
        email="vieja@example.com", name="Ana", birthdate=date(1990, 1, 1), country="ES"
    )

    _migrate(MigrationExecutor(connection).loader.graph.leaf_nodes("accounts"))

    assert User.objects.get(email="vieja@example.com").language == "es"
