import hashlib
import hmac
import re
from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.accounts import codes

PUBLIC_ID = "abc_DEF-123"
REG = codes.Purpose.REGISTRATION
RESET = codes.Purpose.PASSWORD_RESET


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
def test_fingerprint_is_hmac_of_purpose_public_id_and_code() -> None:
    message = f"registration:{PUBLIC_ID}:123456".encode()
    expected = hmac.new(b"secret-a", message, hashlib.sha256).hexdigest()

    fingerprint = codes.code_fingerprint(REG, PUBLIC_ID, "123456")

    assert fingerprint == expected
    assert "123456" not in fingerprint


def test_fingerprint_changes_with_secret_public_id_and_code() -> None:
    with override_settings(REGISTRATION_CODE_SECRET="secret-a"):
        base = codes.code_fingerprint(REG, PUBLIC_ID, "123456")
        other_public_id = codes.code_fingerprint(REG, "other-id", "123456")
        other_code = codes.code_fingerprint(REG, PUBLIC_ID, "654321")
    with override_settings(REGISTRATION_CODE_SECRET="secret-b"):
        other_secret = codes.code_fingerprint(REG, PUBLIC_ID, "123456")

    assert len({base, other_public_id, other_code, other_secret}) == 4


def test_verify_accepts_only_the_right_code_for_the_right_process() -> None:
    fingerprint = codes.code_fingerprint(REG, PUBLIC_ID, "123456")

    assert codes.verify_code(REG, PUBLIC_ID, "123456", fingerprint)
    assert not codes.verify_code(REG, PUBLIC_ID, "123457", fingerprint)
    assert not codes.verify_code(REG, "other-id", "123456", fingerprint)
    assert not codes.verify_code(REG, PUBLIC_ID, "123456", "0" * 64)


def test_purposes_have_stable_names() -> None:
    assert [purpose.value for purpose in codes.Purpose] == ["registration", "password_reset"]


@override_settings(REGISTRATION_CODE_SECRET="secret-a")
def test_password_reset_fingerprint_is_hmac_with_its_own_purpose() -> None:
    message = f"password_reset:{PUBLIC_ID}:123456".encode()
    expected = hmac.new(b"secret-a", message, hashlib.sha256).hexdigest()

    assert codes.code_fingerprint(RESET, PUBLIC_ID, "123456") == expected


def test_fingerprint_of_one_purpose_never_verifies_for_the_other() -> None:
    registration = codes.code_fingerprint(REG, PUBLIC_ID, "123456")
    reset = codes.code_fingerprint(RESET, PUBLIC_ID, "123456")

    assert registration != reset
    assert codes.verify_code(RESET, PUBLIC_ID, "123456", reset)
    assert not codes.verify_code(RESET, PUBLIC_ID, "123456", registration)
    assert not codes.verify_code(REG, PUBLIC_ID, "123456", reset)


def test_previous_secret_keeps_purposes_apart() -> None:
    with override_settings(REGISTRATION_CODE_SECRET="old-secret"):
        reset = codes.code_fingerprint(RESET, PUBLIC_ID, "123456")
    with _rotation(30):
        assert codes.verify_code(RESET, PUBLIC_ID, "123456", reset)
        assert not codes.verify_code(REG, PUBLIC_ID, "123456", reset)


