import logging
from typing import Any

from celery import current_app, shared_task
from django.utils import timezone

from apps.accounts import conf, registration
from apps.accounts.models import PhantomProcess

logger = logging.getLogger(__name__)

RESOLVE_TASKS = {
    PhantomProcess.Purpose.REGISTRATION: "apps.accounts.tasks.resolve_registration",
}
REISSUE_FUNCTIONS = {
    PhantomProcess.Purpose.REGISTRATION: registration.reissue_code,
}
_FIRST_WAIT_SECONDS = 15
_MAX_WAIT_SECONDS = 60


@shared_task(bind=True, name="apps.accounts.tasks.resolve_registration")  # type: ignore[untyped-decorator]
def resolve_registration(self: Any, public_id: str) -> None:
    try:
        registration.resolve_registration(public_id)
    except Exception as error:
        if _within_window(public_id):
            wait = min(_FIRST_WAIT_SECONDS * 2**self.request.retries, _MAX_WAIT_SECONDS)
            raise self.retry(exc=error, countdown=wait) from error
        _give_up(public_id, error)


@shared_task(name="apps.accounts.tasks.reissue_code")  # type: ignore[untyped-decorator]
def reissue_code(purpose: str, public_id: str) -> None:
    REISSUE_FUNCTIONS[PhantomProcess.Purpose(purpose)](public_id)


@shared_task(name="apps.accounts.tasks.sweep_unresolved")  # type: ignore[untyped-decorator]
def sweep_unresolved() -> int:
    # Recoge las plazas cuyo encolado se perdió (por ejemplo, con la cola caída) (D-15).
    unresolved = PhantomProcess.objects.filter(payload__isnull=False)
    limit = timezone.now() - conf.start_retry_window()
    queued = 0
    for slot in unresolved.filter(created_at__gt=limit):
        current_app.send_task(
            RESOLVE_TASKS[PhantomProcess.Purpose(slot.purpose)], args=[slot.public_id]
        )
        queued += 1
    for slot in unresolved.filter(created_at__lte=limit):
        _give_up(slot.public_id, None)
    return queued


def _within_window(public_id: str) -> bool:
    slot = PhantomProcess.objects.filter(public_id=public_id).first()
    return slot is not None and timezone.now() < slot.created_at + conf.start_retry_window()


def _give_up(public_id: str, error: BaseException | None) -> None:
    # La plaza queda como identificador sin registro detrás, igual que con cuenta (C-03).
    PhantomProcess.objects.filter(public_id=public_id).update(payload=None)
    logger.error("Background start of a process gave up: %r", error)
