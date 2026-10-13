from django.db import models
from django.utils import timezone


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


class SecurityEvent(models.Model):
    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    session_key = models.CharField(max_length=64, blank=True, default="")
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    user_email_hash = models.CharField(max_length=64, blank=True, default="")
    success = models.BooleanField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.event_type} {self.created_at.isoformat()}"
