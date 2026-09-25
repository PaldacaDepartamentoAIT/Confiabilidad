from django_celery_beat.models import IntervalSchedule, PeriodicTask

DEMO_TASK_NAME = "demo-record-ping"


def register_demo_periodic_task() -> PeriodicTask:
    # Registro idempotente: no duplica al repetirse (RF-005).
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=60,
        period=IntervalSchedule.SECONDS,
    )
    task, _ = PeriodicTask.objects.update_or_create(
        name=DEMO_TASK_NAME,
        defaults={"interval": schedule, "task": "apps.core.tasks.record_ping"},
    )
    return task
