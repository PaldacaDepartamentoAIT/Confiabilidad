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


def test_defaults() -> None:
    assert conf.max_failed_attempts() == 5
    assert conf.code_ttl() == timedelta(minutes=15)
    assert conf.grace_period() == timedelta(minutes=15)
    assert conf.max_lifetime() == timedelta(hours=1)
    assert conf.pwned_timeout() == 2.0
    assert settings.REGISTRATION_SECRET_TRANSITION_MINUTES == 60
    assert conf.start_retry_window() == timedelta(minutes=5)
    assert conf.rate_email_ip_interval() == timedelta(seconds=60)
    assert conf.rate_email_ip_per_hour() == 5
    assert conf.rate_ip_per_hour() == 20
    assert conf.resend_interval() == timedelta(seconds=60)
    assert conf.max_resends() == 5
    assert conf.rate_flow_ip_per_hour() == 60
    assert conf.purge_after() == timedelta(hours=24)


@override_settings(
    REGISTRATION_MAX_FAILED_ATTEMPTS=3,
    REGISTRATION_CODE_TTL_MINUTES=10,
    REGISTRATION_GRACE_MINUTES=5,
    REGISTRATION_MAX_LIFETIME_MINUTES=30,
    PWNED_PASSWORDS_TIMEOUT_SECONDS=0.5,
    REGISTRATION_START_RETRY_MINUTES=2,
    REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS=30,
    REGISTRATION_RATE_EMAIL_IP_PER_HOUR=3,
    REGISTRATION_RATE_IP_PER_HOUR=100,
    REGISTRATION_RESEND_INTERVAL_SECONDS=30,
    REGISTRATION_MAX_RESENDS=2,
    REGISTRATION_RATE_FLOW_IP_PER_HOUR=10,
    REGISTRATION_PURGE_AFTER_HOURS=48,
)
def test_values_follow_settings() -> None:
    assert conf.max_failed_attempts() == 3
    assert conf.code_ttl() == timedelta(minutes=10)
    assert conf.grace_period() == timedelta(minutes=5)
    assert conf.max_lifetime() == timedelta(minutes=30)
    assert conf.pwned_timeout() == 0.5
    assert conf.start_retry_window() == timedelta(minutes=2)
    assert conf.rate_email_ip_interval() == timedelta(seconds=30)
    assert conf.rate_email_ip_per_hour() == 3
    assert conf.rate_ip_per_hour() == 100
    assert conf.resend_interval() == timedelta(seconds=30)
    assert conf.max_resends() == 2
    assert conf.rate_flow_ip_per_hour() == 10
    assert conf.purge_after() == timedelta(hours=48)


BACKEND_DIR = Path(__file__).resolve().parents[3]
ENV_LIMITS = {
    "REGISTRATION_MAX_FAILED_ATTEMPTS": "7",
    "REGISTRATION_CODE_TTL_MINUTES": "11",
    "REGISTRATION_GRACE_MINUTES": "12",
    "REGISTRATION_MAX_LIFETIME_MINUTES": "90",
    "REGISTRATION_SECRET_TRANSITION_MINUTES": "45",
    "PWNED_PASSWORDS_TIMEOUT_SECONDS": "0.75",
    "REGISTRATION_START_RETRY_MINUTES": "8",
    "REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS": "90",
    "REGISTRATION_RATE_EMAIL_IP_PER_HOUR": "4",
    "REGISTRATION_RATE_IP_PER_HOUR": "50",
    "REGISTRATION_RESEND_INTERVAL_SECONDS": "45",
    "REGISTRATION_MAX_RESENDS": "3",
    "REGISTRATION_RATE_FLOW_IP_PER_HOUR": "40",
    "REGISTRATION_PURGE_AFTER_HOURS": "36",
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
        "REGISTRATION_START_RETRY_MINUTES": 8,
        "REGISTRATION_CODE_TTL_MINUTES": 11,
        "REGISTRATION_GRACE_MINUTES": 12,
        "REGISTRATION_MAX_FAILED_ATTEMPTS": 7,
        "REGISTRATION_MAX_LIFETIME_MINUTES": 90,
        "REGISTRATION_SECRET_TRANSITION_MINUTES": 45,
        "REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS": 90,
        "REGISTRATION_RATE_EMAIL_IP_PER_HOUR": 4,
        "REGISTRATION_RATE_IP_PER_HOUR": 50,
        "REGISTRATION_RESEND_INTERVAL_SECONDS": 45,
        "REGISTRATION_MAX_RESENDS": 3,
        "REGISTRATION_RATE_FLOW_IP_PER_HOUR": 40,
        "REGISTRATION_PURGE_AFTER_HOURS": 36,
    }


@pytest.mark.parametrize(
    ("name", "reader"),
    [
        ("REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS", conf.rate_email_ip_interval),
        ("REGISTRATION_RATE_EMAIL_IP_PER_HOUR", conf.rate_email_ip_per_hour),
        ("REGISTRATION_RATE_IP_PER_HOUR", conf.rate_ip_per_hour),
        ("REGISTRATION_RESEND_INTERVAL_SECONDS", conf.resend_interval),
        ("REGISTRATION_MAX_RESENDS", conf.max_resends),
        ("REGISTRATION_RATE_FLOW_IP_PER_HOUR", conf.rate_flow_ip_per_hour),
        ("REGISTRATION_PURGE_AFTER_HOURS", conf.purge_after),
    ],
)
@pytest.mark.parametrize("value", [0, -1])
def test_rate_limit_below_one_is_a_configuration_error(
    name: str, reader: Callable[[], object], value: int
) -> None:
    with override_settings(**{name: value}):
        with pytest.raises(ImproperlyConfigured, match=name):
            reader()


@override_settings(
    REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS=1,
    REGISTRATION_RATE_EMAIL_IP_PER_HOUR=1,
    REGISTRATION_RATE_IP_PER_HOUR=1,
    REGISTRATION_RESEND_INTERVAL_SECONDS=1,
    REGISTRATION_MAX_RESENDS=1,
    REGISTRATION_RATE_FLOW_IP_PER_HOUR=1,
    REGISTRATION_PURGE_AFTER_HOURS=1,
)
def test_rate_limits_of_one_are_valid() -> None:
    assert conf.rate_email_ip_interval() == timedelta(seconds=1)
    assert conf.rate_email_ip_per_hour() == 1
    assert conf.rate_ip_per_hour() == 1
    assert conf.resend_interval() == timedelta(seconds=1)
    assert conf.max_resends() == 1
    assert conf.rate_flow_ip_per_hour() == 1
    assert conf.purge_after() == timedelta(hours=1)
