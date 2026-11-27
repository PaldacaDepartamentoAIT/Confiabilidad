from collections.abc import Callable, Iterator
from datetime import timedelta
from io import StringIO
from typing import Any

import pytest
from celery import current_app
from celery.contrib.testing.worker import start_worker
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import PendingRegistration, User, UserSession
from apps.accounts.tests.factories import make_pending, make_user
from apps.audit.models import EventType, SecurityEvent
from apps.core.management.commands.maintenance_tasks import TASK_PATHS
from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus
from config.celery import app as celery_app


def _set_queue(queue: str, routing_key: str) -> None:
    celery_app.conf.update(task_default_queue=queue, task_default_routing_key=routing_key)
    celery_app.amqp.__dict__.pop("queues", None)
    celery_app.amqp.__dict__.pop("router", None)


@pytest.fixture
def isolated_worker() -> Iterator[None]:
    prev = (celery_app.conf.task_default_queue, celery_app.conf.task_default_routing_key)
    _set_queue("test-maintenance", "test-maintenance")
    try:
        with start_worker(celery_app, perform_ping_check=False, shutdown_timeout=20):
            yield
    finally:
        _set_queue(*prev)


def _seed(name: MaintenanceTaskName) -> Callable[[], bool]:
    if name == MaintenanceTaskName.PURGE_STALE_REGISTRATIONS:
        qs = PendingRegistration.objects.filter(public_id=make_pending("e2e@ejemplo.com").public_id)
        qs.update(code_expires_at=timezone.now() - timedelta(hours=25))
        return qs.exists
    if name == MaintenanceTaskName.PURGE_EXPIRED_SESSIONS:
        row = UserSession.objects.create(
            user=make_user(email="e2e-s@ejemplo.com"),
            session_key="b" * 64,
            ip="192.0.2.41",
            last_seen_at=timezone.now() - timedelta(days=15),
        )
        return UserSession.objects.filter(pk=row.pk).exists
    if name == MaintenanceTaskName.PURGE_DISABLED_ACCOUNTS:
        user = make_user(
            email="e2e-disabled@ejemplo.com",
            is_active=False,
            disabled_at=timezone.now() - timedelta(days=400),
        )
        return User.objects.filter(pk=user.pk).exists
    event = SecurityEvent.objects.create(
        event_type=EventType.LOGIN, success=True, created_at=timezone.now() - timedelta(days=400)
    )
    return SecurityEvent.objects.filter(pk=event.pk).exists


def _state(name: MaintenanceTaskName) -> tuple[str, int]:
    return (
        MaintenanceTaskStatus.objects.get(task_name=name).status,
        MaintenanceAlert.objects.filter(task_name=name, resolved_at__isnull=True).count(),
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("name", list(MaintenanceTaskName))
def test_real_worker_simulates_failure_and_recovers(
    isolated_worker: None, settings: Any, name: MaintenanceTaskName
) -> None:
    settings.MAINTENANCE_ALERT_EMAILS = ["ops@ejemplo.com"]
    still_exists = _seed(name)
    out = StringIO()
    call_command("maintenance_tasks", "simulate-failure", name.value, "--wait", "15", stdout=out)
    assert f"simulated failure observed for {name.value}" in out.getvalue()
    assert still_exists() is True
    assert _state(name) == (MaintenanceTaskStatus.Status.FAILURE, 1)
    assert len(mail.outbox) == 1
    assert current_app.send_task(TASK_PATHS[name]).get(timeout=15) == 1
    assert still_exists() is False
    assert _state(name) == (MaintenanceTaskStatus.Status.SUCCESS, 0)
