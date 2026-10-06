from datetime import UTC, datetime, timedelta

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
