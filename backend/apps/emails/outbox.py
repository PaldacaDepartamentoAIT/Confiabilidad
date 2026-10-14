import logging
from collections.abc import Mapping

from celery import current_app
from django.db import transaction

from apps.emails.models import OutboundEmail

logger = logging.getLogger(__name__)

DELIVER_TASK = "apps.emails.tasks.deliver"


def enqueue(
    *, kind: str, recipient: str, locale: str, context: Mapping[str, str] | None = None
) -> OutboundEmail:
    email = OutboundEmail.objects.create(
        kind=kind, recipient=recipient, locale=locale, context=dict(context or {})
    )
    transaction.on_commit(lambda: _queue(email.pk))
    return email


def _queue(email_id: int) -> None:
    # Si la cola no responde, el correo queda pendiente y lo recoge el barrido periódico (D-01).
    try:
        current_app.send_task(DELIVER_TASK, args=[email_id])
    except Exception:
        logger.warning("Could not queue outbound email %s; the sweep will retry it.", email_id)
