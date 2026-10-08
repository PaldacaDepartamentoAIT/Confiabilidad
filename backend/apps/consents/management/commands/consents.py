from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.translation import gettext as _

from apps.accounts.models import User
from apps.consents import services
from apps.consents.models import Terms
from apps.consents.validators import LOCALES
from apps.consents.versions import current_document


class Command(BaseCommand):
    help = (
        "Manage legal consents from the console: show the current document, accept terms, "
        "grant or revoke marketing and show a user's status."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        actions = parser.add_subparsers(dest="action", required=True)
        current = actions.add_parser("current", help="Show the current document in a language.")
        current.add_argument("--kind", required=True, choices=Terms.Kind.values)
        current.add_argument("--locale", required=True, choices=LOCALES)
        accept = actions.add_parser("accept-terms", help="Accept a terms document for a user.")
        accept.add_argument("email")
        accept.add_argument("--version", required=True)
        accept.add_argument("--locale", required=True, choices=LOCALES)
        grant = actions.add_parser("grant-marketing", help="Grant marketing consent for a user.")
        grant.add_argument("email")
        grant.add_argument("--version", required=True)
        grant.add_argument("--locale", required=True, choices=LOCALES)
        revoke = actions.add_parser("revoke-marketing", help="Revoke a user's marketing consent.")
        revoke.add_argument("email")
        status = actions.add_parser("status", help="Show a user's consent status.")
        status.add_argument("email")

    def handle(self, *args: Any, **options: Any) -> None:
        getattr(self, f"_{options['action'].replace('-', '_')}")(options)

    def _current(self, options: dict[str, Any]) -> None:
        document = current_document(options["kind"], options["locale"])
        if document is None:
            raise CommandError(_("There is no current version of this document."))
        published_at = document.published_at.isoformat() if document.published_at else ""
        self.stdout.write(
            f"kind: {document.kind}\nversion: {document.version}\n"
            f"locale: {document.locale}\npublished_at: {published_at}\n\n{document.content}"
        )

    def _accept_terms(self, options: dict[str, Any]) -> None:
        user = _user(options["email"])
        try:
            acceptance = services.accept_terms(
                user, version=options["version"], locale=options["locale"]
            )
        except ValidationError as error:
            raise CommandError("\n".join(error.messages)) from error
        self.stdout.write(
            f"accepted: {acceptance.terms}\naccepted_at: {acceptance.terms_accepted_at.isoformat()}"
        )

    def _grant_marketing(self, options: dict[str, Any]) -> None:
        user = _user(options["email"])
        try:
            consent = services.grant_marketing(
                user, version=options["version"], locale=options["locale"]
            )
        except ValidationError as error:
            raise CommandError("\n".join(error.messages)) from error
        self.stdout.write(f"granted: {consent.terms}\ngranted_at: {consent.granted_at.isoformat()}")

    def _revoke_marketing(self, options: dict[str, Any]) -> None:
        consent = services.revoke_marketing(_user(options["email"]))
        if consent is None or consent.revoked_at is None:
            self.stdout.write("revoked: none")
            return
        self.stdout.write(f"revoked: {consent.terms}\nrevoked_at: {consent.revoked_at.isoformat()}")

    def _status(self, options: dict[str, Any]) -> None:
        status = services.consent_status(_user(options["email"]))
        marketing = status.marketing.terms if status.marketing is not None else "none"
        self.stdout.write(f"terms: {status.terms}\nmarketing: {marketing}")


def _user(email: str) -> User:
    user = User.objects.filter(email__iexact=email.strip()).first()
    if user is None:
        raise CommandError(_("Unknown user: %(email)s.") % {"email": email})
    return user
