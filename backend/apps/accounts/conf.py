from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _


def max_failed_attempts() -> int:
    return int(settings.REGISTRATION_MAX_FAILED_ATTEMPTS)


def code_ttl() -> timedelta:
    return timedelta(minutes=settings.REGISTRATION_CODE_TTL_MINUTES)


def grace_period() -> timedelta:
    return timedelta(minutes=settings.REGISTRATION_GRACE_MINUTES)


def max_lifetime() -> timedelta:
    return timedelta(minutes=settings.REGISTRATION_MAX_LIFETIME_MINUTES)


def secret_transition() -> timedelta:
    return timedelta(minutes=settings.REGISTRATION_SECRET_TRANSITION_MINUTES)


def code_secret() -> str:
    secret = str(settings.REGISTRATION_CODE_SECRET)
    if not secret.strip():
        raise ImproperlyConfigured(_("REGISTRATION_CODE_SECRET must not be empty."))
    if secret == settings.REGISTRATION_CODE_SECRET_PREVIOUS:
        raise ImproperlyConfigured(
            _("REGISTRATION_CODE_SECRET_PREVIOUS must differ from REGISTRATION_CODE_SECRET.")
        )
    return secret


def previous_code_secret() -> str | None:
    return settings.REGISTRATION_CODE_SECRET_PREVIOUS or None


def secret_rotated_at() -> datetime | None:
    raw = settings.REGISTRATION_CODE_SECRET_ROTATED_AT
    if not raw:
        return None
    parsed = parse_datetime(raw)
    if parsed is None or parsed.tzinfo is None:
        raise ImproperlyConfigured(
            _("REGISTRATION_CODE_SECRET_ROTATED_AT must be an ISO 8601 datetime with a timezone.")
        )
    return parsed


def pwned_timeout() -> float:
    return float(settings.PWNED_PASSWORDS_TIMEOUT_SECONDS)
