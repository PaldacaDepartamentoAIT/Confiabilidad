import argparse
import getpass
from datetime import date
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from apps.accounts import registration
from apps.accounts.management.console import format_validation_error, show_code

VERIFY_ERRORS = {
    registration.VerifyResult.WRONG_CODE: gettext_noop("Wrong code."),
    registration.VerifyResult.LOCKED: gettext_noop("Too many failed attempts; request a new code."),
    registration.VerifyResult.CODE_EXPIRED: gettext_noop(
        "The code has expired; request a new code."
    ),
    registration.VerifyResult.EXPIRED: gettext_noop("The registration has expired; start again."),
    registration.VerifyResult.ALREADY_VERIFIED: gettext_noop("The code was already verified."),
    registration.VerifyResult.NOT_FOUND: gettext_noop("Unknown registration."),
}
RESEND_ERRORS = {
    registration.ResendRefusal.EXPIRED: gettext_noop("The registration has expired; start again."),
    registration.ResendRefusal.ALREADY_VERIFIED: gettext_noop("The code was already verified."),
    registration.ResendRefusal.NOT_FOUND: gettext_noop("Unknown registration."),
}


COMPLETE_ERRORS = {
    registration.CompleteRefusal.NOT_FOUND: gettext_noop("Unknown registration."),
    registration.CompleteRefusal.EXPIRED: gettext_noop(
        "The registration has expired; start again."
    ),
    registration.CompleteRefusal.CODE_NOT_VERIFIED: gettext_noop(
        "Verify the code before completing."
    ),
    registration.CompleteRefusal.ACCOUNT_EXISTS: gettext_noop(
        "An account with this email already exists; the registration was deleted."
    ),
}


def _birthdate(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(_("Birthdate must be YYYY-MM-DD.")) from error


class Command(BaseCommand):
    help = (
        "Run the pending registration from the console: "
        "start, verify, resend, complete and purge."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        actions = parser.add_subparsers(dest="action", required=True)
        start = actions.add_parser("start", help="Start a registration and show its code.")
        start.add_argument("--email", required=True)
        start.add_argument("--name", required=True)
        start.add_argument("--birthdate", required=True, type=_birthdate)
        start.add_argument("--country", required=True)
        verify = actions.add_parser("verify", help="Check the code of a registration.")
        verify.add_argument("public_id")
        verify.add_argument("code")
        resend = actions.add_parser("resend", help="Issue a new code for a registration.")
        resend.add_argument("public_id")
        complete = actions.add_parser(
            "complete", help="Create the account; asks for the password if not given."
        )
        complete.add_argument("public_id")
        complete.add_argument("--password", help="Visible in the shell history; avoid it.")
        actions.add_parser("purge", help="Delete expired registrations.")

    def handle(self, *args: Any, **options: Any) -> None:
        getattr(self, f"_{options['action']}")(options)

    def _start(self, options: dict[str, Any]) -> None:
        try:
            result = registration.start(
                email=options["email"],
                name=options["name"],
                birthdate=options["birthdate"],
                country=options["country"],
            )
        except ValidationError as error:
            raise CommandError(format_validation_error(error)) from error
        if isinstance(result, registration.AccountExists):
            raise CommandError(_("An account with this email already exists."))
        show_code(self.stdout, result.public_id, result.code)

    def _verify(self, options: dict[str, Any]) -> None:
        result = registration.verify(public_id=options["public_id"], code=options["code"])
        if result != registration.VerifyResult.VERIFIED:
            raise CommandError(_(VERIFY_ERRORS[result]))
        self.stdout.write(f"public_id: {options['public_id']}\n" + _("Code verified."))

    def _resend(self, options: dict[str, Any]) -> None:
        result = registration.resend(public_id=options["public_id"])
        if not isinstance(result, registration.Resent):
            raise CommandError(_(RESEND_ERRORS[result]))
        show_code(self.stdout, result.public_id, result.code)

    def _complete(self, options: dict[str, Any]) -> None:
        password = options["password"] or getpass.getpass(_("Password: "))
        try:
            result = registration.complete(public_id=options["public_id"], password=password)
        except ValidationError as error:
            raise CommandError(format_validation_error(error)) from error
        if not isinstance(result, registration.Completed):
            raise CommandError(_(COMPLETE_ERRORS[result]))
        self.stdout.write(f"public_id: {options['public_id']}\naccount: {result.user.email}")

    def _purge(self, options: dict[str, Any]) -> None:
        self.stdout.write(f"deleted: {registration.purge_expired()}")
