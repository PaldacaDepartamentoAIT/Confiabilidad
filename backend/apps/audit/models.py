from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

_purge_context: ContextVar[bool] = ContextVar("audit_purge_allowed", default=False)


@contextmanager
def _purge_allowed() -> Iterator[None]:
    token = _purge_context.set(True)
    try:
        yield
    finally:
        _purge_context.reset(token)


class InsertOnlyError(Exception):
    def __init__(self) -> None:
        super().__init__(_("Security events are insert-only; they cannot be changed or deleted."))


class EventType(models.TextChoices):
    ACCOUNT_REGISTRATION = "account_registration", "Account registration"
    PENDING_REGISTRATION = "pending_registration", "Pending registration request"
    CODE_SENT = "code_sent", "Code sent"
    CODE_VERIFIED = "code_verified", "Code verified"
    LOGIN = "login", "Login"
    LOCKOUT = "lockout", "Lockout"
    LOGOUT = "logout", "Logout"
    PASSWORD_CHANGE = "password_change", "Password change"
    PASSWORD_RESET = "password_reset", "Password reset"
    PROFILE_EDIT = "profile_edit", "Profile edit"
    ACCOUNT_DISABLE = "account_disable", "Account disable"


class SecurityEventQuerySet(models.QuerySet["SecurityEvent"]):
    def update(self, **kwargs: Any) -> int:
        raise InsertOnlyError

    def delete(self) -> tuple[int, dict[str, int]]:
        if not _purge_context.get():
            raise InsertOnlyError
        return super().delete()

    def bulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("update_conflicts"):
            raise InsertOnlyError
        return super().bulk_create(objs, *args, **kwargs)

    def purge_older_than(self, cutoff: datetime) -> int:
        with _purge_allowed():
            deleted, _ = self.filter(created_at__lt=cutoff).delete()
        return deleted


class SecurityEvent(models.Model):
    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    session_key = models.CharField(max_length=64, blank=True, default="")
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    user_email_hash = models.CharField(max_length=64, blank=True, default="")
    success = models.BooleanField()
    metadata = models.JSONField(default=dict, blank=True)

    objects = SecurityEventQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.event_type} {self.created_at.isoformat()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding or self.pk is not None:
            raise InsertOnlyError
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if not _purge_context.get():
            raise InsertOnlyError
        return super().delete(*args, **kwargs)
