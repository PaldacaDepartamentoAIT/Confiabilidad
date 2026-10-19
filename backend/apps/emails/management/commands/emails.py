from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.core.validators import validate_email
from django.db import transaction
from django.utils.translation import gettext as _

from apps.emails import delivery, locales, outbox, rendering
from apps.emails.models import EmailTemplate, OutboundEmail

SAMPLE_NAME = "Ana Ejemplo"
SAMPLE_CODE = "123456"
SAMPLE_PUBLIC_ID = "sample"
SAMPLE_LIFETIME = timedelta(minutes=15)
_CODE_PURPOSES = {"registration_code": "registration", "password_reset_code": "password_reset"}
# Avisos cuya acción aún no existe: se envían a mano a una cuenta (RF-009).
NOTIFY_KINDS = ["password_changed", "account_disabled", "sessions_closed"]


class Command(BaseCommand):
    help = "Queue emails from the console: a sample, a notice to an account, or the due ones."

    def add_arguments(self, parser: CommandParser) -> None:
        actions = parser.add_subparsers(dest="action", required=True)
        test = actions.add_parser("test", help="Queue a sample email with example data.")
        test.add_argument("--kind", required=True, choices=EmailTemplate.Kind.values)
        test.add_argument("--locale", required=True, choices=locales.SUPPORTED)
        test.add_argument("--to", required=True)
        notify = actions.add_parser("notify", help="Queue a security notice to an account.")
        notify.add_argument("--kind", required=True, choices=NOTIFY_KINDS)
        notify.add_argument("--email", required=True)
        actions.add_parser("dispatch", help="Queue every pending email that is due now.")

    def handle(self, *args: Any, **options: Any) -> None:
        getattr(self, f"_{options['action']}")(options)

    def _test(self, options: dict[str, Any]) -> None:
        kind, locale, recipient = options["kind"], options["locale"], options["to"]
        try:
            validate_email(recipient)
        except ValidationError as error:
            raise CommandError(_("Invalid email address: %(to)s") % {"to": recipient}) from error
        # El código de ejemplo no es secreto: va como dato del correo, sin máscara ni comprobación.
        context = {"name": SAMPLE_NAME}
        if kind in rendering.CODE_KINDS:
            context.update(
                code=SAMPLE_CODE,
                link=rendering.process_link(_CODE_PURPOSES[kind], SAMPLE_PUBLIC_ID),
                expires_in=rendering.expires_in(locale, SAMPLE_LIFETIME),
            )
        # Una prueba no es de ninguna cuenta: no lleva tope ni idioma de cuenta, se encola tal cual.
        email = OutboundEmail.objects.create(
            kind=kind, recipient=recipient, locale=locale, context=context
        )
        transaction.on_commit(lambda: outbox.queue(email.pk))
        self.stdout.write(f"queued: {email.pk} → {recipient} ({kind}, {locale})")

    def _notify(self, options: dict[str, Any]) -> None:
        user_model = get_user_model()
        account = user_model.objects.filter(email__iexact=options["email"].strip()).first()
        if account is None:
            raise CommandError(_("Unknown account: %(email)s") % {"email": options["email"]})
        email = outbox.enqueue(
            kind=options["kind"],
            recipient=account.email,
            locale=account.language,
            context={"name": account.name},
            account=account,
        )
        assert email is not None
        self.stdout.write(f"queued: {email.pk} → {account.email} ({email.kind}, {email.locale})")

    def _dispatch(self, options: dict[str, Any]) -> None:
        self.stdout.write(f"queued: {delivery.dispatch_due()}")
