import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django_celery_beat.models import PeriodicTask

from apps.core.beat import DEMO_TASK_NAME, register_demo_periodic_task


@pytest.mark.django_db
def test_register_is_idempotent() -> None:
    first = register_demo_periodic_task()
    second = register_demo_periodic_task()

    assert first.pk == second.pk
    assert PeriodicTask.objects.filter(name=DEMO_TASK_NAME).count() == 1
    assert first.task == "apps.core.tasks.record_ping"


@pytest.mark.django_db
def test_command_registers_in_development() -> None:
    with override_settings(DEBUG=True):
        call_command("demo_beat_register")

    assert PeriodicTask.objects.filter(name=DEMO_TASK_NAME).exists()


@pytest.mark.django_db
def test_command_refuses_outside_development() -> None:
    with override_settings(DEBUG=False), pytest.raises(CommandError):
        call_command("demo_beat_register")
