from datetime import timedelta

from celery import current_app
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

from apps.emails import rendering
from apps.emails.models import EmailTemplate, OutboundEmail
from apps.emails.outbox import DELIVER_TASK

# Mientras dura la reserva, ningún otro intento toma la misma fila (D-04).
LEASE = timedelta(minutes=5)


def deliver(email_id: int) -> None:
    email = _claim(email_id)
    if email is None:
        return
    template = EmailTemplate.objects.get(kind=email.kind, locale=email.locale)
    subject, body = rendering.compose(
        email.kind, email.locale, template.subject, template.body, email.context
    )
    EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [email.recipient]).send()
    email.delete()


def dispatch_due() -> int:
    due = list(
        OutboundEmail.objects.filter(
            status=OutboundEmail.Status.PENDING, next_attempt_at__lte=timezone.now()
        ).values_list("pk", flat=True)
    )
    for email_id in due:
        current_app.send_task(DELIVER_TASK, args=[email_id])
    return len(due)


def _claim(email_id: int) -> OutboundEmail | None:
    with transaction.atomic():
        email = (
            OutboundEmail.objects.select_for_update(skip_locked=True)
            .filter(
                pk=email_id,
                status=OutboundEmail.Status.PENDING,
                next_attempt_at__lte=timezone.now(),
            )
            .first()
        )
        if email is not None:
            email.next_attempt_at = timezone.now() + LEASE
            email.save(update_fields=["next_attempt_at"])
        return email
