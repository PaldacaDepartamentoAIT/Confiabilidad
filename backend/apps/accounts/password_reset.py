from dataclasses import dataclass
from enum import StrEnum

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts import codes, processes
from apps.accounts.models import PasswordResetRequest, User
from apps.accounts.processes import VerifyResult as VerifyResult

_PURPOSE = codes.Purpose.PASSWORD_RESET
_REPLACED_FIELDS = [*processes.ISSUED_FIELDS, "created_at", "account_stamp"]


@dataclass(frozen=True)
class Started:
    public_id: str
    code: str


@dataclass(frozen=True)
class NoEligibleAccount:
    pass


def start(*, email: str) -> Started | NoEligibleAccount:
    with transaction.atomic():
        user = User.objects.select_for_update().filter(email__iexact=email.strip()).first()
        if user is None or not user.is_active:
            return NoEligibleAccount()
        request = _locked_request(user)
        if request is None:
            request = PasswordResetRequest(user=user)
            code = _issue(request)
            try:
                with transaction.atomic():
                    request.save()
                return Started(public_id=request.public_id, code=code)
            except IntegrityError:
                request = _locked_request(user)
                if request is None:
                    raise
        code = _issue(request)
        request.save(update_fields=_REPLACED_FIELDS)
        return Started(public_id=request.public_id, code=code)


class AccountRefusal(StrEnum):
    INACTIVE = "inactive"
    ACCOUNT_CHANGED = "account_changed"


def verify(*, public_id: str, code: str) -> VerifyResult | AccountRefusal:
    with transaction.atomic():
        request = _locked_by_public_id(public_id)
        if request is None:
            return VerifyResult.NOT_FOUND
        if request.is_expired:
            return VerifyResult.EXPIRED
        refusal = _account_refusal(request)
        if refusal is not None:
            return refusal
        return processes.check_code(request, _PURPOSE, code)


@dataclass(frozen=True)
class Resent:
    public_id: str
    code: str


class ResendRefusal(StrEnum):
    EXPIRED = "expired"
    ALREADY_VERIFIED = "already_verified"
    NOT_FOUND = "not_found"


def resend(*, public_id: str) -> Resent | ResendRefusal | AccountRefusal:
    with transaction.atomic():
        request = _locked_by_public_id(public_id)
        if request is None:
            return ResendRefusal.NOT_FOUND
        if request.is_expired:
            return ResendRefusal.EXPIRED
        refusal = _account_refusal(request)
        if refusal is not None:
            return refusal
        if request.code_validated_at is not None:
            return ResendRefusal.ALREADY_VERIFIED
        return Resent(public_id=public_id, code=processes.renew_code(request, _PURPOSE))


def _locked_by_public_id(public_id: str) -> PasswordResetRequest | None:
    return (
        PasswordResetRequest.objects.select_for_update(of=("self",))
        .select_related("user")
        .filter(public_id=public_id)
        .first()
    )


def _account_refusal(request: PasswordResetRequest) -> AccountRefusal | None:
    user = request.user
    if not user.is_active:
        return AccountRefusal.INACTIVE
    if not codes.account_stamp_matches(request.account_stamp, user.email, user.password):
        return AccountRefusal.ACCOUNT_CHANGED
    return None


def _locked_request(user: User) -> PasswordResetRequest | None:
    return PasswordResetRequest.objects.select_for_update().filter(user=user).first()


def _issue(request: PasswordResetRequest) -> str:
    code = processes.issue_code(request, _PURPOSE)
    request.created_at = timezone.now()
    request.account_stamp = codes.account_stamp(request.user.email, request.user.password)
    return code
