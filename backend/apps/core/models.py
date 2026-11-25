from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class DemoRecord(models.Model):
    # Registro desechable para probar la infraestructura (S-02).
    label = models.CharField(max_length=100)
    source = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.label} ({self.source})"


class MaintenanceTaskName(models.TextChoices):
    PURGE_STALE_REGISTRATIONS = "purge_stale_registrations", _("Purge stale registrations")
    PURGE_EXPIRED_SESSIONS = "purge_expired_sessions", _("Purge expired sessions")
    PURGE_SECURITY_EVENTS = "purge_security_events", _("Purge security events")


class MaintenanceTaskStatus(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", _("Success")
        FAILURE = "failure", _("Failure")

    task_name = models.CharField(
        max_length=64,
        unique=True,
        choices=MaintenanceTaskName.choices,
    )
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=Status.choices)
    deleted_count = models.PositiveIntegerField(default=0)
    error_summary = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["task_name"]
        verbose_name = _("maintenance task status")
        verbose_name_plural = _("maintenance task statuses")

    def __str__(self) -> str:
        return f"{self.task_name}: {self.status}"


class MaintenanceAlert(models.Model):
    task_name = models.CharField(
        max_length=64,
        choices=MaintenanceTaskName.choices,
        db_index=True,
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    error_summary = models.CharField(max_length=500)
    resolved_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("maintenance alert")
        verbose_name_plural = _("maintenance alerts")

    def __str__(self) -> str:
        state = "open" if self.is_open else "resolved"
        return f"{self.task_name} ({state})"

    @property
    def is_open(self) -> bool:
        return self.resolved_at is None
