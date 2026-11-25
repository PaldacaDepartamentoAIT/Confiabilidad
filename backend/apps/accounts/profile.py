from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Final

from allauth.account.signals import password_changed
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpRequest

from apps.accounts import sessions, signals, throttling
from apps.accounts.models import User
from apps.accounts.validators import normalize_country, normalize_name
from apps.emails import outbox


class _Unset(Enum):
    TOKEN = 0


UNSET: Final = _Unset.TOKEN


@dataclass(frozen=True)
class ProfileData:
    email: str
    name: str
    birthdate: date
    country: str


@dataclass(frozen=True)
class PasswordChanged:
    user: User
    revoked_sessions: int


@dataclass(frozen=True)
class PasswordChangeLocked:
    retry_after: int


@dataclass(frozen=True)
class PasswordChangeInvalid:
    current_password_incorrect: bool
    new_password_codes: tuple[str, ...] = ()


def get_profile(user: User) -> ProfileData:
    return ProfileData(
        email=user.email,
        name=user.name,
        birthdate=user.birthdate,
        country=user.country,
    )


def update_profile(
    user: User,
    *,
    name: str | _Unset = UNSET,
    birthdate: date | _Unset = UNSET,
    country: str | _Unset = UNSET,
) -> ProfileData:
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        next_name = normalize_name(name) if not isinstance(name, _Unset) else locked.name
        next_birthdate = birthdate if not isinstance(birthdate, _Unset) else locked.birthdate
        next_country = (
            normalize_country(country) if not isinstance(country, _Unset) else locked.country
        )

        changed_fields: list[str] = []
        if next_name != locked.name:
            locked.name = next_name
            changed_fields.append("name")
        if next_birthdate != locked.birthdate:
            locked.birthdate = next_birthdate
            changed_fields.append("birthdate")
        if next_country != locked.country:
            locked.country = next_country
            changed_fields.append("country")

        if changed_fields:
            locked.save(update_fields=changed_fields)
            signals.profile_edited.send(sender=User, email=locked.email, success=True)

    user.name = locked.name
    user.birthdate = locked.birthdate
    user.country = locked.country
    return get_profile(locked)


def _audit_request(request: HttpRequest | None, active_key: str | None) -> HttpRequest | None:
    if active_key is None:
        return request
    if (
        request is not None
        and getattr(getattr(request, "session", None), "session_key", None) == active_key
    ):
        return request
    copy = HttpRequest()
    if request is not None:
        copy.META = request.META
    copy.session = sessions._session_store(active_key)
    return copy


def change_password(
    user: User,
    *,
    current_password: str,
    new_password: str,
    current_session_key: str | None = None,
    request: HttpRequest | None = None,
    rotate_session_key: bool = True,
) -> PasswordChanged | PasswordChangeLocked | PasswordChangeInvalid:
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        verdict = throttling.check_password_change(locked.pk)
        if not verdict.allowed:
            return PasswordChangeLocked(retry_after=verdict.retry_after)

        current_ok = bool(current_password) and locked.check_password(current_password)
        new_codes: tuple[str, ...] = ()
        if new_password:
            try:
                validate_password(new_password, user=locked)
            except ValidationError as error:
                new_codes = tuple(str(item.code) for item in error.error_list)

        if not current_ok or new_codes or not new_password:
            if current_password and not current_ok:
                throttling.record_password_change_failure(locked.pk)
            return PasswordChangeInvalid(
                current_password_incorrect=not current_ok,
                new_password_codes=new_codes,
            )

        locked.set_password(new_password)
        locked.skip_password_session_revocation = True
        try:
            locked.save(update_fields=["password"])
        finally:
            del locked.skip_password_session_revocation

        active_key = (
            sessions.refresh_current_session(
                locked, current_session_key, request=request, rotate=rotate_session_key
            )
            if current_session_key
            else None
        )
        revoked_count = sessions.revoke_all_other_sessions(locked, active_key, request=request)
        password_changed.send(sender=User, request=_audit_request(request, active_key), user=locked)
        outbox.enqueue(
            kind="password_changed",
            recipient=locked.email,
            locale=locked.language,
            context={"name": locked.name},
            account=locked,
        )
        if revoked_count > 0:
            outbox.enqueue(
                kind="sessions_closed",
                recipient=locked.email,
                locale=locked.language,
                context={"name": locked.name},
                account=locked,
            )
        user_id = locked.pk
        transaction.on_commit(lambda: throttling.clear_password_change_failures(user_id))

    user.password = locked.password
    return PasswordChanged(user=locked, revoked_sessions=revoked_count)
