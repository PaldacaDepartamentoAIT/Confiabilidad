import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime

import redis
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from redis.exceptions import LockError

from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus

logger = logging.getLogger(__name__)
MAX_ERROR_SUMMARY_LENGTH = 500


class SimulatedMaintenanceFailure(RuntimeError):
    """Controlled failure raised before touching domain data when testing alerts."""


def summarize_error(exc: BaseException, max_length: int = MAX_ERROR_SUMMARY_LENGTH) -> str:
    detail = " ".join(f"{type(exc).__name__}: {exc}".split())
    if len(detail) <= max_length:
        return detail
    return f"{detail[: max_length - 3]}..."


@contextmanager
def _task_lock(task_name: MaintenanceTaskName) -> Iterator[None]:
    client = redis.Redis.from_url(settings.CACHE_URL)
    lock = client.lock(
        f"maintenance-task:{task_name.value}",
        timeout=settings.MAINTENANCE_LOCK_TIMEOUT_SECONDS,
        blocking=True,
    )
    lock.acquire()
    try:
        yield
    finally:
        try:
            lock.release()
        except LockError:
            logger.warning("Maintenance lock expired before release for %s.", task_name)
        client.close()


def _record_status(
    *,
    task_name: MaintenanceTaskName,
    started_at: datetime,
    finished_at: datetime,
    status: MaintenanceTaskStatus.Status,
    deleted_count: int,
    error_summary: str = "",
) -> None:
    MaintenanceTaskStatus.objects.update_or_create(
        task_name=task_name,
        defaults={
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "deleted_count": deleted_count,
            "error_summary": error_summary,
        },
    )


def _send_alert_email(task_name: MaintenanceTaskName, occurred_at: datetime, summary: str) -> None:
    recipients = [addr.strip() for addr in settings.MAINTENANCE_ALERT_EMAILS if addr.strip()]
    if not recipients:
        return
    subject = f"[Maintenance Alert] {task_name.value} failed"
    body = f"Task: {task_name.value}\n" f"Time: {occurred_at.isoformat()}\n" f"Error: {summary}\n"
    try:
        EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, recipients).send()
    except Exception:
        logger.exception("Failed to send maintenance alert email for %s.", task_name)


def _record_failure(
    task_name: MaintenanceTaskName,
    started_at: datetime,
    exc: BaseException,
) -> None:
    finished_at = timezone.now()
    summary = summarize_error(exc)
    logger.exception("Maintenance task %s failed.", task_name)
    try:
        had_open_alert = MaintenanceAlert.objects.filter(
            task_name=task_name, resolved_at__isnull=True
        ).exists()
        _record_status(
            task_name=task_name,
            started_at=started_at,
            finished_at=finished_at,
            status=MaintenanceTaskStatus.Status.FAILURE,
            deleted_count=0,
            error_summary=summary,
        )
        MaintenanceAlert.objects.create(
            task_name=task_name,
            created_at=finished_at,
            error_summary=summary,
        )
    except Exception:
        logger.exception("Failed to persist maintenance failure state for %s.", task_name)
        return
    if not had_open_alert:
        _send_alert_email(task_name, finished_at, summary)


def run_maintenance_task(
    task_name: MaintenanceTaskName | str,
    action: Callable[[], int],
    *,
    simulate_failure: bool = False,
) -> int:
    name = MaintenanceTaskName(task_name)
    with _task_lock(name):
        started_at = timezone.now()
        try:
            if simulate_failure:
                raise SimulatedMaintenanceFailure("Simulated maintenance task failure.")
            deleted_count = action()
        except Exception as exc:
            _record_failure(name, started_at, exc)
            raise

        finished_at = timezone.now()
        _record_status(
            task_name=name,
            started_at=started_at,
            finished_at=finished_at,
            status=MaintenanceTaskStatus.Status.SUCCESS,
            deleted_count=deleted_count,
        )
        MaintenanceAlert.objects.filter(task_name=name, resolved_at__isnull=True).update(
            resolved_at=finished_at
        )
        return deleted_count
