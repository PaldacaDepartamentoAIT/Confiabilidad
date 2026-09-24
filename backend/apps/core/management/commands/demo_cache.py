from typing import Any

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Escribe y lee una clave en la caché de Redis para verificarla."

    def handle(self, *args: Any, **options: Any) -> None:
        cache.set("demo-command-key", "demo-command-value", timeout=60)
        value = cache.get("demo-command-key")
        self.stdout.write(f"Cache get -> {value}")
