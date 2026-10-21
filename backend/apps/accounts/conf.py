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


def start_retry_window() -> timedelta:
    return timedelta(minutes=settings.REGISTRATION_START_RETRY_MINUTES)


def rate_email_ip_interval() -> timedelta:
    return timedelta(seconds=settings.REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS)


def rate_email_ip_per_hour() -> int:
    return int(settings.REGISTRATION_RATE_EMAIL_IP_PER_HOUR)


def rate_ip_per_hour() -> int:
    return int(settings.REGISTRATION_RATE_IP_PER_HOUR)
