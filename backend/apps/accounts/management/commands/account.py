import getpass
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.translation import gettext as _

from apps.accounts import disable
from apps.accounts.models import User


class Command(BaseCommand):
    help = "Disable or reactivate an account from the console."

    def add_arguments(self, parser: CommandParser) -> None:
        actions = parser.add_subparsers(dest="action", required=True)
        disable_parser = actions.add_parser("disable", help="Disable an active account.")
        disable_parser.add_argument("--email", required=True)
        disable_parser.add_argument(
            "--current-password",
            default=None,
            help="Visible in shell history; avoid passing inline.",
        )

        reactivate_parser = actions.add_parser(
            "reactivate", help="Reactivate a disabled account within the retention period."
        )
        reactivate_parser.add_argument("--email", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        action = str(options["action"]).replace("-", "_")
        getattr(self, f"_{action}")(options)

    def _disable(self, options: dict[str, Any]) -> None:
        email = str(options["email"]).strip()
        user = User.active.filter(email__iexact=email).first()
        if user is None:
            raise CommandError(_("Unknown or inactive account: %(email)s") % {"email": email})
        current = options["current_password"]
        if current is None:
            current = getpass.getpass(_("Current password: "))
        result = disable.disable_account(user, current_password=str(current))
        if isinstance(result, disable.DisableBlocked):
            if result.reason is disable.DisableBlockReason.OWNS_COMPANY:
                raise CommandError(_("You must transfer or delete your company first."))
            if result.reason is disable.DisableBlockReason.LAST_SUPERUSER:
                raise CommandError(_("Cannot disable the last active superuser."))
            raise CommandError(_("Account is already inactive."))
        if isinstance(result, disable.DisableLocked):
            raise CommandError(
                _("Too many failed attempts. Wait %(seconds)d seconds.")
                % {"seconds": result.retry_after}
            )
        if isinstance(result, disable.DisableInvalid):
            if result.missing_password:
                raise CommandError(_("Current password is required."))
            raise CommandError(_("Current password is incorrect."))
        self.stdout.write(f"disabled: {result.user.email}")

    def _reactivate(self, options: dict[str, Any]) -> None:
        email = str(options["email"]).strip()
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            raise CommandError(_("Unknown account: %(email)s") % {"email": email})
        result = disable.reactivate_account(user)
        if isinstance(result, disable.ReactivationAlreadyActive):
            raise CommandError(_("Account is already active: %(email)s") % {"email": email})
        if isinstance(result, disable.ReactivationExpired):
            raise CommandError(
                _("The 12-month reactivation period has expired for %(email)s.") % {"email": email}
            )
        self.stdout.write(f"reactivated: {result.user.email}")
