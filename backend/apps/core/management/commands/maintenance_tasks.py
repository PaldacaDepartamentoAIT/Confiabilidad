from typing import Any

from celery import current_app
from django.core.management.base import BaseCommand, CommandError
from django.utils.module_loading import import_string

from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus

TASK_PATHS: dict[str, str] = {
    MaintenanceTaskName.PURGE_STALE_REGISTRATIONS: "apps.accounts.tasks.purge_stale_registrations",
    MaintenanceTaskName.PURGE_EXPIRED_SESSIONS: "apps.accounts.tasks.purge_expired_sessions",
    MaintenanceTaskName.PURGE_SECURITY_EVENTS: "apps.audit.tasks.purge_security_events",
}


class Command(BaseCommand):
    help = "Inspect, run, and simulate failures for periodic maintenance tasks."

    def add_arguments(self, parser: Any) -> None:
        subparsers = parser.add_subparsers(dest="action", required=True)
        status_parser = subparsers.add_parser("status", help="Show last executions and alerts.")
        status_parser.add_argument("--open-only", action="store_true")

        run_parser = subparsers.add_parser("run", help="Run one or all maintenance tasks.")
        run_parser.add_argument("task", nargs="?", choices=list(TASK_PATHS))
        run_parser.add_argument("--all", action="store_true", dest="run_all")
        run_parser.add_argument("--async", action="store_true", dest="run_async")

        sim_parser = subparsers.add_parser("simulate-failure", help="Simulate task failure.")
        sim_parser.add_argument("task", choices=list(TASK_PATHS))
        sim_parser.add_argument("--wait", type=float, default=0.0)

    def handle(self, *args: Any, **options: Any) -> None:
        action = options["action"]
        if action == "status":
            self._status(open_only=bool(options["open_only"]))
        elif action == "run":
            self._run(
                task=options["task"],
                run_all=bool(options["run_all"]),
                run_async=bool(options["run_async"]),
            )
        else:
            self._simulate_failure(task=options["task"], wait=float(options["wait"]))

    def _status(self, *, open_only: bool) -> None:
        statuses = {row.task_name: row for row in MaintenanceTaskStatus.objects.all()}
        for name in TASK_PATHS:
            row = statuses.get(name)
            if row is None:
                self.stdout.write(f"{name}: no executions recorded")
            else:
                self.stdout.write(
                    f"{name}: status={row.status} deleted={row.deleted_count} "
                    f"finished_at={row.finished_at.isoformat()} error={row.error_summary or '-'}"
                )
        alerts = MaintenanceAlert.objects.all()
        if open_only:
            alerts = alerts.filter(resolved_at__isnull=True)
        alert_list = list(alerts)
        if not alert_list:
            self.stdout.write("alerts: none")
            return
        for alert in alert_list:
            state = "open" if alert.is_open else "resolved"
            resolved = alert.resolved_at.isoformat() if alert.resolved_at else "-"
            self.stdout.write(
                f"alert[{alert.pk}] {alert.task_name} state={state} "
                f"created={alert.created_at.isoformat()} resolved={resolved} "
                f"error={alert.error_summary}"
            )

    def _run(self, *, task: str | None, run_all: bool, run_async: bool) -> None:
        if not task and not run_all:
            raise CommandError("Specify a task name or --all.")
        targets = list(TASK_PATHS) if run_all else [str(task)]
        for name in targets:
            path = TASK_PATHS[name]
            if run_async:
                result = current_app.send_task(path)
                self.stdout.write(f"queued {name}: {result.id}")
            else:
                fn = import_string(path)
                deleted = fn()
                self.stdout.write(f"completed {name}: deleted={deleted}")

    def _simulate_failure(self, *, task: str, wait: float) -> None:
        result = current_app.send_task(TASK_PATHS[task], kwargs={"simulate_failure": True})
        if wait > 0:
            try:
                result.get(timeout=wait)
            except Exception as exc:
                self.stdout.write(
                    f"simulated failure observed for {task} ({result.id}): "
                    f"{type(exc).__name__}: {exc}"
                )
                return
        self.stdout.write(f"queued simulated failure {task}: {result.id}")
