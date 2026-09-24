from typing import Any

from django.core.management.base import BaseCommand

from apps.core.tasks import record_ping


class Command(BaseCommand):
    help = "Encola la tarea de prueba record_ping en la cola de Celery."

    def handle(self, *args: Any, **options: Any) -> None:
        result = record_ping.delay("demo-command")
        self.stdout.write(f"Tarea encolada: {result.id}")
