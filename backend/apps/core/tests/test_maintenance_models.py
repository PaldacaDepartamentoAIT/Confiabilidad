from io import StringIO

import pytest
from django.core.management import call_command
from django.db import IntegrityError
from django.utils import timezone

from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus

pytestmark = pytest.mark.django_db


def test_maintenance_task_status_starts_empty_and_enforces_unique_task_name() -> None:
    assert MaintenanceTaskStatus.objects.count() == 0

    now = timezone.now()
    status = MaintenanceTaskStatus.objects.create(
        task_name=MaintenanceTaskName.PURGE_STALE_REGISTRATIONS,
        started_at=now,
        finished_at=now,
        status=MaintenanceTaskStatus.Status.SUCCESS,
        deleted_count=3,
    )
    assert str(status) == "purge_stale_registrations: success"

    with pytest.raises(IntegrityError):
        MaintenanceTaskStatus.objects.create(
            task_name=MaintenanceTaskName.PURGE_STALE_REGISTRATIONS,
            started_at=now,
            finished_at=now,
            status=MaintenanceTaskStatus.Status.FAILURE,
        )


def test_maintenance_alert_distinguishes_open_and_resolved() -> None:
    open_alert = MaintenanceAlert.objects.create(
        task_name=MaintenanceTaskName.PURGE_EXPIRED_SESSIONS,
        error_summary="RuntimeError: boom",
    )
    resolved_alert = MaintenanceAlert.objects.create(
        task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS,
        error_summary="OSError: disk",
        resolved_at=timezone.now(),
    )

    assert open_alert.is_open is True
    assert str(open_alert) == "purge_expired_sessions (open)"
    assert resolved_alert.is_open is False
    assert str(resolved_alert) == "purge_security_events (resolved)"


def test_core_migrations_have_no_pending_changes() -> None:
    call_command("makemigrations", "core", check=True, dry_run=True, stdout=StringIO())
