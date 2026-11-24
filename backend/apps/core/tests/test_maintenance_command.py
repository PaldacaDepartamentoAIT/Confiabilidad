from io import StringIO
from pathlib import Path
from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.core.maintenance import SimulatedMaintenanceFailure
from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus

pytestmark = pytest.mark.django_db
BACKEND_DIR = Path(__file__).resolve().parents[3]


def test_status_reports_unexecuted_tasks_then_statuses_and_alerts() -> None:
    empty_out = StringIO()
    call_command("maintenance_tasks", "status", stdout=empty_out)
    text = empty_out.getvalue()
    for name in MaintenanceTaskName:
        assert f"{name}: no executions recorded" in text
    assert "alerts: none" in text

    now = timezone.now()
    MaintenanceTaskStatus.objects.create(
        task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS,
        started_at=now,
        finished_at=now,
        status=MaintenanceTaskStatus.Status.FAILURE,
        error_summary="RuntimeError: bad",
    )
    MaintenanceAlert.objects.create(
        task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS,
        error_summary="RuntimeError: bad",
    )
    MaintenanceAlert.objects.create(
        task_name=MaintenanceTaskName.PURGE_EXPIRED_SESSIONS,
        error_summary="old error",
        resolved_at=now,
    )

    open_out = StringIO()
    call_command("maintenance_tasks", "status", "--open-only", stdout=open_out)
    open_text = open_out.getvalue()
    assert "status=failure" in open_text
    assert "RuntimeError: bad" in open_text
    assert "old error" not in open_text


def test_run_requires_target_and_executes_sync_or_async() -> None:
    with pytest.raises(CommandError):
        call_command("maintenance_tasks", "run")

    sync_out = StringIO()
    call_command("maintenance_tasks", "run", "--all", stdout=sync_out)
    assert "completed purge_stale_registrations: deleted=0" in sync_out.getvalue()
    assert "completed purge_security_events: deleted=0" in sync_out.getvalue()

    async_out = StringIO()
    with mock.patch("apps.core.management.commands.maintenance_tasks.current_app") as app:
        app.send_task.return_value = mock.Mock(id="task-123")
        call_command(
            "maintenance_tasks", "run", "purge_expired_sessions", "--async", stdout=async_out
        )
    app.send_task.assert_called_once_with("apps.accounts.tasks.purge_expired_sessions")
    assert "queued purge_expired_sessions: task-123" in async_out.getvalue()


def test_simulate_failure_queues_task_and_can_wait_for_failure() -> None:
    out = StringIO()
    async_result = mock.Mock(id="sim-1")
    async_result.get.side_effect = SimulatedMaintenanceFailure("boom")
    with mock.patch("apps.core.management.commands.maintenance_tasks.current_app") as app:
        app.send_task.return_value = async_result
        call_command(
            "maintenance_tasks", "simulate-failure", "purge_security_events", "--wait=5", stdout=out
        )

    app.send_task.assert_called_once_with(
        "apps.audit.tasks.purge_security_events",
        kwargs={"simulate_failure": True},
    )
    assert "simulated failure observed for purge_security_events (sim-1)" in out.getvalue()


def test_env_example_documents_all_maintenance_variables() -> None:
    example = (BACKEND_DIR / ".env.example").read_text()
    for var in (
        "PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS",
        "PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS",
        "PURGE_SECURITY_EVENTS_INTERVAL_SECONDS",
        "MAINTENANCE_ALERT_EMAILS",
        "MAINTENANCE_LOCK_TIMEOUT_SECONDS",
    ):
        assert f"# {var}=" in example
