from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts import codes, conf
from apps.accounts.models import PendingRegistration


@dataclass(frozen=True)
class Started:
    public_id: str
    code: str


@dataclass(frozen=True)
class AccountExists:
    pass


def start(*, email: str, name: str, birthdate: date, country: str) -> Started | AccountExists:
    public_id, code = codes.generate_public_id(), codes.generate_code()
    pending = PendingRegistration(
        email=email,
        name=name,
        birthdate=birthdate,
        country=country,
        public_id=public_id,
        code_hash=codes.code_fingerprint(public_id, code),
        code_expires_at=timezone.now() + conf.code_ttl(),
    )
    with transaction.atomic():
        PendingRegistration.objects.expired().filter(email__iexact=email.strip()).delete()
        try:
            with transaction.atomic():
                pending.save()
        except ValidationError as error:
            if _is_account_conflict(error):
                return AccountExists()
            raise
        except IntegrityError:
            existing = (
                PendingRegistration.objects.select_for_update()
                .filter(email__iexact=pending.email)
                .first()
            )
            if existing is None:
                raise
            return _reissue(existing)
    return Started(public_id=public_id, code=code)


def _reissue(pending: PendingRegistration) -> Started:
    public_id, code = codes.generate_public_id(), codes.generate_code()
    pending.public_id = public_id
    pending.code_hash = codes.code_fingerprint(public_id, code)
    pending.code_expires_at = timezone.now() + conf.code_ttl()
    pending.failed_attempts = 0
    pending.code_validated_at = None
    pending.save(
        update_fields=[
            "public_id",
            "code_hash",
            "code_expires_at",
            "failed_attempts",
            "code_validated_at",
        ]
    )
    return Started(public_id=public_id, code=code)


class VerifyResult(StrEnum):
    VERIFIED = "verified"
    WRONG_CODE = "wrong_code"
    LOCKED = "locked"
    CODE_EXPIRED = "code_expired"
    EXPIRED = "expired"
    ALREADY_VERIFIED = "already_verified"
    NOT_FOUND = "not_found"


def verify(*, public_id: str, code: str) -> VerifyResult:
    with transaction.atomic():
        pending = (
            PendingRegistration.objects.select_for_update().filter(public_id=public_id).first()
        )
        if pending is None:
            return VerifyResult.NOT_FOUND
        if pending.is_expired:
            return VerifyResult.EXPIRED
        if pending.code_validated_at is not None:
            return VerifyResult.ALREADY_VERIFIED
        if pending.is_locked:
            return VerifyResult.LOCKED
        if timezone.now() >= pending.code_expires_at:
            return VerifyResult.CODE_EXPIRED
        if not codes.verify_code(public_id, code, pending.code_hash):
            pending.failed_attempts += 1
            pending.save(update_fields=["failed_attempts"])
            return VerifyResult.WRONG_CODE
        pending.code_validated_at = timezone.now()
        pending.save(update_fields=["code_validated_at"])
        return VerifyResult.VERIFIED


def _is_account_conflict(error: ValidationError) -> bool:
    errors = error.error_dict
    return set(errors) == {"email"} and all(e.code == "email_has_account" for e in errors["email"])
