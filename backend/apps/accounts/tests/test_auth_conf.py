import json
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from apps.accounts import conf

BACKEND_DIR = Path(__file__).resolve().parents[3]
ENV_LIMITS = {
    "LOGIN_MAX_FAILED_ATTEMPTS": "4",
    "LOGIN_LOCKOUT_MINUTES": "10",
    "LOGIN_RATE_IP_PER_MINUTE": "25",
    "SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS": "120",
    "SESSION_LIFETIME_DAYS": "7",
}
_READ_SETTINGS = (
    "import json, django\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    "names = [\n"
    "    'LOGIN_MAX_FAILED_ATTEMPTS',\n"
    "    'LOGIN_LOCKOUT_MINUTES',\n"
    "    'LOGIN_RATE_IP_PER_MINUTE',\n"
    "    'SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS',\n"
    "    'SESSION_LIFETIME_DAYS',\n"
    "    'SESSION_COOKIE_AGE',\n"
    "    'ACCOUNT_RATE_LIMITS',\n"
    "]\n"
    "print(json.dumps({name: getattr(settings, name) for name in names}))\n"
)


def test_defaults() -> None:
    assert conf.login_max_failed_attempts() == 5
    assert conf.login_lockout_window() == timedelta(minutes=5)
    assert conf.login_rate_ip_per_minute() == 30
    assert conf.session_activity_update_interval() == timedelta(seconds=60)
    assert conf.session_lifetime() == timedelta(days=14)
    assert settings.SESSION_COOKIE_AGE == 14 * 86400
    assert settings.ACCOUNT_RATE_LIMITS == {"login_failed": "10/m/ip,5/5m/key"}


@override_settings(
    LOGIN_MAX_FAILED_ATTEMPTS=3,
    LOGIN_LOCKOUT_MINUTES=15,
    LOGIN_RATE_IP_PER_MINUTE=12,
    SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS=30,
    SESSION_LIFETIME_DAYS=21,
)
def test_values_follow_settings() -> None:
    assert conf.login_max_failed_attempts() == 3
    assert conf.login_lockout_window() == timedelta(minutes=15)
    assert conf.login_rate_ip_per_minute() == 12
    assert conf.session_activity_update_interval() == timedelta(seconds=30)
    assert conf.session_lifetime() == timedelta(days=21)


def test_auth_settings_are_read_from_environment_variables() -> None:
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
        "LOGIN_MAX_FAILED_ATTEMPTS": 4,
        "LOGIN_LOCKOUT_MINUTES": 10,
        "LOGIN_RATE_IP_PER_MINUTE": 25,
        "SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS": 120,
        "SESSION_LIFETIME_DAYS": 7,
        "SESSION_COOKIE_AGE": 7 * 86400,
        "ACCOUNT_RATE_LIMITS": {"login_failed": "10/m/ip,4/10m/key"},
    }


@pytest.mark.parametrize(
    ("name", "reader"),
    [
        ("LOGIN_MAX_FAILED_ATTEMPTS", conf.login_max_failed_attempts),
        ("LOGIN_LOCKOUT_MINUTES", conf.login_lockout_window),
        ("LOGIN_RATE_IP_PER_MINUTE", conf.login_rate_ip_per_minute),
        (
            "SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS",
            conf.session_activity_update_interval,
        ),
        ("SESSION_LIFETIME_DAYS", conf.session_lifetime),
    ],
)
@pytest.mark.parametrize("value", [0, -1])
def test_auth_setting_below_one_is_a_configuration_error(
    name: str, reader: Callable[[], object], value: int
) -> None:
    with override_settings(**{name: value}):
        with pytest.raises(ImproperlyConfigured, match=name):
            reader()


@override_settings(
    LOGIN_MAX_FAILED_ATTEMPTS=1,
    LOGIN_LOCKOUT_MINUTES=1,
    LOGIN_RATE_IP_PER_MINUTE=1,
    SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS=1,
    SESSION_LIFETIME_DAYS=1,
)
def test_auth_settings_of_one_are_valid() -> None:
    assert conf.login_max_failed_attempts() == 1
    assert conf.login_lockout_window() == timedelta(minutes=1)
    assert conf.login_rate_ip_per_minute() == 1
    assert conf.session_activity_update_interval() == timedelta(seconds=1)
    assert conf.session_lifetime() == timedelta(days=1)
