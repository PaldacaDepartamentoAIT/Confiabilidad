import hashlib
import hmac
import re
from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.accounts import codes

PUBLIC_ID = "abc_DEF-123"


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


@override_settings(REGISTRATION_CODE_SECRET="secret-a")
def test_fingerprint_is_hmac_of_public_id_and_code() -> None:
    expected = hmac.new(b"secret-a", f"{PUBLIC_ID}:123456".encode(), hashlib.sha256).hexdigest()

    fingerprint = codes.code_fingerprint(PUBLIC_ID, "123456")

    assert fingerprint == expected
    assert "123456" not in fingerprint


def test_fingerprint_changes_with_secret_public_id_and_code() -> None:
    with override_settings(REGISTRATION_CODE_SECRET="secret-a"):
        base = codes.code_fingerprint(PUBLIC_ID, "123456")
        other_public_id = codes.code_fingerprint("other-id", "123456")
        other_code = codes.code_fingerprint(PUBLIC_ID, "654321")
    with override_settings(REGISTRATION_CODE_SECRET="secret-b"):
        other_secret = codes.code_fingerprint(PUBLIC_ID, "123456")

    assert len({base, other_public_id, other_code, other_secret}) == 4


def test_verify_accepts_only_the_right_code_for_the_right_process() -> None:
    fingerprint = codes.code_fingerprint(PUBLIC_ID, "123456")

    assert codes.verify_code(PUBLIC_ID, "123456", fingerprint)
    assert not codes.verify_code(PUBLIC_ID, "123457", fingerprint)
    assert not codes.verify_code("other-id", "123456", fingerprint)
    assert not codes.verify_code(PUBLIC_ID, "123456", "0" * 64)


def test_verify_compares_in_constant_time(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    real_compare = hmac.compare_digest

    def spy(a: str, b: str) -> bool:
        calls.append((a, b))
        return real_compare(a, b)

    monkeypatch.setattr("apps.accounts.codes.hmac.compare_digest", spy)
    codes.verify_code(PUBLIC_ID, "123456", codes.code_fingerprint(PUBLIC_ID, "123456"))

    assert len(calls) == 1


def _old_fingerprint() -> str:
    with override_settings(REGISTRATION_CODE_SECRET="old-secret"):
        return codes.code_fingerprint(PUBLIC_ID, "123456")


def _rotation(
    minutes_ago: int | None, previous: str = "old-secret", **extra: object
) -> override_settings:
    rotated_at = (
        "" if minutes_ago is None else (timezone.now() - timedelta(minutes=minutes_ago)).isoformat()
    )
    return override_settings(
        REGISTRATION_CODE_SECRET="new-secret",
        REGISTRATION_CODE_SECRET_PREVIOUS=previous,
        REGISTRATION_CODE_SECRET_ROTATED_AT=rotated_at,
        **extra,
    )


def test_previous_secret_is_accepted_during_transition() -> None:
    fingerprint = _old_fingerprint()
    with _rotation(30):
        assert codes.verify_code(PUBLIC_ID, "123456", fingerprint)
        assert not codes.verify_code(PUBLIC_ID, "654321", fingerprint)


def test_previous_secret_is_rejected_after_transition() -> None:
    fingerprint = _old_fingerprint()
    with _rotation(61):
        assert not codes.verify_code(PUBLIC_ID, "123456", fingerprint)


def test_transition_length_follows_settings() -> None:
    fingerprint = _old_fingerprint()
    with _rotation(30, REGISTRATION_SECRET_TRANSITION_MINUTES=20):
        assert not codes.verify_code(PUBLIC_ID, "123456", fingerprint)
    with _rotation(90, REGISTRATION_SECRET_TRANSITION_MINUTES=120):
        assert codes.verify_code(PUBLIC_ID, "123456", fingerprint)


def test_previous_secret_is_rejected_without_full_configuration() -> None:
    fingerprint = _old_fingerprint()
    with _rotation(30, previous=""):
        assert not codes.verify_code(PUBLIC_ID, "123456", fingerprint)
    with _rotation(None):
        assert not codes.verify_code(PUBLIC_ID, "123456", fingerprint)


def test_new_fingerprints_use_the_current_secret_during_transition() -> None:
    with _rotation(30):
        fingerprint = codes.code_fingerprint(PUBLIC_ID, "123456")
    with override_settings(REGISTRATION_CODE_SECRET="new-secret"):
        assert codes.verify_code(PUBLIC_ID, "123456", fingerprint)


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
