import logging
from unittest import mock

import pytest

from apps.core.maintenance import (
    MAX_ERROR_SUMMARY_LENGTH,
    SimulatedMaintenanceFailure,
    run_maintenance_task,
)
from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus

pytestmark = pytest.mark.django_db


def test_run_records_and_overwrites_last_execution_status() -> None:
    first = run_maintenance_task(MaintenanceTaskName.PURGE_STALE_REGISTRATIONS, lambda: 4)
    second = run_maintenance_task(MaintenanceTaskName.PURGE_STALE_REGISTRATIONS, lambda: 2)

    assert (first, second) == (4, 2)
    assert MaintenanceTaskStatus.objects.count() == 1
    status = MaintenanceTaskStatus.objects.get(
        task_name=MaintenanceTaskName.PURGE_STALE_REGISTRATIONS
    )
    assert status.status == MaintenanceTaskStatus.Status.SUCCESS
    assert status.deleted_count == 2
    assert status.error_summary == ""
    assert status.finished_at >= status.started_at


def test_run_records_truncated_failure_creates_alert_and_reraises(
    caplog: pytest.LogCaptureFixture,
) -> None:
    long_message = "secret-boom " * 60

    def explode() -> int:
        raise ValueError(long_message)

    with caplog.at_level(logging.ERROR, logger="apps.core.maintenance"):
        with pytest.raises(ValueError):
            run_maintenance_task(MaintenanceTaskName.PURGE_EXPIRED_SESSIONS, explode)

    status = MaintenanceTaskStatus.objects.get(task_name=MaintenanceTaskName.PURGE_EXPIRED_SESSIONS)
    assert status.status == MaintenanceTaskStatus.Status.FAILURE
    assert status.deleted_count == 0
    assert len(status.error_summary) == MAX_ERROR_SUMMARY_LENGTH
    assert status.error_summary.startswith("ValueError: secret-boom")
    assert status.error_summary.endswith("...")
    assert "Traceback" not in status.error_summary

    alert = MaintenanceAlert.objects.get(task_name=MaintenanceTaskName.PURGE_EXPIRED_SESSIONS)
    assert alert.is_open is True
    assert alert.error_summary == status.error_summary
    assert any(
        "Maintenance task purge_expired_sessions failed." in rec.message for rec in caplog.records
    )


def test_simulate_failure_aborts_before_action_and_opens_alert() -> None:
    action = mock.Mock(return_value=99)

    with pytest.raises(SimulatedMaintenanceFailure):
        run_maintenance_task(
            MaintenanceTaskName.PURGE_SECURITY_EVENTS,
            action,
            simulate_failure=True,
        )

    action.assert_not_called()
    status = MaintenanceTaskStatus.objects.get(task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS)
    assert status.status == MaintenanceTaskStatus.Status.FAILURE
    assert MaintenanceAlert.objects.filter(
        task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS, resolved_at__isnull=True
    ).exists()


def test_subsequent_success_resolves_only_that_tasks_open_alerts() -> None:
    with pytest.raises(SimulatedMaintenanceFailure):
        run_maintenance_task(
            MaintenanceTaskName.PURGE_SECURITY_EVENTS, lambda: 0, simulate_failure=True
        )
    with pytest.raises(SimulatedMaintenanceFailure):
        run_maintenance_task(
            MaintenanceTaskName.PURGE_EXPIRED_SESSIONS, lambda: 0, simulate_failure=True
        )

    run_maintenance_task(MaintenanceTaskName.PURGE_SECURITY_EVENTS, lambda: 5)

    assert not MaintenanceAlert.objects.filter(
        task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS, resolved_at__isnull=True
    ).exists()
    resolved = MaintenanceAlert.objects.get(task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS)
    assert resolved.resolved_at is not None
    assert MaintenanceAlert.objects.filter(
        task_name=MaintenanceTaskName.PURGE_EXPIRED_SESSIONS, resolved_at__isnull=True
    ).exists()
