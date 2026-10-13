import hashlib
import hmac
import re
from datetime import timedelta

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.utils import timezone
from pytest_django import DjangoAssertNumQueries

from apps.core import fingerprints

PUBLIC_ID = "abc_DEF-123"
REG = "registration"
RESET = "password_reset"

# Huellas generadas con el código anterior a esta feature: si cambia un byte del mensaje, fallan
# (RF-005, D-06).
CODE_VECTORS = {
    REG: "9461c626be1dc42a216920a66d6d9c2282a8fef8c926bdbca63be3199bd95b1b",
    RESET: "f5a97a5b4d7b89dd07b3bd5b6e6a48cf2e9467ce7e94baadece53f9f5174a701",
}


@pytest.mark.parametrize("purpose", [REG, RESET])
@override_settings(REGISTRATION_CODE_SECRET="vector-code-key")
def test_code_fingerprint_matches_the_stored_vector(purpose: str) -> None:
    assert fingerprints.code_fingerprint(purpose, PUBLIC_ID, "012345") == CODE_VECTORS[purpose]


@override_settings(REGISTRATION_CODE_SECRET="secret-a")
def test_code_fingerprint_is_hmac_of_purpose_public_id_and_code() -> None:
    message = f"registration:{PUBLIC_ID}:123456".encode()
    expected = hmac.new(b"secret-a", message, hashlib.sha256).hexdigest()

    fingerprint = fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")

    assert fingerprint == expected
    assert re.fullmatch(r"[0-9a-f]{64}", fingerprint)


def test_code_fingerprint_changes_with_key_purpose_public_id_and_code() -> None:
    with override_settings(REGISTRATION_CODE_SECRET="secret-a"):
        base = fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
        other_purpose = fingerprints.code_fingerprint(RESET, PUBLIC_ID, "123456")
        other_public_id = fingerprints.code_fingerprint(REG, "other-id", "123456")
        other_code = fingerprints.code_fingerprint(REG, PUBLIC_ID, "654321")
    with override_settings(REGISTRATION_CODE_SECRET="secret-b"):
        other_key = fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")

    assert len({base, other_purpose, other_public_id, other_code, other_key}) == 5


def test_code_matches_only_the_same_purpose_public_id_and_code() -> None:
    fingerprint = fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")

    assert fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)
    assert not fingerprints.code_matches(REG, PUBLIC_ID, "123457", fingerprint)
    assert not fingerprints.code_matches(REG, "other-id", "123456", fingerprint)
    assert not fingerprints.code_matches(RESET, PUBLIC_ID, "123456", fingerprint)
    assert not fingerprints.code_matches(REG, PUBLIC_ID, "123456", "0" * 64)


def _compare_spy(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []
    real_compare = hmac.compare_digest

    def spy(a: str, b: str) -> bool:
        calls.append((a, b))
        return real_compare(a, b)

    monkeypatch.setattr("apps.core.fingerprints.hmac.compare_digest", spy)
    return calls


def test_code_matches_compares_in_constant_time(monkeypatch: pytest.MonkeyPatch) -> None:
    fingerprint = fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
    calls = _compare_spy(monkeypatch)

    assert fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)
    assert calls == [(fingerprint, fingerprint)]


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


def _old_code_fingerprint(purpose: str = REG) -> str:
    with override_settings(REGISTRATION_CODE_SECRET="old-secret"):
        return fingerprints.code_fingerprint(purpose, PUBLIC_ID, "123456")


def test_previous_code_key_is_accepted_during_transition() -> None:
    fingerprint = _old_code_fingerprint()
    with _rotation(30):
        assert fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)
        assert not fingerprints.code_matches(REG, PUBLIC_ID, "654321", fingerprint)


def test_previous_code_key_keeps_purposes_apart() -> None:
    fingerprint = _old_code_fingerprint(RESET)
    with _rotation(30):
        assert fingerprints.code_matches(RESET, PUBLIC_ID, "123456", fingerprint)
        assert not fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)


def test_previous_code_key_is_rejected_after_transition() -> None:
    fingerprint = _old_code_fingerprint()
    with _rotation(61):
        assert not fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)


def test_transition_length_follows_settings() -> None:
    fingerprint = _old_code_fingerprint()
    with _rotation(30, REGISTRATION_SECRET_TRANSITION_MINUTES=20):
        assert not fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)
    with _rotation(90, REGISTRATION_SECRET_TRANSITION_MINUTES=120):
        assert fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)


def test_previous_code_key_without_rotation_date_is_ignored() -> None:
    fingerprint = _old_code_fingerprint()
    with _rotation(None):
        assert not fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)
    with _rotation(30, previous=""):
        assert not fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)


def test_empty_previous_code_key_is_never_used_as_a_key() -> None:
    message = f"registration:{PUBLIC_ID}:123456".encode()
    signed_with_empty_key = hmac.new(b"", message, hashlib.sha256).hexdigest()
    with _rotation(30, previous=""):
        assert not fingerprints.code_matches(REG, PUBLIC_ID, "123456", signed_with_empty_key)


def test_new_code_fingerprints_use_the_current_key_during_transition() -> None:
    with _rotation(30):
        fingerprint = fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
    with override_settings(REGISTRATION_CODE_SECRET="new-secret"):
        assert fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)


@pytest.mark.parametrize("key", ["", "   "])
def test_empty_code_key_is_rejected_when_computing_and_matching(key: str) -> None:
    with override_settings(REGISTRATION_CODE_SECRET=key):
        with pytest.raises(ImproperlyConfigured, match="REGISTRATION_CODE_SECRET"):
            fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
        with pytest.raises(ImproperlyConfigured, match="REGISTRATION_CODE_SECRET"):
            fingerprints.code_matches(REG, PUBLIC_ID, "123456", "0" * 64)


@override_settings(REGISTRATION_CODE_SECRET="same", REGISTRATION_CODE_SECRET_PREVIOUS="same")
def test_previous_code_key_equal_to_current_is_rejected() -> None:
    with pytest.raises(ImproperlyConfigured, match="REGISTRATION_CODE_SECRET_PREVIOUS"):
        fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
    with pytest.raises(ImproperlyConfigured, match="REGISTRATION_CODE_SECRET_PREVIOUS"):
        fingerprints.code_matches(REG, PUBLIC_ID, "123456", "0" * 64)


@pytest.mark.parametrize("previous", ["old-secret", ""])
@pytest.mark.parametrize("raw", ["not-a-date", "2026-10-06T10:00:00"])
def test_rotation_date_without_timezone_is_rejected_only_when_matching(
    raw: str, previous: str
) -> None:
    with override_settings(
        REGISTRATION_CODE_SECRET="new-secret",
        REGISTRATION_CODE_SECRET_PREVIOUS=previous,
        REGISTRATION_CODE_SECRET_ROTATED_AT=raw,
    ):
        fingerprint = fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
        for code in ("123456", "654321"):
            with pytest.raises(ImproperlyConfigured, match="REGISTRATION_CODE_SECRET_ROTATED_AT"):
                fingerprints.code_matches(REG, PUBLIC_ID, code, fingerprint)


def test_code_key_defaults_to_secret_key() -> None:
    assert settings.REGISTRATION_CODE_SECRET == settings.SECRET_KEY
    expected = hmac.new(
        settings.SECRET_KEY.encode(), f"registration:{PUBLIC_ID}:123456".encode(), hashlib.sha256
    ).hexdigest()

    assert fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456") == expected


@pytest.mark.django_db
def test_code_fingerprints_never_query_the_database(
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    fingerprint = _old_code_fingerprint()
    with django_assert_num_queries(0), _rotation(30):
        fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
        fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)
