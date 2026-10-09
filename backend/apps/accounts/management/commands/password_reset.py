import getpass
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from apps.accounts import password_reset
from apps.accounts.management.console import format_validation_error, show_code

EXPIRED = gettext_noop("The password reset request has expired; start again.")
ALREADY_VERIFIED = gettext_noop("The code was already verified.")
NOT_FOUND = gettext_noop("Unknown password reset request.")

VERIFY_ERRORS: dict[str, str] = {
    password_reset.VerifyResult.WRONG_CODE: gettext_noop("Wrong code."),
    password_reset.VerifyResult.LOCKED: gettext_noop(
        "Too many failed attempts; request a new code."
    ),
    password_reset.VerifyResult.CODE_EXPIRED: gettext_noop(
        "The code has expired; request a new code."
    ),
    password_reset.VerifyResult.EXPIRED: EXPIRED,
    password_reset.VerifyResult.ALREADY_VERIFIED: ALREADY_VERIFIED,
    password_reset.VerifyResult.NOT_FOUND: NOT_FOUND,
}
RESEND_ERRORS: dict[str, str] = {
    password_reset.ResendRefusal.EXPIRED: EXPIRED,
    password_reset.ResendRefusal.ALREADY_VERIFIED: ALREADY_VERIFIED,
    password_reset.ResendRefusal.NOT_FOUND: NOT_FOUND,
}
COMPLETE_ERRORS: dict[str, str] = {
    password_reset.CompleteRefusal.NOT_FOUND: NOT_FOUND,
    password_reset.CompleteRefusal.EXPIRED: EXPIRED,
    password_reset.CompleteRefusal.CODE_NOT_VERIFIED: gettext_noop(
        "Verify the code before completing."
    ),
}
ACCOUNT_ERRORS: dict[str, str] = {
    password_reset.AccountRefusal.INACTIVE: gettext_noop("The account is inactive."),
    password_reset.AccountRefusal.ACCOUNT_CHANGED: gettext_noop(
        "The account's email or password changed after the request; start again."
    ),
}


class Command(BaseCommand):
    help = "Run the password reset from the console: start, verify, resend, complete and purge."

    def add_arguments(self, parser: CommandParser) -> None:
        actions = parser.add_subparsers(dest="action", required=True)
        start = actions.add_parser("start", help="Request a password reset and show its code.")
        start.add_argument("--email", required=True)
        verify = actions.add_parser("verify", help="Check the code of a request.")
        verify.add_argument("public_id")
        verify.add_argument("code")
        resend = actions.add_parser("resend", help="Issue a new code for a request.")
        resend.add_argument("public_id")
        complete = actions.add_parser(
            "complete", help="Set the new password; asks for it if not given."
        )
        complete.add_argument("public_id")
        complete.add_argument("--password", help="Visible in the shell history; avoid it.")
        actions.add_parser("purge", help="Delete expired requests.")

    def handle(self, *args: Any, **options: Any) -> None:
        getattr(self, f"_{options['action']}")(options)

    def _start(self, options: dict[str, Any]) -> None:
        result = password_reset.start(email=options["email"])
        if isinstance(result, password_reset.NoEligibleAccount):
            raise CommandError(_("No active account with this email."))
        show_code(self.stdout, result.public_id, result.code)

    def _verify(self, options: dict[str, Any]) -> None:
        result = password_reset.verify(public_id=options["public_id"], code=options["code"])
        if result != password_reset.VerifyResult.VERIFIED:
            raise CommandError(_({**VERIFY_ERRORS, **ACCOUNT_ERRORS}[result]))
        self.stdout.write(f"public_id: {options['public_id']}\n" + _("Code verified."))

    def _resend(self, options: dict[str, Any]) -> None:
        result = password_reset.resend(public_id=options["public_id"])
        if not isinstance(result, password_reset.Resent):
            raise CommandError(_({**RESEND_ERRORS, **ACCOUNT_ERRORS}[result]))
        show_code(self.stdout, result.public_id, result.code)

    def _complete(self, options: dict[str, Any]) -> None:
        password = options["password"] or getpass.getpass(_("Password: "))
        try:
            result = password_reset.complete(public_id=options["public_id"], password=password)
        except ValidationError as error:
            raise CommandError(format_validation_error(error)) from error
        if not isinstance(result, password_reset.Completed):
            raise CommandError(_({**COMPLETE_ERRORS, **ACCOUNT_ERRORS}[result]))
        self.stdout.write(f"public_id: {options['public_id']}\naccount: {result.user.email}")

    def _purge(self, options: dict[str, Any]) -> None:
        self.stdout.write(f"deleted: {password_reset.purge_expired()}")
