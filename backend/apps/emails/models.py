from typing import Any, ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.emails import rendering


def _deletion_refused() -> ValidationError:
    return ValidationError(_("Email templates cannot be deleted."), code="template_protected")


class EmailTemplateQuerySet(models.QuerySet["EmailTemplate"]):
    def delete(self) -> tuple[int, dict[str, int]]:
        raise _deletion_refused()


class EmailTemplate(models.Model):
    class Kind(models.TextChoices):
        REGISTRATION_CODE = "registration_code", _("Registration code")
        PASSWORD_RESET_CODE = "password_reset_code", _("Password reset code")
        ACCOUNT_EXISTS = "account_exists", _("You already have an account")
        PASSWORD_RESET_DONE = "password_reset_done", _("Password reset")
        PASSWORD_CHANGED = "password_changed", _("Password changed")
        ACCOUNT_DISABLED = "account_disabled", _("Account disabled")
        SESSIONS_CLOSED = "sessions_closed", _("Sessions closed remotely")

    class Locale(models.TextChoices):
        ES = "es", "Español"
        PT_BR = "pt-BR", "Português (Brasil)"
        EN = "en", "English"

    kind = models.CharField(max_length=32, choices=Kind.choices)
    locale = models.CharField(max_length=5, choices=Locale.choices)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    objects = EmailTemplateQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("email template")
        verbose_name_plural = _("email templates")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                "kind",
                "locale",
                name="emails_template_kind_locale_unique",
                violation_error_message=_("A template for this kind and language already exists."),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kind} ({self.locale})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean(validate_unique=False, validate_constraints=False)
        super().save(*args, **kwargs)

    def clean(self) -> None:
        rendering.validate_template(self.kind, self.subject, self.body)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise _deletion_refused()


class OutboundEmail(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        FAILED = "failed", _("Failed")

    kind = models.CharField(max_length=32, choices=EmailTemplate.Kind.choices)
    locale = models.CharField(max_length=5, choices=EmailTemplate.Locale.choices)
    recipient = models.EmailField()
    # Solo datos no secretos (nombre, identificador público); el código nunca va aquí (RF-018).
    context = models.JSONField(default=dict, blank=True)
    purpose = models.CharField(max_length=32, blank=True)
    public_id = models.CharField(max_length=64, blank=True)
    masked_code = models.PositiveIntegerField(null=True, blank=True)
    code_nonce = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("outbound email")
        verbose_name_plural = _("outbound emails")
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["status", "next_attempt_at"], name="emails_outbound_due_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.kind} → {self.recipient}"


class FailedEmailManager(models.Manager["FailedEmail"]):
    def get_queryset(self) -> models.QuerySet["FailedEmail"]:
        return super().get_queryset().filter(status=OutboundEmail.Status.FAILED)


class FailedEmail(OutboundEmail):
    # Vista del panel sobre los correos que agotaron sus intentos o se rechazaron (RF-017).
    objects = FailedEmailManager()  # type: ignore[misc]

    class Meta:
        proxy = True
        verbose_name = _("failed email")
        verbose_name_plural = _("failed emails")


class AccountExistsNotice(models.Model):
    # Hora del último aviso "ya tienes cuenta" encolado para la cuenta: es el tope de RF-007.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account_exists_notice"
    )
    last_queued_at = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.user_id} @ {self.last_queued_at:%Y-%m-%d %H:%M}"
