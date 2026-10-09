from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from allauth.account.models import EmailAddress
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts import codes, processes
from apps.accounts.models import PendingRegistration, User
from apps.accounts.processes import VerifyResult as VerifyResult

_PURPOSE = codes.Purpose.REGISTRATION


@dataclass(frozen=True)
class Started:
    public_id: str
    code: str


@dataclass(frozen=True)
class AccountExists:
    pass


def start(*, email: str, name: str, birthdate: date, country: str) -> Started | AccountExists:
    pending = PendingRegistration(email=email, name=name, birthdate=birthdate, country=country)
    code = processes.issue_code(pending, _PURPOSE)
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
    return Started(public_id=pending.public_id, code=code)


def _reissue(pending: PendingRegistration) -> Started:
    code = processes.issue_code(pending, _PURPOSE)
    pending.save(update_fields=processes.ISSUED_FIELDS)
    return Started(public_id=pending.public_id, code=code)


def verify(*, public_id: str, code: str) -> VerifyResult:
    with transaction.atomic():
        pending = (
            PendingRegistration.objects.select_for_update().filter(public_id=public_id).first()
        )
        if pending is None:
            return VerifyResult.NOT_FOUND
        if pending.is_expired:
            return VerifyResult.EXPIRED
        return processes.check_code(pending, _PURPOSE, code)


@dataclass(frozen=True)
class Resent:
    public_id: str
    code: str


class ResendRefusal(StrEnum):
    EXPIRED = "expired"
    ALREADY_VERIFIED = "already_verified"
    NOT_FOUND = "not_found"


def resend(*, public_id: str) -> Resent | ResendRefusal:
    with transaction.atomic():
        pending = (
            PendingRegistration.objects.select_for_update().filter(public_id=public_id).first()
        )
        if pending is None:
            return ResendRefusal.NOT_FOUND
        if pending.is_expired:
            return ResendRefusal.EXPIRED
        if pending.code_validated_at is not None:
            return ResendRefusal.ALREADY_VERIFIED
        code = processes.renew_code(pending, _PURPOSE)
        return Resent(public_id=public_id, code=code)


@dataclass(frozen=True)
class Completed:
    user: User


class CompleteRefusal(StrEnum):
    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    CODE_NOT_VERIFIED = "code_not_verified"
    ACCOUNT_EXISTS = "account_exists"


def complete(*, public_id: str, password: str) -> Completed | CompleteRefusal:
    with transaction.atomic():
        pending = (
            PendingRegistration.objects.select_for_update().filter(public_id=public_id).first()
        )
        if pending is None:
            return CompleteRefusal.NOT_FOUND
        if pending.is_expired:
            return CompleteRefusal.EXPIRED
        if pending.code_validated_at is None:
            return CompleteRefusal.CODE_NOT_VERIFIED
        if User.objects.filter(email__iexact=pending.email).exists():
            pending.delete()
            return CompleteRefusal.ACCOUNT_EXISTS
        user = User(
            email=pending.email,
            name=pending.name,
            birthdate=pending.birthdate,
            country=pending.country,
        )
        validate_password(password, user=user)
        user.set_password(password)
        user.save()
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        pending.delete()
        return Completed(user=user)


def purge_expired() -> int:
    _total, by_model = PendingRegistration.objects.expired().delete()
    return by_model.get(PendingRegistration._meta.label, 0)


def _is_account_conflict(error: ValidationError) -> bool:
    errors = error.error_dict
    return set(errors) == {"email"} and all(e.code == "email_has_account" for e in errors["email"])
