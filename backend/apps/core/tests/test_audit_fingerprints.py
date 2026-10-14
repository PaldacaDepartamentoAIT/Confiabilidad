import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import Promise

from apps.core.checks import check_audit_hash_secret
from apps.core.fingerprints import audit_email_fingerprint, audit_session_fingerprint

KEY = "test-audit-key"
EMAIL_VECTOR = "ed19def9f3398b37ed7d315cbdfbfb1a54916c8e27c528bb0a1733781149f476"
SESSION_VECTOR = "716ecc4117177bddb121e9d1f53f7e1ab99ba1efdd3ab063773a4d01f57d3264"
BACKEND_DIR = Path(__file__).resolve().parents[3]


@pytest.fixture
def audit_key(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = KEY  # type: ignore[attr-defined]


def test_email_fingerprint_matches_fixed_vector(audit_key: None) -> None:
    assert audit_email_fingerprint("ana@x.com") == EMAIL_VECTOR


def test_email_fingerprint_normalizes_case_and_spaces(audit_key: None) -> None:
    assert audit_email_fingerprint(" Ana@X.com ") == EMAIL_VECTOR


def test_session_fingerprint_matches_fixed_vector(audit_key: None) -> None:
    assert audit_session_fingerprint("sess-123") == SESSION_VECTOR


def test_email_and_session_fingerprints_are_domain_separated(audit_key: None) -> None:
    assert audit_email_fingerprint("sess-123") != audit_session_fingerprint("sess-123")


def test_fingerprint_without_key_raises(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = ""  # type: ignore[attr-defined]
    with pytest.raises(ImproperlyConfigured):
        audit_email_fingerprint("ana@x.com")


def test_check_reports_error_when_key_is_missing(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = ""  # type: ignore[attr-defined]
    errors = check_audit_hash_secret(None)
    assert [error.id for error in errors] == ["audit.E001"]


def test_check_is_silent_when_key_is_set(audit_key: None) -> None:
    assert check_audit_hash_secret(None) == []


def test_check_message_is_marked_for_translation(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = ""  # type: ignore[attr-defined]
    (error,) = check_audit_hash_secret(None)
    assert isinstance(error.msg, Promise)
    assert str(error.msg) == "AUDIT_HASH_SECRET must not be empty."


def _check_without_audit_key(debug: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "DJANGO_DEBUG": debug,
        "AUDIT_HASH_SECRET": "",
    }
    return subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_development_starts_without_audit_key() -> None:
    result = _check_without_audit_key("1")

    assert result.returncode == 0, result.stderr
    assert "audit.E001" not in result.stdout + result.stderr


def test_production_still_requires_audit_key() -> None:
    result = _check_without_audit_key("0")

    assert result.returncode != 0
    assert "audit.E001" in result.stderr
