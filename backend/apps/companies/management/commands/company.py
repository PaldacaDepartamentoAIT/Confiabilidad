from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.translation import gettext as _

from apps.accounts.management.console import format_validation_error
from apps.accounts.models import User
from apps.companies.models import Company


class Command(BaseCommand):
    help = "Create, list, or delete preliminary companies from the console."

    def add_arguments(self, parser: CommandParser) -> None:
        actions = parser.add_subparsers(dest="action", required=True)

        create_parser = actions.add_parser("create", help="Create a preliminary company.")
        create_parser.add_argument("--email", required=True)
        create_parser.add_argument("--name", required=True)

        list_parser = actions.add_parser("list", help="List companies, optionally by owner.")
        list_parser.add_argument("--email", default="")

        delete_parser = actions.add_parser("delete", help="Delete a preliminary company.")
        delete_parser.add_argument("--id", type=int, required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        action = str(options["action"])
        getattr(self, f"_{action}")(options)

    def _create(self, options: dict[str, Any]) -> None:
        email = str(options["email"]).strip()
        owner = User.active.filter(email__iexact=email).first()
        if owner is None:
            raise CommandError(_("Unknown or inactive account: %(email)s") % {"email": email})
        try:
            company = Company.objects.create(name=str(options["name"]), owner=owner)
        except ValidationError as error:
            raise CommandError(format_validation_error(error)) from error
        self.stdout.write(f"id={company.pk} name={company.name} owner={owner.email}")

    def _list(self, options: dict[str, Any]) -> None:
        queryset = Company.objects.select_related("owner").order_by("id")
        email = str(options["email"]).strip()
        if email:
            queryset = queryset.filter(owner__email__iexact=email)
        rows = list(queryset)
        if not rows:
            self.stdout.write("none")
            return
        for item in rows:
            self.stdout.write(f"id={item.pk} name={item.name} owner={item.owner.email}")

    def _delete(self, options: dict[str, Any]) -> None:
        company_id = int(options["id"])
        deleted, _details = Company.objects.filter(pk=company_id).delete()
        if not deleted:
            raise CommandError(_("Unknown company id: %(id)s") % {"id": company_id})
        self.stdout.write(f"deleted={company_id}")
