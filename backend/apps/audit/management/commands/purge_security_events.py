from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.audit.models import SecurityEvent, purge_expired, retention_cutoff


class Command(BaseCommand):
    help = "Delete security events older than one year."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report how many events would be deleted without deleting them.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        cutoff = retention_cutoff(timezone.now())
        if options["dry_run"]:
            count = SecurityEvent.objects.filter(created_at__lt=cutoff).count()
            self.stdout.write(f"{count} security events would be deleted.")
            return
        deleted = purge_expired(timezone.now())
        self.stdout.write(f"{deleted} security events deleted.")
