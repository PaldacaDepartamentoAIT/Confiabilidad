import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING

from celery import current_app
from django.db import transaction

from apps.emails import locales, rendering
from apps.emails.models import OutboundEmail

if TYPE_CHECKING:
    from apps.accounts.models import User

logger = logging.getLogger(__name__)

DELIVER_TASK = "apps.emails.tasks.deliver"


def enqueue(
    *,
    kind: str,
    recipient: str,
    locale: str,
    context: Mapping[str, str] | None = None,
    account: "User | None" = None,
) -> OutboundEmail:
    email = OutboundEmail.objects.create(
        kind=kind,
        recipient=recipient,
        locale=_language(kind, locale, account),
        context=dict(context or {}),
    )
    transaction.on_commit(lambda: _queue(email.pk))
    return email


def _queue(email_id: int) -> None:
    # Si la cola no responde, el correo queda pendiente y lo recoge el barrido periódico (D-01).
    try:
        current_app.send_task(DELIVER_TASK, args=[email_id])
    except Exception:
        logger.warning("Could not queue outbound email %s; the sweep will retry it.", email_id)


def _language(kind: str, requested: str, account: "User | None") -> str:
    # Un aviso va en el idioma del titular, nunca en el de quien lo provoca (S-02).
    if account is not None and kind not in rendering.CODE_KINDS:
        return locales.normalize(account.language)
    return locales.normalize(requested)
