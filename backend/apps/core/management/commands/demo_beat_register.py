from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.beat import register_demo_periodic_task


class Command(BaseCommand):
    help = "Registra la tarea periódica de demostración (solo en desarrollo)."

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEBUG:
            raise CommandError("Solo disponible en desarrollo (DEBUG=True).")
        task = register_demo_periodic_task()
        self.stdout.write(f"Tarea periódica registrada: {task.name}")
