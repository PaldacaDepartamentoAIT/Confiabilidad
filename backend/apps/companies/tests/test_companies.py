from io import StringIO

import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import ProtectedError

from apps.accounts.tests.factories import make_user
from apps.companies.admin import CompanyAdmin
from apps.companies.models import Company, owns_company


@pytest.mark.django_db
def test_user_can_own_multiple_companies_with_non_unique_names() -> None:
    owner = make_user()
    other = make_user()

    assert owns_company(owner) is False

    first = Company.objects.create(name="  Planta Norte  ", owner=owner)
    second = Company.objects.create(name="Planta Norte", owner=owner)

    assert first.name == "Planta Norte"
    assert second.name == "Planta Norte"
    assert first.pk != second.pk
    assert owns_company(owner) is True
    assert owns_company(other) is False


@pytest.mark.django_db
def test_company_rejects_blank_name() -> None:
    owner = make_user()
    with pytest.raises(ValidationError):
        Company.objects.create(name="   ", owner=owner)


@pytest.mark.django_db
def test_company_owner_uses_protect_on_delete() -> None:
    owner = make_user()
    Company.objects.create(name="Planta Sur", owner=owner)

    with pytest.raises(ProtectedError):
        owner.delete()


def test_company_is_registered_in_admin() -> None:
    assert isinstance(admin.site._registry.get(Company), CompanyAdmin)


@pytest.mark.django_db
def test_company_models_have_no_pending_migrations() -> None:
    call_command("makemigrations", "companies", "--check", "--dry-run", stdout=StringIO())


@pytest.mark.django_db
def test_company_cli_create_list_and_delete() -> None:
    owner = make_user(email="owner@example.com")
    inactive = make_user(email="inactive@example.com", is_active=False)

    with pytest.raises(CommandError, match="Unknown or inactive"):
        call_command("company", "create", "--email", inactive.email, "--name", "No Entra")

    create_out = StringIO()
    call_command(
        "company",
        "create",
        "--email",
        "OWNER@EXAMPLE.COM",
        "--name",
        "Planta Centro",
        stdout=create_out,
    )
    created = Company.objects.get(owner=owner)
    assert created.name == "Planta Centro"
    assert f"id={created.pk}" in create_out.getvalue()

    list_out = StringIO()
    call_command("company", "list", "--email", owner.email, stdout=list_out)
    assert "Planta Centro" in list_out.getvalue()

    delete_out = StringIO()
    call_command("company", "delete", "--id", str(created.pk), stdout=delete_out)
    assert not Company.objects.filter(pk=created.pk).exists()
    assert owns_company(owner) is False