def test_verify_compares_in_constant_time(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    real_compare = hmac.compare_digest

    def spy(a: str, b: str) -> bool:
        calls.append((a, b))
        return real_compare(a, b)

    monkeypatch.setattr("apps.accounts.codes.hmac.compare_digest", spy)
    codes.verify_code(REG, PUBLIC_ID, "123456", codes.code_fingerprint(REG, PUBLIC_ID, "123456"))

    assert len(calls) == 1


def _old_fingerprint() -> str:
    with override_settings(REGISTRATION_CODE_SECRET="old-secret"):
        return codes.code_fingerprint(REG, PUBLIC_ID, "123456")


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
        assert codes.verify_code(REG, PUBLIC_ID, "123456", fingerprint)
        assert not codes.verify_code(REG, PUBLIC_ID, "654321", fingerprint)


def test_previous_secret_is_rejected_after_transition() -> None:
    fingerprint = _old_fingerprint()
    with _rotation(61):
        assert not codes.verify_code(REG, PUBLIC_ID, "123456", fingerprint)


def test_transition_length_follows_settings() -> None:
    fingerprint = _old_fingerprint()
    with _rotation(30, REGISTRATION_SECRET_TRANSITION_MINUTES=20):
        assert not codes.verify_code(REG, PUBLIC_ID, "123456", fingerprint)
    with _rotation(90, REGISTRATION_SECRET_TRANSITION_MINUTES=120):
        assert codes.verify_code(REG, PUBLIC_ID, "123456", fingerprint)


def test_previous_secret_is_rejected_without_full_configuration() -> None:
    fingerprint = _old_fingerprint()
    with _rotation(30, previous=""):
        assert not codes.verify_code(REG, PUBLIC_ID, "123456", fingerprint)
    with _rotation(None):
        assert not codes.verify_code(REG, PUBLIC_ID, "123456", fingerprint)


def test_new_fingerprints_use_the_current_secret_during_transition() -> None:
    with _rotation(30):
        fingerprint = codes.code_fingerprint(REG, PUBLIC_ID, "123456")
    with override_settings(REGISTRATION_CODE_SECRET="new-secret"):
        assert codes.verify_code(REG, PUBLIC_ID, "123456", fingerprint)


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


PASSWORD_HASH = "pbkdf2_sha256$870000$salt$hash="


@override_settings(REGISTRATION_CODE_SECRET="secret-a")
def test_account_stamp_is_hmac_of_lowercase_email_and_password_hash() -> None:
    message = f"password_reset_account:ana@x.com:{PASSWORD_HASH}".encode()
    expected = hmac.new(b"secret-a", message, hashlib.sha256).hexdigest()

    stamp = codes.account_stamp("Ana@X.com", PASSWORD_HASH)

    assert stamp == expected
    assert re.fullmatch(r"[0-9a-f]{64}", stamp)
    assert "ana" not in stamp


def test_account_stamp_changes_with_email_and_password_hash() -> None:
    base = codes.account_stamp("ana@x.com", PASSWORD_HASH)

    assert codes.account_stamp("ANA@x.com", PASSWORD_HASH) == base
    assert codes.account_stamp("ana@y.com", PASSWORD_HASH) != base
    assert codes.account_stamp("ana@x.com", PASSWORD_HASH + "x") != base


def test_account_stamp_matches_only_the_same_email_and_password_hash() -> None:
    stamp = codes.account_stamp("ana@x.com", PASSWORD_HASH)

    assert codes.account_stamp_matches(stamp, "Ana@X.com", PASSWORD_HASH)
    assert not codes.account_stamp_matches(stamp, "ana@y.com", PASSWORD_HASH)
    assert not codes.account_stamp_matches(stamp, "ana@x.com", "other-hash")


def test_account_stamp_with_previous_secret_matches_only_during_transition() -> None:
    with override_settings(REGISTRATION_CODE_SECRET="old-secret"):
        stamp = codes.account_stamp("ana@x.com", PASSWORD_HASH)
    with _rotation(30):
        assert codes.account_stamp_matches(stamp, "ana@x.com", PASSWORD_HASH)
        assert not codes.account_stamp_matches(stamp, "ana@y.com", PASSWORD_HASH)
    with _rotation(61):
        assert not codes.account_stamp_matches(stamp, "ana@x.com", PASSWORD_HASH)


def test_account_stamp_is_not_a_code_fingerprint() -> None:
    stamp = codes.account_stamp("ana@x.com", "123456")

    assert not codes.verify_code(RESET, "account", "ana@x.com:123456", stamp)
