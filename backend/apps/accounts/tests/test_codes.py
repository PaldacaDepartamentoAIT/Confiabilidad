import re

import pytest

from apps.accounts import codes


def test_code_has_six_digits() -> None:
    for _ in range(200):
        assert re.fullmatch(r"\d{6}", codes.generate_code())


def test_code_keeps_leading_zeros(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("apps.accounts.codes.secrets.randbelow", lambda _: 42)

    assert codes.generate_code() == "000042"


def test_public_id_is_random_and_url_safe() -> None:
    first, second = codes.generate_public_id(), codes.generate_public_id()

    assert re.fullmatch(r"[A-Za-z0-9_-]{43,64}", first)
    assert first != second


def test_purposes_have_stable_names() -> None:
    assert [purpose.value for purpose in codes.Purpose] == ["registration", "password_reset"]


def test_public_id_never_starts_with_a_dash(monkeypatch: pytest.MonkeyPatch) -> None:
    values = iter(["-starts-with-dash", "clean-id"])
    monkeypatch.setattr("apps.accounts.codes.secrets.token_urlsafe", lambda _: next(values))

    assert codes.generate_public_id() == "clean-id"


def test_code_is_drawn_from_the_full_six_digit_range(monkeypatch: pytest.MonkeyPatch) -> None:
    upper_bounds: list[int] = []

    def fake_randbelow(upper: int) -> int:
        upper_bounds.append(upper)
        return upper - 1

    monkeypatch.setattr("apps.accounts.codes.secrets.randbelow", fake_randbelow)

    assert codes.generate_code() == "999999"
    assert upper_bounds == [10**6]
