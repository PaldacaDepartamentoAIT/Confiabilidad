from datetime import date

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.validators import (
    PLACEHOLDER_COUNTRY,
    minimum_age_date,
    normalize_country,
    normalize_name,
    validate_birthdate,
    validate_country,
    validate_name,
)


@pytest.mark.parametrize(
    "name",
    ["Ana García", "Ñandú Pérez-O'Neill", "Мария Иванова", "李小龍", "a" * 150],
)
def test_valid_names_are_accepted(name: str) -> None:
    validate_name(name)


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("", "name_empty"),
        ("a" * 151, "name_too_long"),
        ("Ana  García", "name_consecutive_spaces"),
        ("Ana\u00a0\u00a0García", "name_consecutive_spaces"),
        ("李\u3000\u3000小龍", "name_consecutive_spaces"),
        ("Ana \u2003García", "name_consecutive_spaces"),
        ("Ana\tGarcía", "name_control_char"),
        ("Ana\nGarcía", "name_control_char"),
        ("Ana García", "name_control_char"),
    ],
)
def test_invalid_names_are_rejected(name: str, code: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        validate_name(name)
    assert excinfo.value.code == code


def test_name_is_trimmed() -> None:
    assert normalize_name("  Ana García  ") == "Ana García"


def test_minimum_age_is_eighteen_years_and_five_days() -> None:
    assert minimum_age_date(date(2000, 6, 10)) == date(2018, 6, 15)


def test_leap_day_birth_turns_eighteen_on_feb_28() -> None:
    assert minimum_age_date(date(2008, 2, 29)) == date(2026, 3, 5)


def test_birthdate_on_minimum_age_day_is_accepted() -> None:
    validate_birthdate(date(2008, 2, 29), today=date(2026, 3, 5))


def test_birthdate_one_day_before_minimum_age_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        validate_birthdate(date(2008, 2, 29), today=date(2026, 3, 4))
    assert excinfo.value.code == "birthdate_under_minimum_age"


def test_future_birthdate_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        validate_birthdate(date(2030, 1, 1), today=date(2026, 9, 29))
    assert excinfo.value.code == "birthdate_in_future"


def test_country_is_uppercased() -> None:
    assert normalize_country(" es ") == "ES"


def test_existing_iso_country_is_accepted() -> None:
    validate_country("ES")


@pytest.mark.parametrize("country", ["XX", "XK", PLACEHOLDER_COUNTRY])
def test_non_iso_countries_are_rejected(country: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        validate_country(country)
    assert excinfo.value.code == "country_invalid"


def test_placeholder_country_is_kept_while_unchanged() -> None:
    validate_country(PLACEHOLDER_COUNTRY, stored_value=PLACEHOLDER_COUNTRY)
