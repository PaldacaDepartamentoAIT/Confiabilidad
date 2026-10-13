from datetime import timedelta

from django.conf import settings


def max_failed_attempts() -> int:
    return int(settings.REGISTRATION_MAX_FAILED_ATTEMPTS)


def code_ttl() -> timedelta:
    return timedelta(minutes=settings.REGISTRATION_CODE_TTL_MINUTES)


def grace_period() -> timedelta:
    return timedelta(minutes=settings.REGISTRATION_GRACE_MINUTES)


def max_lifetime() -> timedelta:
    return timedelta(minutes=settings.REGISTRATION_MAX_LIFETIME_MINUTES)


def pwned_timeout() -> float:
    return float(settings.PWNED_PASSWORDS_TIMEOUT_SECONDS)
