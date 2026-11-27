import calendar
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from django.db import transaction
from django.utils import timezone

from apps.accounts import conf, signals, throttling
from apps.accounts.models import PasswordResetRequest, PhantomProcess, User
from apps.companies.models import owns_company
from apps.emails import outbox

logger = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class AccountReactivated:
    user: User


@dataclass(frozen=True)
class ReactivationExpired:
    deadline: datetime


@dataclass(frozen=True)
class ReactivationAlreadyActive:
    pass


ReactivationResult = AccountReactivated | ReactivationExpired | ReactivationAlreadyActive


def retention_deadline(disabled_at: datetime, *, months: int | None = None) -> datetime:
    total_months = conf.account_disable_retention_months() if months is None else months
    start = disabled_at.astimezone(UTC) if disabled_at.tzinfo else disabled_at.replace(tzinfo=UTC)
    zero_based_month = (start.month - 1) + total_months
    year = start.year + (zero_based_month // 12)
    month = (zero_based_month % 12) + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return start.replace(year=year, month=month, day=day)


def is_retention_expired(user: User, *, now: datetime | None = None) -> bool:
    disabled_at = user.disabled_at
    if user.is_active or disabled_at is None:
        return False
    current = timezone.now() if now is None else now
    return current >= retention_deadline(disabled_at)


def reactivate_account(user: User, *, now: datetime | None = None) -> ReactivationResult:
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        if locked.is_active:
            return ReactivationAlreadyActive()
        disabled_at = locked.disabled_at
        if disabled_at is not None:
            deadline = retention_deadline(disabled_at)
            current = timezone.now() if now is None else now
            if current >= deadline:
                return ReactivationExpired(deadline=deadline)
        locked.is_active = True
        locked.disabled_at = None
        locked.save(update_fields=["is_active", "disabled_at"])

    user.is_active = locked.is_active
    user.disabled_at = locked.disabled_at
    return AccountReactivated(user=locked)


class DisabledAccountPurgeAnomaly(RuntimeError):
    """Raised after partial purge when expired disabled accounts still own companies."""


def purge_expired_accounts(*, now: datetime | None = None) -> int:
    current = timezone.now() if now is None else now
    candidates = list(
        User.objects.filter(is_active=False, disabled_at__isnull=False).order_by("pk")
    )
    deleted_count = 0
    skipped_ids: list[int] = []
    for candidate in candidates:
        if not is_retention_expired(candidate, now=current):
            continue
        if owns_company(candidate):
            logger.error(
                "Cannot purge expired disabled account %s because it still owns at least one "
                "company.",
                candidate.pk,
            )
            skipped_ids.append(candidate.pk)
            continue
        with transaction.atomic():
            locked = (
                User.objects.select_for_update()
                .filter(pk=candidate.pk, is_active=False, disabled_at__isnull=False)
                .first()
            )
            if locked is None or not is_retention_expired(locked, now=current):
                continue
            if owns_company(locked):
                logger.error(
                    "Cannot purge expired disabled account %s because it still owns at least one "
                    "company.",
                    locked.pk,
                )
                skipped_ids.append(locked.pk)
                continue
            locked.delete()
            deleted_count += 1
    if skipped_ids:
        raise DisabledAccountPurgeAnomaly(
            f"Skipped {len(skipped_ids)} expired disabled account(s) still owning a company "
            f"(ids={skipped_ids})."
        )
    return deleted_count
