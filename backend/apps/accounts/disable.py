from dataclasses import dataclass
from enum import StrEnum

from django.db import transaction
from django.utils import timezone

from apps.accounts import signals, throttling
from apps.accounts.models import PasswordResetRequest, PhantomProcess, User
from apps.companies.models import owns_company
from apps.emails import outbox


class DisableBlockReason(StrEnum):
    OWNS_COMPANY = "owns_company"
    LAST_SUPERUSER = "last_superuser"
    INACTIVE_ACCOUNT = "inactive_account"


@dataclass(frozen=True)
class AccountDisabled:
    user: User


@dataclass(frozen=True)
class DisableBlocked:
    reason: DisableBlockReason


@dataclass(frozen=True)
class DisableLocked:
    retry_after: int


@dataclass(frozen=True)
class DisableInvalid:
    missing_password: bool = False


DisableResult = AccountDisabled | DisableBlocked | DisableLocked | DisableInvalid


def disable_block_reason(user: User) -> DisableBlockReason | None:
    if not user.is_active:
        return DisableBlockReason.INACTIVE_ACCOUNT
    if owns_company(user):
        return DisableBlockReason.OWNS_COMPANY
    if user.is_superuser and not User.active.filter(is_superuser=True).exclude(pk=user.pk).exists():
        return DisableBlockReason.LAST_SUPERUSER
    return None


def _invalidate_pending_password_reset(user: User) -> None:
    pending = PasswordResetRequest.objects.filter(user=user).first()
    if pending is None:
        return
    tombstone = PhantomProcess(
        purpose=PhantomProcess.Purpose.PASSWORD_RESET,
        email="",
        public_id=pending.public_id,
        code_hash="",
        code_expires_at=pending.code_expires_at,
        answers_expired=True,
    )
    tombstone.save()
    PhantomProcess.objects.filter(pk=tombstone.pk).update(created_at=pending.created_at)
    pending.delete()


def disable_account(
    user: User,
    *,
    current_password: str = "",
    require_password: bool = True,
) -> DisableResult:
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        if not locked.is_active:
            return DisableBlocked(reason=DisableBlockReason.INACTIVE_ACCOUNT)
        if owns_company(locked):
            return DisableBlocked(reason=DisableBlockReason.OWNS_COMPANY)
        if (
            locked.is_superuser
            and not User.active.select_for_update()
            .filter(is_superuser=True)
            .exclude(pk=locked.pk)
            .exists()
        ):
            return DisableBlocked(reason=DisableBlockReason.LAST_SUPERUSER)

        if require_password:
            verdict = throttling.check_account_disable(locked.pk)
            if not verdict.allowed:
                return DisableLocked(retry_after=verdict.retry_after)
            if not current_password:
                return DisableInvalid(missing_password=True)
            if not locked.check_password(current_password):
                throttling.record_account_disable_failure(locked.pk)
                return DisableInvalid(missing_password=False)

        locked.is_active = False
        locked.disabled_at = timezone.now()
        locked.save(update_fields=["is_active", "disabled_at"])
        _invalidate_pending_password_reset(locked)
        signals.account_disabled.send(sender=User, email=locked.email, success=True)
        outbox.enqueue(
            kind="account_disabled",
            recipient=locked.email,
            locale=locked.language,
            context={"name": locked.name},
            account=locked,
        )
        user_id = locked.pk
        transaction.on_commit(lambda: throttling.clear_account_disable_failures(user_id))

    user.is_active = locked.is_active
    user.disabled_at = locked.disabled_at
    return AccountDisabled(user=locked)
