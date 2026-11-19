from typing import Any

from django.core.management.base import BaseCommand

from apps.accounts import sessions


class Command(BaseCommand):
    help = "Delete expired or invalidated user sessions."

    def handle(self, *args: Any, **options: Any) -> None:
        deleted = sessions.purge_expired()
        self.stdout.write(f"{deleted} expired user sessions deleted.")
