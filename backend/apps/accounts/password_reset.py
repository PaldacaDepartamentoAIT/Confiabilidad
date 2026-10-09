from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts import codes, processes
from apps.accounts.models import PasswordResetRequest, User

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


def _locked_request(user: User) -> PasswordResetRequest | None:
    return PasswordResetRequest.objects.select_for_update().filter(user=user).first()


def _issue(request: PasswordResetRequest) -> str:
    code = processes.issue_code(request, _PURPOSE)
    request.created_at = timezone.now()
    request.account_stamp = codes.account_stamp(request.user.email, request.user.password)
    return code
