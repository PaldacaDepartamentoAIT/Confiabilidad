from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


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

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise _deletion_refused()
