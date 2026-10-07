from typing import Any, ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
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
        if self.kind == self.Kind.MARKETING:
            self.requires_reacceptance = False
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        if (
            self.kind == self.Kind.TERMS
            and self._siblings().exclude(requires_reacceptance=self.requires_reacceptance).exists()
        ):
            raise ValidationError(
                {
                    "requires_reacceptance": ValidationError(
                        _("Every language of a version must have the same re-acceptance value."),
                        code="reacceptance_mismatch",
                    )
                }
            )

    def _siblings(self) -> models.QuerySet["Terms"]:
        return Terms.objects.filter(kind=self.kind, version__iexact=self.version).exclude(
            pk=self.pk
        )


class UserTerms(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="terms_acceptances",
    )
    terms = models.ForeignKey(
        Terms,
        on_delete=models.PROTECT,
        related_name="acceptances",
        limit_choices_to={"kind": Terms.Kind.TERMS},
    )
    user_email_hash = models.CharField(max_length=64, editable=False)
    terms_accepted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("terms acceptance")
        verbose_name_plural = _("terms acceptances")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["user", "terms"],
                condition=models.Q(revoked_at__isnull=True),
                name="consents_userterms_active_unique",
                violation_error_message=_("This user has already accepted this document."),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.terms} · {self.user_email_hash[:12]}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class MarketingConsent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="marketing_consents",
    )
    terms = models.ForeignKey(
        Terms,
        on_delete=models.PROTECT,
        related_name="marketing_consents",
        limit_choices_to={"kind": Terms.Kind.MARKETING},
    )
    user_email_hash = models.CharField(max_length=64, editable=False)
    granted = models.BooleanField(default=True)
    granted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("marketing consent")
        verbose_name_plural = _("marketing consents")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(granted=True),
                name="consents_marketingconsent_active_unique",
                violation_error_message=_("This user already has an active marketing consent."),
            ),
            models.CheckConstraint(
                condition=models.Q(granted=True, revoked_at__isnull=True)
                | models.Q(granted=False, revoked_at__isnull=False),
                name="consents_marketingconsent_granted_matches_revocation",
                violation_error_message=_(
                    "A consent is granted if and only if it has no revocation date."
                ),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.terms} · {self.user_email_hash[:12]}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
