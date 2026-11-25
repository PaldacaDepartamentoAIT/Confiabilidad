import logging
import threading
from unittest import mock

import pytest
from django.core import mail
from django.db import OperationalError, connections

from apps.core.maintenance import SimulatedMaintenanceFailure, run_maintenance_task
from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus


@pytest.mark.django_db(transaction=True)
def test_same_task_is_serialized_across_concurrent_invocations() -> None:
    first_entered = threading.Event()
    release_first = threading.Event()
    events: list[str] = []

    def first_action() -> int:
        events.append("first_start")
        first_entered.set()
        assert release_first.wait(timeout=5)
        events.append("first_end")
        return 1

    def second_action() -> int:
        events.append("second_start")
        events.append("second_end")
        return 7

    def run_first() -> None:
        try:
            run_maintenance_task(MaintenanceTaskName.PURGE_STALE_REGISTRATIONS, first_action)
        finally:
            connections.close_all()

    def run_second() -> None:
        try:
            run_maintenance_task(MaintenanceTaskName.PURGE_STALE_REGISTRATIONS, second_action)
        finally:
            connections.close_all()

    t1 = threading.Thread(target=run_first)
    t2 = threading.Thread(target=run_second)
    t1.start()
    assert first_entered.wait(timeout=5)
    t2.start()
    # Breve espera para confirmar que la segunda ejecución espera a la primera.
    threading.Event().wait(0.15)
    assert events == ["first_start"]
    release_first.set()
    t1.join(timeout=5)
    t2.join(timeout=5)

    assert events == ["first_start", "first_end", "second_start", "second_end"]
    status = MaintenanceTaskStatus.objects.get(
        task_name=MaintenanceTaskName.PURGE_STALE_REGISTRATIONS
    )
    assert status.deleted_count == 7


@pytest.mark.django_db(transaction=True)
def test_different_tasks_do_not_block_each_other() -> None:
    first_entered = threading.Event()
    release_first = threading.Event()
    other_finished = threading.Event()

    def slow_action() -> int:
        first_entered.set()
        assert release_first.wait(timeout=5)
        return 1

    def fast_action() -> int:
        other_finished.set()
        return 2

    def run_slow() -> None:
        try:
            run_maintenance_task(MaintenanceTaskName.PURGE_STALE_REGISTRATIONS, slow_action)
        finally:
            connections.close_all()

    def run_fast() -> None:
        try:
            run_maintenance_task(MaintenanceTaskName.PURGE_EXPIRED_SESSIONS, fast_action)
        finally:
            connections.close_all()

    t1 = threading.Thread(target=run_slow)
    t2 = threading.Thread(target=run_fast)
    t1.start()
    assert first_entered.wait(timeout=5)
    t2.start()
    assert other_finished.wait(timeout=3)
    release_first.set()
    t1.join(timeout=5)
    t2.join(timeout=5)


@pytest.mark.django_db
def test_consecutive_failures_suppress_duplicate_emails_until_resolved(
    settings: object,
) -> None:
    settings.MAINTENANCE_ALERT_EMAILS = ["ops@ejemplo.com", "sec@ejemplo.com"]  # type: ignore[attr-defined]

    with pytest.raises(SimulatedMaintenanceFailure):
        run_maintenance_task(
            MaintenanceTaskName.PURGE_SECURITY_EVENTS, lambda: 0, simulate_failure=True
        )
    with pytest.raises(SimulatedMaintenanceFailure):
        run_maintenance_task(
            MaintenanceTaskName.PURGE_SECURITY_EVENTS, lambda: 0, simulate_failure=True
        )

    assert (
        MaintenanceAlert.objects.filter(
            task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS, resolved_at__isnull=True
        ).count()
        == 2
    )
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["ops@ejemplo.com", "sec@ejemplo.com"]
    assert "purge_security_events" in mail.outbox[0].subject
    assert "SimulatedMaintenanceFailure" in mail.outbox[0].body
    assert "Traceback" not in mail.outbox[0].body

    run_maintenance_task(MaintenanceTaskName.PURGE_SECURITY_EVENTS, lambda: 3)
    with pytest.raises(SimulatedMaintenanceFailure):
        run_maintenance_task(
            MaintenanceTaskName.PURGE_SECURITY_EVENTS, lambda: 0, simulate_failure=True
        )

    assert len(mail.outbox) == 2


@pytest.mark.django_db
def test_empty_recipients_skips_email_without_error(settings: object) -> None:
    settings.MAINTENANCE_ALERT_EMAILS = []  # type: ignore[attr-defined]

    with pytest.raises(SimulatedMaintenanceFailure):
        run_maintenance_task(
            MaintenanceTaskName.PURGE_EXPIRED_SESSIONS, lambda: 0, simulate_failure=True
        )

    assert len(mail.outbox) == 0
    assert MaintenanceAlert.objects.filter(
        task_name=MaintenanceTaskName.PURGE_EXPIRED_SESSIONS, resolved_at__isnull=True
    ).exists()


@pytest.mark.django_db
def test_email_delivery_error_preserves_status_and_alert(
    settings: object, caplog: pytest.LogCaptureFixture
) -> None:
    settings.MAINTENANCE_ALERT_EMAILS = ["ops@ejemplo.com"]  # type: ignore[attr-defined]

    with (
        mock.patch("apps.core.maintenance.EmailMessage.send", side_effect=OSError("smtp down")),
        caplog.at_level(logging.ERROR, logger="apps.core.maintenance"),
        pytest.raises(SimulatedMaintenanceFailure),
    ):
        run_maintenance_task(
            MaintenanceTaskName.PURGE_STALE_REGISTRATIONS, lambda: 0, simulate_failure=True
        )

    assert (
        MaintenanceTaskStatus.objects.get(
            task_name=MaintenanceTaskName.PURGE_STALE_REGISTRATIONS
        ).status
        == MaintenanceTaskStatus.Status.FAILURE
    )
    assert MaintenanceAlert.objects.filter(
        task_name=MaintenanceTaskName.PURGE_STALE_REGISTRATIONS, resolved_at__isnull=True
    ).exists()
    assert any("Failed to send maintenance alert email" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_database_error_during_failure_recording_logs_only_and_skips_email(
    settings: object, caplog: pytest.LogCaptureFixture
) -> None:
    settings.MAINTENANCE_ALERT_EMAILS = ["ops@ejemplo.com"]  # type: ignore[attr-defined]

    with (
        mock.patch(
            "apps.core.maintenance.MaintenanceAlert.objects.filter",
            side_effect=OperationalError("db down"),
        ),
        caplog.at_level(logging.ERROR, logger="apps.core.maintenance"),
        pytest.raises(RuntimeError, match="task error"),
    ):
        run_maintenance_task(
            MaintenanceTaskName.PURGE_EXPIRED_SESSIONS,
            lambda: (_ for _ in ()).throw(RuntimeError("task error")),
        )

    assert len(mail.outbox) == 0
    messages = [record.message for record in caplog.records]
    assert any("Maintenance task purge_expired_sessions failed." in msg for msg in messages)
    assert any("Failed to persist maintenance failure state" in msg for msg in messages)
