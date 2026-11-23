import json
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from django.conf import settings
from django.utils import timezone
from django_celery_beat.models import PeriodicTask
from django_celery_beat.schedulers import DatabaseScheduler

from apps.audit import tasks
from apps.audit.models import EventType, SecurityEvent
from config.celery import app as celery_app

BACKEND_DIR = Path(__file__).resolve().parents[3]
_READ_SETTINGS = (
    "import django, json\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    "print(json.dumps({"
    "'registrations': settings.CELERY_BEAT_SCHEDULE["
    "'accounts-purge-stale-registrations']['schedule'],"
    "'sessions': settings.CELERY_BEAT_SCHEDULE['accounts-purge-expired-sessions']['schedule'],"
    "'audit': settings.CELERY_BEAT_SCHEDULE['audit-purge-security-events']['schedule'],"
    "'emails': settings.MAINTENANCE_ALERT_EMAILS,"
    "'lock_timeout': settings.MAINTENANCE_LOCK_TIMEOUT_SECONDS,"
    "}))\n"
)


@pytest.mark.django_db
def test_purge_security_events_task_deletes_only_events_older_than_one_year() -> None:
    old_event = SecurityEvent.objects.create(
        event_type=EventType.LOGIN,
        success=True,
        created_at=timezone.now() - timedelta(days=400),
    )
    recent_event = SecurityEvent.objects.create(
        event_type=EventType.LOGIN,
        success=True,
        created_at=timezone.now() - timedelta(days=10),
    )

    deleted = tasks.purge_security_events()

    assert deleted == 1
    assert not SecurityEvent.objects.filter(pk=old_event.pk).exists()
    assert SecurityEvent.objects.filter(pk=recent_event.pk).exists()


def test_maintenance_tasks_have_expected_default_beat_schedule() -> None:
    schedule = settings.CELERY_BEAT_SCHEDULE

    assert schedule["accounts-purge-stale-registrations"]["schedule"] == 3600.0
    assert (
        schedule["accounts-purge-stale-registrations"]["task"]
        == "apps.accounts.tasks.purge_stale_registrations"
    )
    assert schedule["accounts-purge-expired-sessions"]["schedule"] == 3600.0
    assert (
        schedule["accounts-purge-expired-sessions"]["task"]
        == "apps.accounts.tasks.purge_expired_sessions"
    )
    assert schedule["audit-purge-security-events"]["schedule"] == 86400.0
    assert (
        schedule["audit-purge-security-events"]["task"] == "apps.audit.tasks.purge_security_events"
    )


@pytest.mark.django_db
def test_database_scheduler_registers_all_three_maintenance_tasks() -> None:
    scheduler = DatabaseScheduler(app=celery_app)
    try:
        expected = {
            "accounts-purge-stale-registrations": (
                "apps.accounts.tasks.purge_stale_registrations",
                3600,
            ),
            "accounts-purge-expired-sessions": (
                "apps.accounts.tasks.purge_expired_sessions",
                3600,
            ),
            "audit-purge-security-events": (
                "apps.audit.tasks.purge_security_events",
                86400,
            ),
        }
        for name, (task_path, every_seconds) in expected.items():
            periodic = PeriodicTask.objects.get(name=name)
            assert periodic.enabled is True
            assert periodic.task == task_path
            assert periodic.interval is not None
            assert periodic.interval.every == every_seconds
    finally:
        scheduler.close()


def test_maintenance_intervals_and_alerts_are_configurable_via_environment() -> None:
    env = dict(os.environ)
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_DEBUG": "1",
            "PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS": "5",
            "PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS": "10",
            "PURGE_SECURITY_EVENTS_INTERVAL_SECONDS": "15",
            "MAINTENANCE_ALERT_EMAILS": "ops@ejemplo.com,sec@ejemplo.com",
            "MAINTENANCE_LOCK_TIMEOUT_SECONDS": "120",
        }
    )
    result = subprocess.run(
        [sys.executable, "-c", _READ_SETTINGS],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    data = json.loads(result.stdout.splitlines()[-1])

    assert data == {
        "registrations": 5.0,
        "sessions": 10.0,
        "audit": 15.0,
        "emails": ["ops@ejemplo.com", "sec@ejemplo.com"],
        "lock_timeout": 120,
    }
