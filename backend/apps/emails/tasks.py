from celery import shared_task

from apps.emails import delivery


@shared_task(name="apps.emails.tasks.deliver")  # type: ignore[untyped-decorator]
def deliver(email_id: int) -> None:
    delivery.deliver(email_id)


@shared_task(name="apps.emails.tasks.dispatch_due")  # type: ignore[untyped-decorator]
def dispatch_due() -> int:
    return delivery.dispatch_due()
