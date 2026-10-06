import hashlib
import hmac
import re

import pytest
from django.test import override_settings

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
