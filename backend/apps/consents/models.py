from typing import Any, ClassVar

from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from apps.consents.validators import (
    VERSION_MAX_LENGTH,
    validate_content,
    validate_locale,
    validate_version,
)

LOCALE_CHOICES = [("es", "Español"), ("pt-BR", "Português (Brasil)"), ("en", "English")]


class Terms(models.Model):
    class Kind(models.TextChoices):
        TERMS = "terms", _("Terms of use")
        MARKETING = "marketing", _("Marketing")

    kind = models.CharField(max_length=20, choices=Kind.choices)
    content = models.TextField(validators=[validate_content])
    version = models.CharField(max_length=VERSION_MAX_LENGTH, validators=[validate_version])
    locale = models.CharField(max_length=5, choices=LOCALE_CHOICES, validators=[validate_locale])
    requires_reacceptance = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("legal document")
        verbose_name_plural = _("legal documents")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                "kind",
                Lower("version"),
                "locale",
                name="consents_terms_version_ci_unique",
                violation_error_message=_(
                    "A document of this kind with this version and language already exists."
                ),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kind} {self.version} ({self.locale})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
