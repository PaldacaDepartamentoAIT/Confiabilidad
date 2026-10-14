import logging
from collections.abc import Mapping
from datetime import timedelta
from typing import TYPE_CHECKING

from celery import current_app
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import fingerprints
from apps.emails import locales, rendering
from apps.emails.models import AccountExistsNotice, OutboundEmail

if TYPE_CHECKING:
    from apps.accounts.models import User

logger = logging.getLogger(__name__)

DELIVER_TASK = "apps.emails.tasks.deliver"
ACCOUNT_EXISTS = "account_exists"


def enqueue(
    *,
    kind: str,
    recipient: str,
    locale: str,
    context: Mapping[str, str] | None = None,
    account: "User | None" = None,
    purpose: str = "",
    public_id: str = "",
    code: str | None = None,
) -> OutboundEmail | None:
    if kind == ACCOUNT_EXISTS and not _account_exists_allowed(account):
        return None
    # El código solo se guarda oculto con la máscara de su clave propia (RF-018).
    masked_code, code_nonce = fingerprints.mask_code(code) if code is not None else (None, "")
    email = OutboundEmail.objects.create(
        kind=kind,
        recipient=recipient,
        locale=_language(kind, locale, account),
        context=dict(context or {}),
        purpose=purpose,
        public_id=public_id,
        masked_code=masked_code,
        code_nonce=code_nonce,
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


def _account_exists_allowed(account: "User | None") -> bool:
    if account is None:
        raise ValueError(_("An account exists notice needs the account."))
    now = timezone.now()
    window = timedelta(minutes=settings.EMAIL_ACCOUNT_EXISTS_WINDOW_MINUTES)
    with transaction.atomic():
        notice, created = AccountExistsNotice.objects.select_for_update().get_or_create(
            user=account, defaults={"last_queued_at": now}
        )
        if created:
            return True
        if now < notice.last_queued_at + window:
            return False
        notice.last_queued_at = now
        notice.save(update_fields=["last_queued_at"])
        return True
