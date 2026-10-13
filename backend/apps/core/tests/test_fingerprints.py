import hashlib
import hmac
import os
import re
import subprocess
import sys
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

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
        with pytest.raises(ImproperlyConfigured, match=r"\bREGISTRATION_CODE_SECRET\b"):
            fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
        with pytest.raises(ImproperlyConfigured, match=r"\bREGISTRATION_CODE_SECRET\b"):
            fingerprints.code_matches(REG, PUBLIC_ID, "123456", "0" * 64)


@override_settings(REGISTRATION_CODE_SECRET="same", REGISTRATION_CODE_SECRET_PREVIOUS="same")
def test_previous_code_key_equal_to_current_is_rejected() -> None:
    with pytest.raises(ImproperlyConfigured, match="REGISTRATION_CODE_SECRET_PREVIOUS"):
        fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
    with pytest.raises(ImproperlyConfigured, match="REGISTRATION_CODE_SECRET_PREVIOUS"):
        fingerprints.code_matches(REG, PUBLIC_ID, "123456", "0" * 64)


@pytest.mark.parametrize("previous", ["old-secret", ""])
@pytest.mark.parametrize(
    "raw",
    ["not-a-date", "2026-10-06T10:00:00", "2026-13-01T10:00:00+00:00", "2026-02-30T10:00:00+00:00"],
)
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


PASSWORD_HASH = "pbkdf2_sha256$870000$salt$hash="
STAMP_VECTOR = "27e2bc21dc9aeb0e3ef4d84e062e17c2e624212c6af3bca268a20dd116913145"


@override_settings(REGISTRATION_CODE_SECRET="vector-code-key")
def test_account_stamp_matches_the_stored_vector() -> None:
    assert fingerprints.account_stamp("ana@x.com", PASSWORD_HASH) == STAMP_VECTOR


@override_settings(REGISTRATION_CODE_SECRET="secret-a")
def test_account_stamp_is_hmac_of_normalized_email_and_password_hash() -> None:
    message = f"password_reset_account:ana@x.com:{PASSWORD_HASH}".encode()
    expected = hmac.new(b"secret-a", message, hashlib.sha256).hexdigest()

    stamp = fingerprints.account_stamp(" Ana@X.com ", PASSWORD_HASH)

    assert stamp == expected
    assert re.fullmatch(r"[0-9a-f]{64}", stamp)


def test_account_stamp_changes_with_email_and_password_hash() -> None:
    base = fingerprints.account_stamp("ana@x.com", PASSWORD_HASH)

    assert fingerprints.account_stamp(" ANA@x.com\t", PASSWORD_HASH) == base
    assert fingerprints.account_stamp("ana@y.com", PASSWORD_HASH) != base
    assert fingerprints.account_stamp("ana@x.com", PASSWORD_HASH + "x") != base


def test_account_stamp_matches_only_the_same_email_and_password_hash() -> None:
    stamp = fingerprints.account_stamp("ana@x.com", PASSWORD_HASH)

    assert fingerprints.account_stamp_matches(stamp, " Ana@X.com ", PASSWORD_HASH)
    assert not fingerprints.account_stamp_matches(stamp, "ana@y.com", PASSWORD_HASH)
    assert not fingerprints.account_stamp_matches(stamp, "ana@x.com", "other-hash")


def test_account_stamp_matches_compares_in_constant_time(monkeypatch: pytest.MonkeyPatch) -> None:
    stamp = fingerprints.account_stamp("ana@x.com", PASSWORD_HASH)
    calls = _compare_spy(monkeypatch)

    assert fingerprints.account_stamp_matches(stamp, "ana@x.com", PASSWORD_HASH)
    assert calls == [(stamp, stamp)]


def test_account_stamp_with_previous_key_matches_only_during_transition() -> None:
    with override_settings(REGISTRATION_CODE_SECRET="old-secret"):
        stamp = fingerprints.account_stamp("ana@x.com", PASSWORD_HASH)
    with _rotation(30):
        assert fingerprints.account_stamp_matches(stamp, "ana@x.com", PASSWORD_HASH)
        assert not fingerprints.account_stamp_matches(stamp, "ana@y.com", PASSWORD_HASH)
    with _rotation(61):
        assert not fingerprints.account_stamp_matches(stamp, "ana@x.com", PASSWORD_HASH)


