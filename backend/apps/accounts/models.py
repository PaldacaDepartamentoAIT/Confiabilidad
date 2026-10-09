from collections.abc import Callable, Collection
from datetime import datetime
from typing import Any, ClassVar

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.accounts import conf
from apps.accounts.validators import (
    NAME_MAX_LENGTH,
    PLACEHOLDER_COUNTRY,
    normalize_country,
    normalize_name,
    validate_birthdate,
    validate_country,
    validate_name,
)


class UserManager(BaseUserManager["User"]):
    def create_user(self, email: str, password: str | None = None, **extra: Any) -> "User":
        if not email:
            raise ValueError(_("Email is required."))
        missing = [field for field in self.model.REQUIRED_FIELDS if not extra.get(field)]
        if missing:
            raise ValueError(
                _("Missing required fields: %(fields)s.") % {"fields": ", ".join(missing)}
            )
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra: Any) -> "User":
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


HISTORY_EXCLUDED_FIELDS = frozenset({"password", "last_login"})


def _check_profile(
    instance: "User | PendingRegistration",
    excluded: set[str],
    errors: dict[str, list[ValidationError]],
    stored_country: Callable[[], str | None],
) -> None:
    checks: dict[str, Callable[[], None]] = {
        "name": lambda: validate_name(instance.name),
        "birthdate": lambda: validate_birthdate(instance.birthdate),
        "country": lambda: validate_country(instance.country, stored_country()),
    }
    for field_name, check in checks.items():
        if field_name in excluded or field_name in errors:
            continue
        try:
            check()
        except ValidationError as error:
            errors[field_name] = error.error_list


class ActiveUserManager(models.Manager["User"]):
    def get_queryset(self) -> models.QuerySet["User"]:
        return super().get_queryset().filter(is_active=True)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    birthdate = models.DateField()
    country = models.CharField(max_length=2)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    active = ActiveUserManager()
    history = HistoricalRecords(excluded_fields=sorted(HISTORY_EXCLUDED_FIELDS))
    # simple-history omite el registro si este atributo existe en la instancia.
    skip_history_when_saving: bool

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["name", "birthdate", "country"]

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                Lower("email"),
                name="accounts_user_email_ci_unique",
                violation_error_message=_("A user with this email already exists."),
            ),
        ]

    def __str__(self) -> str:
        return self.email

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.email = self.email.strip().lower()
        self.name = normalize_name(self.name)
        self.country = normalize_country(self.country)
        # La contraseña la gestiona allauth; la unicidad del correo, la base de datos.
        exclude = {"password"}
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            exclude |= {
                field.name
                for field in self._meta.concrete_fields
                if field.name not in update_fields
            }
        self.full_clean(exclude=exclude, validate_unique=False, validate_constraints=False)
        skip_history = (
            update_fields is not None
            and set(update_fields) <= HISTORY_EXCLUDED_FIELDS
            and not hasattr(self, "skip_history_when_saving")
        )
        if skip_history:
            self.skip_history_when_saving = True
        try:
            super().save(*args, **kwargs)
        finally:
            if skip_history:
                del self.skip_history_when_saving

    def clean_fields(self, exclude: Collection[str] | None = None) -> None:
        excluded = set(exclude or ())
        errors: dict[str, list[ValidationError]] = {}
        try:
            super().clean_fields(exclude=exclude)
        except ValidationError as error:
            errors = dict(error.error_dict)
        _check_profile(self, excluded, errors, self._stored_country)
        if errors:
            raise ValidationError(errors)

    def _stored_country(self) -> str | None:
        if self._state.adding or self.country != PLACEHOLDER_COUNTRY:
            return None
        return type(self).objects.filter(pk=self.pk).values_list("country", flat=True).first()


class CodeProcessQuerySet[P: "CodeProcess"](models.QuerySet[P]):
    def expired(self) -> "CodeProcessQuerySet[P]":
        now = timezone.now()
        return self.filter(
            models.Q(code_expires_at__lte=now - conf.grace_period())
            | models.Q(created_at__lte=now - conf.max_lifetime())
        )


class CodeProcess(models.Model):
    public_id = models.CharField(max_length=64, unique=True)
    code_hash = models.CharField(max_length=64)
    code_expires_at = models.DateTimeField()
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    code_validated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    @property
    def expires_at(self) -> datetime:
        return min(
            self.code_expires_at + conf.grace_period(),
            self.created_at + conf.max_lifetime(),
        )

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_locked(self) -> bool:
        return self.failed_attempts >= conf.max_failed_attempts()


class PendingRegistration(CodeProcess):
    email = models.EmailField()
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    birthdate = models.DateField()
    country = models.CharField(max_length=2)

    objects = CodeProcessQuerySet["PendingRegistration"].as_manager()

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                Lower("email"),
                name="accounts_pendingregistration_email_ci_unique",
                violation_error_message=_("A pending registration with this email already exists."),
            ),
        ]

    def __str__(self) -> str:
        return self.email

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.email = self.email.strip().lower()
        self.name = normalize_name(self.name)
        self.country = normalize_country(self.country)
        update_fields = kwargs.get("update_fields")
        exclude: set[str] = set()
        if update_fields is not None:
            exclude = {
                field.name
                for field in self._meta.concrete_fields
                if field.name not in update_fields
            }
        self.full_clean(exclude=exclude, validate_unique=False, validate_constraints=False)
        if "email" not in exclude and User.objects.filter(email__iexact=self.email).exists():
            raise ValidationError(
                {
                    "email": ValidationError(
                        _("An account with this email already exists."),
                        code="email_has_account",
                    )
                }
            )
        super().save(*args, **kwargs)

    def clean_fields(self, exclude: Collection[str] | None = None) -> None:
        errors: dict[str, list[ValidationError]] = {}
        try:
            super().clean_fields(exclude=exclude)
        except ValidationError as error:
            errors = dict(error.error_dict)
        _check_profile(self, set(exclude or ()), errors, lambda: None)
        if errors:
            raise ValidationError(errors)


class PasswordResetRequest(CodeProcess):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="password_reset_request"
    )
    account_stamp = models.CharField(max_length=64)

    objects = CodeProcessQuerySet["PasswordResetRequest"].as_manager()

    def __str__(self) -> str:
        return self.user.email
