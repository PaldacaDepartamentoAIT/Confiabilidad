from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Final

from django.db import transaction

from apps.accounts import signals
from apps.accounts.models import User
from apps.accounts.validators import normalize_country, normalize_name


class _Unset(Enum):
    TOKEN = 0


UNSET: Final = _Unset.TOKEN


@dataclass(frozen=True)
class ProfileData:
    email: str
    name: str
    birthdate: date
    country: str


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
