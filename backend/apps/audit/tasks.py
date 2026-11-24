from io import StringIO

from celery import shared_task
from django.core.management import call_command

from apps.core.maintenance import run_maintenance_task
from apps.core.models import MaintenanceTaskName


def _run_audit_purge() -> int:
    stdout = StringIO()
    call_command("purge_security_events", stdout=stdout)
    output = stdout.getvalue().strip()
    if not output:
        raise RuntimeError("purge_security_events did not produce an output count.")
    return int(output.split()[0])


@shared_task(name="apps.audit.tasks.purge_security_events")  # type: ignore[untyped-decorator]
def purge_security_events(simulate_failure: bool = False) -> int:
    return run_maintenance_task(
        MaintenanceTaskName.PURGE_SECURITY_EVENTS,
        _run_audit_purge,
        simulate_failure=simulate_failure,
    )
