from typing import Any, ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.consents.hashing import email_fingerprint
from apps.consents.validators import (
    VERSION_MAX_LENGTH,
    validate_content,
    validate_locale,
    validate_version,
)

PROTECTED_FIELDS = (
    "kind",
    "content",
    "version",
    "locale",
    "published_at",
    "requires_reacceptance",
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

    history = HistoricalRecords()

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
        if not self._state.adding:
            stored = Terms.objects.get(pk=self.pk)
            changed = any(
                getattr(self, field) != getattr(stored, field) for field in PROTECTED_FIELDS
            )
            if changed and stored.has_acceptances():
                raise _version_locked_error()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.has_acceptances():
            raise _version_locked_error()
        return super().delete(*args, **kwargs)

    def has_acceptances(self) -> bool:
        # Bloquea la versión entera: basta una aceptación en cualquiera de sus idiomas (RF-005).
        return (
            Terms.objects.filter(kind=self.kind, version__iexact=self.version)
            .filter(
                models.Q(acceptances__isnull=False) | models.Q(marketing_consents__isnull=False)
            )
            .exists()
        )

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


def _version_locked_error() -> ValidationError:
    return ValidationError(
        _("This version has acceptances; its documents cannot be changed or deleted."),
        code="version_locked",
    )


def _allowed_author(record: Any, author: Any) -> Any:
    # Autor del historial: solo staff activo y nunca el usuario de la fila (RF-020).
    if author is None or not (author.is_staff and author.is_active):
        return None
    if author.pk in (record.user_id, getattr(record, "_stored_user_id", None)):
        return None
    return author


def _history_author(instance: Any, request: Any = None, **kwargs: Any) -> Any:
    return _allowed_author(instance, getattr(request, "user", None))


def _remember_stored_user(record: Any) -> None:
    # Al vaciar el usuario, el dueño anterior tampoco puede constar como autor (RF-020).
    if not record._state.adding:
        record._stored_user_id = (
            type(record).objects.filter(pk=record.pk).values_list("user_id", flat=True).get()
        )


def _filter_explicit_author(record: Any) -> None:
    # El panel fija `_history_user` directamente y se saltaría `get_user`.
    if hasattr(record, "_history_user"):
        record._history_user = _allowed_author(record, record._history_user)


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

    history = HistoricalRecords(excluded_fields=["user"], get_user=_history_author)

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
        _refresh_email_hash(self)
        _remember_stored_user(self)
        _filter_explicit_author(self)
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        _check_user_not_reassigned(self)


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

    history = HistoricalRecords(excluded_fields=["user"], get_user=_history_author)

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
        _refresh_email_hash(self)
        _remember_stored_user(self)
        _filter_explicit_author(self)
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        _check_user_not_reassigned(self)


def _refresh_email_hash(record: UserTerms | MarketingConsent) -> None:
    # La huella la calcula siempre el sistema, solo al crear, y después no cambia (RF-012).
    if record._state.adding:
        if record.user is None:
            raise ValidationError(
                {"user": ValidationError(_("A user is required."), code="user_required")}
            )
        record.user_email_hash = email_fingerprint(record.user.email)
        return
    record.user_email_hash = (
        type(record).objects.filter(pk=record.pk).values_list("user_email_hash", flat=True).get()
    )


def _check_user_not_reassigned(record: UserTerms | MarketingConsent) -> None:
    # Solo se puede vaciar el usuario; nunca asignar otro, tampoco a una fila sin usuario (RF-012).
    if record._state.adding or record.user_id is None:
        return
    stored_user_id = (
        type(record).objects.filter(pk=record.pk).values_list("user_id", flat=True).get()
    )
    if record.user_id != stored_user_id:
        raise ValidationError(
            {
                "user": ValidationError(
                    _("The user of an existing record cannot be changed."),
                    code="user_reassigned",
                )
            }
        )
