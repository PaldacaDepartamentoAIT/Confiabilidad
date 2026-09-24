from typing import Any

from django.core.management.base import BaseCommand

from apps.core.models import DemoRecord


class Command(BaseCommand):
    help = "Crea un DemoRecord de prueba y muestra el total en la base de datos."

    def handle(self, *args: Any, **options: Any) -> None:
        record = DemoRecord.objects.create(label="seed", source="seed")
        total = DemoRecord.objects.count()
        self.stdout.write(f"DemoRecord creado (id={record.pk}); total={total}")
