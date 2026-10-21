import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from celery import current_app
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import fingerprints
from apps.emails import rendering
from apps.emails.errors import Failure, classify
from apps.emails.models import EmailTemplate, OutboundEmail
from apps.emails.outbox import DELIVER_TASK

logger = logging.getLogger(__name__)

# Por propósito, cómo saber si el código de un correo sigue sirviendo: devuelve su caducidad o
# nada si está caducado, validado o reemplazado. Lo registra `accounts` al arrancar (D-05).
CodeCheck = Callable[[str, str], datetime | None]
_CODE_CHECKS: dict[str, CodeCheck] = {}


def register_code_check(purpose: str, check: CodeCheck) -> None:
    _CODE_CHECKS[purpose] = check


# Mientras dura la reserva, ningún otro intento toma la misma fila (D-04).
LEASE = timedelta(minutes=5)
FIRST_WAIT = timedelta(seconds=30)
MAX_WAIT = timedelta(minutes=15)


def deliver(email_id: int) -> None:
    email = _claim(email_id)
    if email is None:
        return
    values = {key: str(value) for key, value in email.context.items()}
    if email.masked_code is not None:
        code = fingerprints.unmask_code(email.masked_code, email.code_nonce)
        expiry = _code_expiry(email, code)
        if expiry is None:
            email.delete()
            return
        values["code"] = code
        values["expires_in"] = rendering.expires_in(email.locale, expiry - timezone.now())
        values["link"] = rendering.process_link(email.purpose, email.public_id)
    template = EmailTemplate.objects.get(kind=email.kind, locale=email.locale)
    subject, body = rendering.compose(
        email.kind, email.locale, template.subject, template.body, values
    )
    try:
        EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [email.recipient]).send()
    except Exception as error:
        _record_failure(email, error, values.get("code"))
        return
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


def _record_failure(email: OutboundEmail, error: BaseException, code: str | None = None) -> None:
    email.attempts += 1
    detail = f"{type(error).__name__}: {error}"
    # Algunos errores citan el mensaje ya preparado: el código nunca se guarda en claro (D-18).
    email.last_error = detail.replace(code, "[code]") if code else detail
    if classify(error) is Failure.PERMANENT or _window_is_over(email):
        email.status = OutboundEmail.Status.FAILED
        _forget_code(email)
    else:
        email.next_attempt_at = timezone.now() + _wait(email.attempts)
    email.save(
        update_fields=[
            "attempts",
            "last_error",
            "status",
            "next_attempt_at",
            "masked_code",
            "code_nonce",
        ]
    )
    logger.info("Outbound email %s failed (attempt %s).", email.pk, email.attempts)


def _wait(attempts: int) -> timedelta:
    return min(FIRST_WAIT * (1 << (attempts - 1)), MAX_WAIT)


def _window_is_over(email: OutboundEmail) -> bool:
    if email.kind in rendering.CODE_KINDS:
        return False
    window = timedelta(hours=settings.EMAIL_NOTICE_RETRY_HOURS)
    return timezone.now() >= email.created_at + window


def _code_expiry(email: OutboundEmail, code: str) -> datetime | None:
    check = _CODE_CHECKS.get(email.purpose)
    if check is None:
        raise ImproperlyConfigured(
            _("No code check is registered for %(purpose)s.") % {"purpose": email.purpose}
        )
    return check(email.public_id, code)


def _forget_code(email: OutboundEmail) -> None:
    email.masked_code = None
    email.code_nonce = ""
