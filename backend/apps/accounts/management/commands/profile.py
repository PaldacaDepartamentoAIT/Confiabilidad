import argparse
import getpass
from datetime import date
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.translation import gettext as _

from apps.accounts import profile
from apps.accounts.management.console import format_validation_error
from apps.accounts.models import User


def _birthdate(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(_("Birthdate must be YYYY-MM-DD.")) from error


def _active_user(email: str) -> User:
    user = User.active.filter(email__iexact=email.strip()).first()
    if user is None:
        raise CommandError(_("Unknown or inactive account: %(email)s") % {"email": email})
    return user


class Command(BaseCommand):
    help = "Inspect or edit an active account profile from the console."

    def add_arguments(self, parser: CommandParser) -> None:
        actions = parser.add_subparsers(dest="action", required=True)
        show = actions.add_parser("show", help="Show an account profile.")
        show.add_argument("--email", required=True)

        edit = actions.add_parser("edit", help="Update profile fields of an account.")
        edit.add_argument("--email", required=True)
        edit.add_argument("--name")
        edit.add_argument("--birthdate", type=_birthdate)
        edit.add_argument("--country")

        change_pw = actions.add_parser(
            "change-password",
            help="Change password using the current one; closes other sessions.",
        )
        change_pw.add_argument("--email", required=True)
        change_pw.add_argument("--current-password", help="Visible in shell history; avoid it.")
        change_pw.add_argument("--new-password", help="Visible in shell history; avoid it.")
        change_pw.add_argument("--keep-session-key", default=None)

    def handle(self, *args: Any, **options: Any) -> None:
        action = str(options["action"]).replace("-", "_")
        getattr(self, f"_{action}")(options)

    def _show(self, options: dict[str, Any]) -> None:
        user = _active_user(options["email"])
        self._write_profile(profile.get_profile(user))

    def _edit(self, options: dict[str, Any]) -> None:
        if options["name"] is None and options["birthdate"] is None and options["country"] is None:
            raise CommandError(_("Provide at least one of --name, --birthdate or --country."))
        user = _active_user(options["email"])
        try:
            updated = profile.update_profile(
                user,
                name=options["name"] if options["name"] is not None else profile.UNSET,
                birthdate=(
                    options["birthdate"] if options["birthdate"] is not None else profile.UNSET
                ),
                country=options["country"] if options["country"] is not None else profile.UNSET,
            )
        except ValidationError as error:
            raise CommandError(format_validation_error(error)) from error
        self._write_profile(updated)

    def _write_profile(self, data: profile.ProfileData) -> None:
        self.stdout.write(
            f"email: {data.email}\n"
            f"name: {data.name}\n"
            f"birthdate: {data.birthdate.isoformat()}\n"
            f"country: {data.country}"
        )

    def _change_password(self, options: dict[str, Any]) -> None:
        user = _active_user(options["email"])
        current = options["current_password"]
        if current is None:
            current = getpass.getpass(_("Current password: "))
        new = options["new_password"]
        if new is None:
            new = getpass.getpass(_("New password: "))
        result = profile.change_password(
            user,
            current_password=current,
            new_password=new,
            current_session_key=options["keep_session_key"],
        )
        if isinstance(result, profile.PasswordChangeLocked):
            raise CommandError(
                _("Too many failed attempts. Wait %(seconds)d seconds.")
                % {"seconds": result.retry_after}
            )
        if isinstance(result, profile.PasswordChangeInvalid):
            reasons: list[str] = []
            if result.current_password_incorrect:
                reasons.append(_("Current password is incorrect."))
            reasons.extend(result.new_password_codes)
            if not reasons:
                reasons.append(_("New password is required."))
            raise CommandError("\n".join(reasons))
        self.stdout.write(
            f"account: {result.user.email}\nrevoked_sessions: {result.revoked_sessions}"
        )