def test_account_stamp_is_not_a_code_fingerprint() -> None:
    stamp = fingerprints.account_stamp("ana@x.com", "123456")

    assert not fingerprints.code_matches(RESET, "account", "ana@x.com:123456", stamp)


CONSENT_VECTOR = "b0b244fb77dfac662c5db03baa83cb0190d37c4ca9e63c549a6755b31dccdedf"


@override_settings(CONSENT_EMAIL_HASH_SECRET="vector-consent-key")
def test_consent_email_fingerprint_matches_the_stored_vector() -> None:
    assert fingerprints.consent_email_fingerprint("ana@x.com") == CONSENT_VECTOR


@override_settings(CONSENT_EMAIL_HASH_SECRET="secret")
def test_consent_email_fingerprint_is_hmac_of_the_normalized_email() -> None:
    expected = hmac.new(b"secret", b"ana@x.com", hashlib.sha256).hexdigest()

    fingerprint = fingerprints.consent_email_fingerprint(" Ana@X.com ")

    assert fingerprint == expected
    assert re.fullmatch(r"[0-9a-f]{64}", fingerprint)


def test_consent_email_fingerprint_changes_with_email_and_key() -> None:
    with override_settings(CONSENT_EMAIL_HASH_SECRET="one"):
        base = fingerprints.consent_email_fingerprint("ana@x.com")
        other_email = fingerprints.consent_email_fingerprint("ana@y.com")
    with override_settings(CONSENT_EMAIL_HASH_SECRET="two"):
        other_key = fingerprints.consent_email_fingerprint("ana@x.com")

    assert len({base, other_email, other_key}) == 3


def test_consent_email_matches_only_the_same_normalized_email() -> None:
    fingerprint = fingerprints.consent_email_fingerprint("ana@x.com")

    assert fingerprints.consent_email_matches(" ANA@x.com ", fingerprint)
    assert not fingerprints.consent_email_matches("ana@y.com", fingerprint)


def test_consent_email_matches_compares_in_constant_time(monkeypatch: pytest.MonkeyPatch) -> None:
    fingerprint = fingerprints.consent_email_fingerprint("ana@x.com")
    calls = _compare_spy(monkeypatch)

    assert fingerprints.consent_email_matches("ana@x.com", fingerprint)
    assert calls == [(fingerprint, fingerprint)]


def test_consent_email_never_uses_a_previous_key() -> None:
    with override_settings(CONSENT_EMAIL_HASH_SECRET="old-secret"):
        fingerprint = fingerprints.consent_email_fingerprint("ana@x.com")
    with _rotation(30, CONSENT_EMAIL_HASH_SECRET="new-consent-secret"):
        assert not fingerprints.consent_email_matches("ana@x.com", fingerprint)


def test_consent_email_ignores_the_code_key_configuration() -> None:
    with override_settings(
        REGISTRATION_CODE_SECRET="", REGISTRATION_CODE_SECRET_ROTATED_AT="not-a-date"
    ):
        fingerprint = fingerprints.consent_email_fingerprint("ana@x.com")
        assert fingerprints.consent_email_matches("ana@x.com", fingerprint)


@pytest.mark.parametrize("key", ["", "   "])
def test_empty_consent_key_is_rejected_when_computing_and_matching(key: str) -> None:
    with override_settings(CONSENT_EMAIL_HASH_SECRET=key):
        with pytest.raises(ImproperlyConfigured, match="CONSENT_EMAIL_HASH_SECRET"):
            fingerprints.consent_email_fingerprint("ana@x.com")
        with pytest.raises(ImproperlyConfigured, match="CONSENT_EMAIL_HASH_SECRET"):
            fingerprints.consent_email_matches("ana@x.com", "0" * 64)


def test_consent_key_defaults_to_secret_key() -> None:
    assert settings.CONSENT_EMAIL_HASH_SECRET == settings.SECRET_KEY
    expected = hmac.new(settings.SECRET_KEY.encode(), b"ana@x.com", hashlib.sha256).hexdigest()

    assert fingerprints.consent_email_fingerprint("ana@x.com") == expected


BACKEND_DIR = Path(__file__).resolve().parents[3]
_PRINT_CONSENT_KEY = (
    "import django\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    "print(settings.CONSENT_EMAIL_HASH_SECRET)\n"
)


