from io import StringIO

from celery import shared_task
from django.core.management import call_command


@shared_task(name="apps.audit.tasks.purge_security_events")  # type: ignore[untyped-decorator]
def purge_security_events() -> int:
    stdout = StringIO()
    call_command("purge_security_events", stdout=stdout)
    output = stdout.getvalue().strip()
    if not output:
        raise RuntimeError("purge_security_events did not produce an output count.")
    return int(output.split()[0])
