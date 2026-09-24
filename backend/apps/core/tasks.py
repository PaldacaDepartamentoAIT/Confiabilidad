from celery import shared_task

from apps.core.models import DemoRecord


@shared_task  # type: ignore[untyped-decorator]
def record_ping(label: str = "ping") -> int:
    record = DemoRecord.objects.create(label=label, source="task")
    return record.pk
