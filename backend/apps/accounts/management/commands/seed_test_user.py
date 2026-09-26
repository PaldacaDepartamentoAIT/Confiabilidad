from typing import Any

from django.core.management.base import BaseCommand

from apps.accounts.models import User

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test-password-123"


class Command(BaseCommand):
    help = "Crea (idempotente) un usuario de prueba por email para verificar el login."

    def handle(self, *args: Any, **options: Any) -> None:
        if User.objects.filter(email=TEST_EMAIL).exists():
            self.stdout.write(f"Usuario de prueba ya existía: {TEST_EMAIL}")
            return
        User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        self.stdout.write(f"Usuario de prueba creado: {TEST_EMAIL}")
