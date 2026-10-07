import argparse
from datetime import date
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.translation import gettext as _

from apps.accounts import registration

VERIFY_ERRORS = {
    registration.VerifyResult.WRONG_CODE: "Wrong code.",
    registration.VerifyResult.LOCKED: "Too many failed attempts; request a new code.",
    registration.VerifyResult.CODE_EXPIRED: "The code has expired; request a new code.",
    registration.VerifyResult.EXPIRED: "The registration has expired; start again.",
    registration.VerifyResult.ALREADY_VERIFIED: "The code was already verified.",
    registration.VerifyResult.NOT_FOUND: "Unknown registration.",
}
RESEND_ERRORS = {
    registration.ResendRefusal.EXPIRED: "The registration has expired; start again.",
    registration.ResendRefusal.ALREADY_VERIFIED: "The code was already verified.",
    registration.ResendRefusal.NOT_FOUND: "Unknown registration.",
}


def _birthdate(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(_("Birthdate must be YYYY-MM-DD.")) from error


class Command(BaseCommand):
    help = "Run the pending registration from the console: start, verify and resend."

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
            raise CommandError(_format(error)) from error
        if isinstance(result, registration.AccountExists):
            raise CommandError(_("An account with this email already exists."))
        self._show_code(result.public_id, result.code)

    def _verify(self, options: dict[str, Any]) -> None:
        result = registration.verify(public_id=options["public_id"], code=options["code"])
        if result != registration.VerifyResult.VERIFIED:
            raise CommandError(_(VERIFY_ERRORS[result]))
        self.stdout.write(f"public_id: {options['public_id']}\n" + _("Code verified."))

    def _resend(self, options: dict[str, Any]) -> None:
        result = registration.resend(public_id=options["public_id"])
        if not isinstance(result, registration.Resent):
            raise CommandError(_(RESEND_ERRORS[result]))
        self._show_code(result.public_id, result.code)

    def _show_code(self, public_id: str, code: str) -> None:
        self.stdout.write(f"public_id: {public_id}\ncode: {code}")


def _format(error: ValidationError) -> str:
    return "\n".join(
        f"{field}: {message}"
        for field, messages in error.message_dict.items()
        for message in messages
    )
