import logging
from collections.abc import Callable
from datetime import datetime

from django.utils import timezone

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


def run_maintenance_task(
    task_name: MaintenanceTaskName | str,
    action: Callable[[], int],
    *,
    simulate_failure: bool = False,
) -> int:
    name = MaintenanceTaskName(task_name)
    started_at = timezone.now()
    try:
        if simulate_failure:
            raise SimulatedMaintenanceFailure("Simulated maintenance task failure.")
        deleted_count = action()
    except Exception as exc:
        finished_at = timezone.now()
        summary = summarize_error(exc)
        logger.exception("Maintenance task %s failed.", name)
        _record_status(
            task_name=name,
            started_at=started_at,
            finished_at=finished_at,
            status=MaintenanceTaskStatus.Status.FAILURE,
            deleted_count=0,
            error_summary=summary,
        )
        MaintenanceAlert.objects.create(
            task_name=name,
            created_at=finished_at,
            error_summary=summary,
        )
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
