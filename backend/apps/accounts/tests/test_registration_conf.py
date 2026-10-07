import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from apps.accounts import conf


def test_defaults() -> None:
    assert conf.max_failed_attempts() == 5
    assert conf.code_ttl() == timedelta(minutes=15)
    assert conf.grace_period() == timedelta(minutes=15)
    assert conf.max_lifetime() == timedelta(hours=1)
    assert conf.secret_transition() == timedelta(hours=1)
    assert conf.pwned_timeout() == 2.0
    assert conf.code_secret() == settings.SECRET_KEY
    assert conf.previous_code_secret() is None
    assert conf.secret_rotated_at() is None


@override_settings(
    REGISTRATION_MAX_FAILED_ATTEMPTS=3,
    REGISTRATION_CODE_TTL_MINUTES=10,
    REGISTRATION_GRACE_MINUTES=5,
    REGISTRATION_MAX_LIFETIME_MINUTES=30,
    REGISTRATION_SECRET_TRANSITION_MINUTES=20,
    PWNED_PASSWORDS_TIMEOUT_SECONDS=0.5,
    REGISTRATION_CODE_SECRET="new-secret",
    REGISTRATION_CODE_SECRET_PREVIOUS="old-secret",
    REGISTRATION_CODE_SECRET_ROTATED_AT="2026-10-06T10:00:00+00:00",
)
def test_values_follow_settings() -> None:
    assert conf.max_failed_attempts() == 3
    assert conf.code_ttl() == timedelta(minutes=10)
    assert conf.grace_period() == timedelta(minutes=5)
    assert conf.max_lifetime() == timedelta(minutes=30)
    assert conf.secret_transition() == timedelta(minutes=20)
    assert conf.pwned_timeout() == 0.5
    assert conf.code_secret() == "new-secret"
    assert conf.previous_code_secret() == "old-secret"
    assert conf.secret_rotated_at() == datetime(2026, 10, 6, 10, 0, tzinfo=UTC)


@pytest.mark.parametrize("raw", ["not-a-date", "2026-10-06T10:00:00"])
def test_rotation_date_without_timezone_is_rejected(raw: str) -> None:
    with override_settings(REGISTRATION_CODE_SECRET_ROTATED_AT=raw):
        with pytest.raises(ImproperlyConfigured):
            conf.secret_rotated_at()


@pytest.mark.parametrize("secret", ["", "   "])
def test_empty_code_secret_is_rejected(secret: str) -> None:
    with override_settings(REGISTRATION_CODE_SECRET=secret):
        with pytest.raises(ImproperlyConfigured):
            conf.code_secret()


@override_settings(REGISTRATION_CODE_SECRET="same", REGISTRATION_CODE_SECRET_PREVIOUS="same")
def test_previous_secret_equal_to_current_is_rejected() -> None:
    with pytest.raises(ImproperlyConfigured):
        conf.code_secret()


BACKEND_DIR = Path(__file__).resolve().parents[3]
ENV_LIMITS = {
    "REGISTRATION_MAX_FAILED_ATTEMPTS": "7",
    "REGISTRATION_CODE_TTL_MINUTES": "11",
    "REGISTRATION_GRACE_MINUTES": "12",
    "REGISTRATION_MAX_LIFETIME_MINUTES": "90",
    "REGISTRATION_SECRET_TRANSITION_MINUTES": "45",
    "PWNED_PASSWORDS_TIMEOUT_SECONDS": "0.75",
}
_READ_SETTINGS = (
    "import json, django\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    f"print(json.dumps({{name: getattr(settings, name) for name in {sorted(ENV_LIMITS)!r}}}))\n"
)


def test_limits_are_read_from_environment_variables() -> None:
    env = {**os.environ, **ENV_LIMITS, "DJANGO_SETTINGS_MODULE": "config.settings"}

    result = subprocess.run(
        [sys.executable, "-c", _READ_SETTINGS],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )

    assert json.loads(result.stdout.splitlines()[-1]) == {
        "PWNED_PASSWORDS_TIMEOUT_SECONDS": 0.75,
        "REGISTRATION_CODE_TTL_MINUTES": 11,
        "REGISTRATION_GRACE_MINUTES": 12,
        "REGISTRATION_MAX_FAILED_ATTEMPTS": 7,
        "REGISTRATION_MAX_LIFETIME_MINUTES": 90,
        "REGISTRATION_SECRET_TRANSITION_MINUTES": 45,
    }
