from collections.abc import Callable
from datetime import timedelta
from unittest import mock

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts import tasks as account_tasks
from apps.accounts.models import PendingRegistration, UserSession
from apps.accounts.tests.factories import make_pending, make_user
from apps.audit import tasks as audit_tasks
from apps.audit.models import EventType, SecurityEvent
from apps.core.maintenance import SimulatedMaintenanceFailure
from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus

pytestmark = pytest.mark.django_db


def _seed_stale_registration() -> Callable[[], bool]:
    started = make_pending("stale@ejemplo.com")
    PendingRegistration.objects.filter(public_id=started.public_id).update(
        code_expires_at=timezone.now() - timedelta(hours=25)
    )
    return lambda: PendingRegistration.objects.filter(public_id=started.public_id).exists()


def _seed_expired_session() -> Callable[[], bool]:
    user = make_user(email="session@ejemplo.com")
    row = UserSession.objects.create(
        user=user,
        session_key="a" * 64,
        ip="192.0.2.40",
        last_seen_at=timezone.now() - timedelta(days=15),
    )
    return lambda: UserSession.objects.filter(pk=row.pk).exists()


def _seed_old_audit_event() -> Callable[[], bool]:
    row = SecurityEvent.objects.create(
        event_type=EventType.LOGIN,
        success=True,
        created_at=timezone.now() - timedelta(days=400),
    )
    return lambda: SecurityEvent.objects.filter(pk=row.pk).exists()


CASES = [
    (
        MaintenanceTaskName.PURGE_STALE_REGISTRATIONS,
        account_tasks.purge_stale_registrations,
        _seed_stale_registration,
    ),
    (
        MaintenanceTaskName.PURGE_EXPIRED_SESSIONS,
        account_tasks.purge_expired_sessions,
        _seed_expired_session,
    ),
    (
        MaintenanceTaskName.PURGE_SECURITY_EVENTS,
        audit_tasks.purge_security_events,
        _seed_old_audit_event,
    ),
]


@pytest.mark.parametrize(("task_name", "task_fn", "seed"), CASES)
def test_task_simulates_failure_without_deleting_then_recovers_on_next_run(
    settings: object,
    task_name: MaintenanceTaskName,
    task_fn: Callable[..., int],
    seed: Callable[[], Callable[[], bool]],
) -> None:
    settings.MAINTENANCE_ALERT_EMAILS = ["ops@ejemplo.com"]  # type: ignore[attr-defined]
    still_exists = seed()

    with pytest.raises(SimulatedMaintenanceFailure):
        task_fn(simulate_failure=True)

    assert still_exists() is True
    assert (
        MaintenanceTaskStatus.objects.get(task_name=task_name).status
        == MaintenanceTaskStatus.Status.FAILURE
    )
    assert (
        MaintenanceAlert.objects.filter(task_name=task_name, resolved_at__isnull=True).count() == 1
    )
    assert len(mail.outbox) == 1

    assert task_fn() == 1
    assert still_exists() is False
    status = MaintenanceTaskStatus.objects.get(task_name=task_name)
    assert status.status == MaintenanceTaskStatus.Status.SUCCESS
    assert status.deleted_count == 1
    assert not MaintenanceAlert.objects.filter(
        task_name=task_name, resolved_at__isnull=True
    ).exists()


def test_audit_purge_task_fails_and_alerts_when_command_produces_empty_output() -> None:
    with (
        mock.patch("apps.audit.tasks.call_command"),
        pytest.raises(RuntimeError, match="did not produce an output count"),
    ):
        audit_tasks.purge_security_events()

    status = MaintenanceTaskStatus.objects.get(task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS)
    assert status.status == MaintenanceTaskStatus.Status.FAILURE
    assert MaintenanceAlert.objects.filter(
        task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS, resolved_at__isnull=True
    ).exists()
