from datetime import date

import pytest
from django.core.exceptions import ValidationError

from apps.accounts import profile
from apps.accounts.models import User
from apps.accounts.tests.factories import make_user
from apps.audit.models import EventType, SecurityEvent

pytestmark = pytest.mark.django_db


def test_get_profile_returns_only_expected_fields() -> None:
    user = make_user(
        email="ana@example.com",
        name="Ana Pérez",
        birthdate=date(1992, 4, 15),
        country="es",
        language="en",
    )

    data = profile.get_profile(user)

    assert data == profile.ProfileData(
        email="ana@example.com",
        name="Ana Pérez",
        birthdate=date(1992, 4, 15),
        country="ES",
    )


def test_update_profile_partial_changes_record_history_and_audit() -> None:
    user = make_user(
        email="eva@example.com",
        name="Eva Gómez",
        birthdate=date(1990, 5, 10),
        country="ES",
    )
    initial_history = user.history.count()

    updated = profile.update_profile(user, name="  Eva María Gómez  ", country="br")

    user.refresh_from_db()
    assert updated == profile.ProfileData(
        email="eva@example.com",
        name="Eva María Gómez",
        birthdate=date(1990, 5, 10),
        country="BR",
    )
    assert user.name == "Eva María Gómez"
    assert user.country == "BR"
    assert user.birthdate == date(1990, 5, 10)
    assert user.history.count() == initial_history + 1
    assert (
        SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT, success=True).count() == 1
    )


def test_update_profile_without_real_changes_skips_history_and_audit() -> None:
    user = make_user(
        email="luis@example.com",
        name="Luis Díaz",
        birthdate=date(1988, 2, 20),
        country="PT",
    )
    initial_history = user.history.count()

    updated = profile.update_profile(user, name="  Luis Díaz ", country="pt")

    assert updated == profile.ProfileData(
        email="luis@example.com",
        name="Luis Díaz",
        birthdate=date(1988, 2, 20),
        country="PT",
    )
    assert user.history.count() == initial_history
    assert not SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT).exists()


def test_update_profile_preserves_placeholder_zz_only_while_unchanged() -> None:
    user = make_user(name="Usuario sin nombre", birthdate=date(1900, 1, 1), country="ES")
    User.objects.filter(pk=user.pk).update(country="ZZ")
    user.refresh_from_db()
    SecurityEvent.objects.all().delete()

    updated = profile.update_profile(user, name="Nombre Real")
    assert updated.country == "ZZ"
    assert updated.name == "Nombre Real"
    assert (
        SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT, success=True).count() == 1
    )

    updated_country = profile.update_profile(user, country="es")
    assert updated_country.country == "ES"

    with pytest.raises(ValidationError) as exc_info:
        profile.update_profile(user, country="ZZ")
    assert "country" in exc_info.value.error_dict


def test_update_profile_rejects_invalid_values_without_saving_or_auditing() -> None:
    user = make_user(name="Ana", birthdate=date(1990, 1, 1), country="ES")

    with pytest.raises(ValidationError) as name_err:
        profile.update_profile(user, name="Ana  Ruiz")
    assert "name" in name_err.value.error_dict

    with pytest.raises(ValidationError) as age_err:
        profile.update_profile(user, birthdate=date.today())
    assert "birthdate" in age_err.value.error_dict

    with pytest.raises(ValidationError) as country_err:
        profile.update_profile(user, country="XX")
    assert "country" in country_err.value.error_dict

    user.refresh_from_db()
    assert user.name == "Ana"
    assert user.birthdate == date(1990, 1, 1)
    assert user.country == "ES"
    assert not SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT).exists()