def _consent_key_from_environment(**variables: str) -> str:
    env = {key: value for key, value in os.environ.items() if key != "CONSENT_EMAIL_HASH_SECRET"}
    env.update(variables, DJANGO_SETTINGS_MODULE="config.settings")
    result = subprocess.run(
        [sys.executable, "-c", _PRINT_CONSENT_KEY],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return result.stdout.splitlines()[-1]


def test_consent_key_is_read_from_environment_variable() -> None:
    assert _consent_key_from_environment(CONSENT_EMAIL_HASH_SECRET="from-env") == "from-env"


def test_consent_key_without_environment_variable_is_secret_key() -> None:
    assert _consent_key_from_environment(DJANGO_SECRET_KEY="the-key") == "the-key"


@pytest.mark.django_db
def test_consent_email_fingerprints_never_query_the_database(
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    with django_assert_num_queries(0):
        fingerprint = fingerprints.consent_email_fingerprint("ana@x.com")
        fingerprints.consent_email_matches("ana@x.com", fingerprint)


_PRINT_CODE_KEY = (
    "import django\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    "print(settings.REGISTRATION_CODE_SECRET)\n"
)


def _code_key_from_environment(**variables: str) -> str:
    env = {key: value for key, value in os.environ.items() if key != "REGISTRATION_CODE_SECRET"}
    env.update(variables, DJANGO_SETTINGS_MODULE="config.settings")
    result = subprocess.run(
        [sys.executable, "-c", _PRINT_CODE_KEY],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return result.stdout.splitlines()[-1]


def test_code_key_is_read_from_environment_variable() -> None:
    assert _code_key_from_environment(REGISTRATION_CODE_SECRET="from-env") == "from-env"


def test_code_key_without_environment_variable_is_secret_key() -> None:
    assert _code_key_from_environment(DJANGO_SECRET_KEY="the-key") == "the-key"


@pytest.mark.django_db
def test_account_stamps_never_query_the_database(
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    with override_settings(REGISTRATION_CODE_SECRET="old-secret"):
        old_stamp = fingerprints.account_stamp("ana@x.com", PASSWORD_HASH)
    with django_assert_num_queries(0), _rotation(30):
        fingerprints.account_stamp("ana@x.com", PASSWORD_HASH)
        fingerprints.account_stamp_matches(old_stamp, "ana@x.com", PASSWORD_HASH)


@pytest.mark.parametrize("minutes_ago", [30, None])
def test_blank_previous_code_key_is_rejected_when_computing_and_matching(
    minutes_ago: int | None,
) -> None:
    with _rotation(minutes_ago, previous="   "):
        for compute in (
            lambda: fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456"),
            lambda: fingerprints.code_matches(REG, PUBLIC_ID, "123456", "0" * 64),
            lambda: fingerprints.account_stamp("ana@x.com", PASSWORD_HASH),
            lambda: fingerprints.account_stamp_matches("0" * 64, "ana@x.com", PASSWORD_HASH),
        ):
            with pytest.raises(ImproperlyConfigured, match="REGISTRATION_CODE_SECRET_PREVIOUS"):
                compute()


@pytest.mark.parametrize("minutes_ago", [30, None])
def test_empty_previous_code_key_is_ignored_without_error(minutes_ago: int | None) -> None:
    with _rotation(minutes_ago, previous=""):
        fingerprint = fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
        assert fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint)


@pytest.mark.parametrize("previous", ["old-secret", ""])
def test_future_rotation_date_is_rejected_when_matching(previous: str) -> None:
    with override_settings(REGISTRATION_CODE_SECRET="new-secret"):
        fingerprint = fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456")
        stamp = fingerprints.account_stamp("ana@x.com", PASSWORD_HASH)
    with _rotation(-1, previous=previous):
        assert fingerprints.code_fingerprint(REG, PUBLIC_ID, "123456") == fingerprint
        assert fingerprints.account_stamp("ana@x.com", PASSWORD_HASH) == stamp
        checks: list[Callable[[], bool]] = [
            lambda: fingerprints.code_matches(REG, PUBLIC_ID, "123456", fingerprint),
            lambda: fingerprints.code_matches(REG, PUBLIC_ID, "654321", fingerprint),
            lambda: fingerprints.account_stamp_matches(stamp, "ana@x.com", PASSWORD_HASH),
        ]
        for check in checks:
            with pytest.raises(
                ImproperlyConfigured, match=r"\bREGISTRATION_CODE_SECRET_ROTATED_AT\b"
            ):
                check()
