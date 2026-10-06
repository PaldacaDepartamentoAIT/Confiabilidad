from datetime import date

import pytest
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.accounts.models import User


def _user(email: str = "x@example.com", name: str = "Bea Ruiz") -> User:
    return User(email=email, name=name, birthdate=date(1990, 5, 10), country="ES")


def _rejection_codes(password: str, user: User) -> set[str | None]:
    with pytest.raises(ValidationError) as excinfo:
        validate_password(password, user=user)
    return {error.code for error in excinfo.value.error_list}


def test_good_password_of_twelve_characters_is_accepted() -> None:
    validate_password("Kq7#mZ2!vR9p", user=_user())


def test_eleven_characters_are_rejected() -> None:
    assert "password_too_short" in _rejection_codes("Kq7#mZ2!vR9", _user())


def test_password_similar_to_the_email_is_rejected() -> None:
    user = _user(email="ana.garcia@example.com")
    assert "password_too_similar" in _rejection_codes("ana.garcia@example", user)


def test_password_similar_to_the_name_is_rejected() -> None:
    user = _user(name="Ana García")
    assert "password_too_similar" in _rejection_codes("anagarcía1990", user)


def test_common_password_is_rejected() -> None:
    assert "password_too_common" in _rejection_codes("qwerty123456", _user())
