import logging
from collections.abc import Callable
from typing import Any

from celery import current_app, shared_task
from django.utils import timezone

from apps.accounts import conf, password_reset, registration
from apps.accounts.models import PhantomProcess

logger = logging.getLogger(__name__)

RESOLVE_TASKS = {
    PhantomProcess.Purpose.REGISTRATION: "apps.accounts.tasks.resolve_registration",
    PhantomProcess.Purpose.PASSWORD_RESET: "apps.accounts.tasks.resolve_password_reset",
}
REISSUE_FUNCTIONS = {
    PhantomProcess.Purpose.REGISTRATION: registration.reissue_code,
    PhantomProcess.Purpose.PASSWORD_RESET: password_reset.reissue_code,
}
_FIRST_WAIT_SECONDS = 15
_MAX_WAIT_SECONDS = 60


# Sin tope de reintentos de Celery: el único límite es la ventana (D-15).
@shared_task(bind=True, max_retries=None, name="apps.accounts.tasks.resolve_registration")  # type: ignore[untyped-decorator]
def resolve_registration(self: Any, public_id: str) -> None:
    _resolve_or_retry(self, registration.resolve_registration, public_id)


@shared_task(bind=True, max_retries=None, name="apps.accounts.tasks.resolve_password_reset")  # type: ignore[untyped-decorator]
def resolve_password_reset(self: Any, public_id: str) -> None:
    _resolve_or_retry(self, password_reset.resolve_password_reset, public_id)


def _resolve_or_retry(task: Any, resolve: Callable[[str], None], public_id: str) -> None:
    # La ventana se mira antes de resolver: un reintento o una tarea atendida tarde no resuelve.
    if _unresolved_after_window(public_id):
        _give_up(public_id, None)
        return
    try:
        resolve(public_id)
    except Exception as error:
        if _within_window(public_id):
            wait = min(_FIRST_WAIT_SECONDS * 2**task.request.retries, _MAX_WAIT_SECONDS)
            raise task.retry(exc=error, countdown=wait) from error
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


def _unresolved_after_window(public_id: str) -> bool:
    slot = PhantomProcess.objects.filter(public_id=public_id, payload__isnull=False).first()
    return slot is not None and timezone.now() >= slot.created_at + conf.start_retry_window()


def _within_window(public_id: str) -> bool:
    slot = PhantomProcess.objects.filter(public_id=public_id).first()
    return slot is not None and timezone.now() < slot.created_at + conf.start_retry_window()


def _give_up(public_id: str, error: BaseException | None) -> None:
    # La plaza queda como identificador sin registro detrás, igual que con cuenta (C-03).
    PhantomProcess.objects.filter(public_id=public_id).update(payload=None)
    logger.error("Background start of a process gave up: %r", error)
