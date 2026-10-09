from dataclasses import dataclass
from enum import StrEnum

from allauth.account import app_settings as allauth_account_settings
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.core.internal import ratelimit as allauth_ratelimit
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.http import HttpRequest
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


@dataclass(frozen=True)
class Completed:
    user: User


class CompleteRefusal(StrEnum):
    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    CODE_NOT_VERIFIED = "code_not_verified"


def complete(*, public_id: str, password: str) -> Completed | CompleteRefusal | AccountRefusal:
    user_id = _owner_id(public_id)
    if user_id is None:
        return CompleteRefusal.NOT_FOUND
    with transaction.atomic():
        # Cuenta antes que solicitud, el mismo orden que en start, para no interbloquearse.
        user = User.objects.select_for_update().filter(pk=user_id).first()
        request = (
            PasswordResetRequest.objects.select_for_update()
            .filter(public_id=public_id, user=user)
            .first()
        )
        if user is None or request is None:
            return CompleteRefusal.NOT_FOUND
        if request.is_expired:
            return CompleteRefusal.EXPIRED
        refusal = _account_refusal(request)
        if refusal is not None:
            return refusal
        if request.code_validated_at is None:
            return CompleteRefusal.CODE_NOT_VERIFIED
        validate_password(password, user=user)
        user.set_password(password)
        user.save(update_fields=["password"])
        _mark_email_verified(user)
        request.delete()
        email = user.email
        transaction.on_commit(lambda: _clear_failed_logins(email))
        return Completed(user=user)


def _owner_id(public_id: str) -> int | None:
    owner: int | None = (
        PasswordResetRequest.objects.filter(public_id=public_id)
        .values_list("user_id", flat=True)
        .first()
    )
    return owner


def _mark_email_verified(user: User) -> None:
    address = EmailAddress.objects.filter(user=user, email__iexact=user.email).first()
    if address is None:
        has_primary = EmailAddress.objects.filter(user=user, primary=True).exists()
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=not has_primary
        )
    elif not address.verified:
        address.verified = True
        address.save(update_fields=["verified"])


def _clear_failed_logins(email: str) -> None:
    # Solo las tasas por correo: la tasa por IP no es de la cuenta (S-12). Con SITE_ID, allauth no
    # necesita una petición real para calcular la clave.
    request = HttpRequest()
    key = get_adapter()._get_login_attempts_cache_key(request, email=email)
    rates = allauth_ratelimit.parse_rates(allauth_account_settings.RATE_LIMITS.get("login_failed"))
    for rate in rates:
        if rate.per == "key":
            cache.delete(
                allauth_ratelimit.get_cache_key(request, action="login_failed", rate=rate, key=key)
            )


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
