from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


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
    return timedelta(seconds=_at_least_one("REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS"))


def rate_email_ip_per_hour() -> int:
    return _at_least_one("REGISTRATION_RATE_EMAIL_IP_PER_HOUR")


def rate_ip_per_hour() -> int:
    return _at_least_one("REGISTRATION_RATE_IP_PER_HOUR")


def resend_interval() -> timedelta:
    return timedelta(seconds=_at_least_one("REGISTRATION_RESEND_INTERVAL_SECONDS"))


def max_resends() -> int:
    return _at_least_one("REGISTRATION_MAX_RESENDS")


def rate_flow_ip_per_hour() -> int:
    return _at_least_one("REGISTRATION_RATE_FLOW_IP_PER_HOUR")


def purge_after() -> timedelta:
    return timedelta(hours=_at_least_one("REGISTRATION_PURGE_AFTER_HOURS"))


def _at_least_one(name: str) -> int:
    # Un límite de 0 no tiene significado definido: es un error de configuración, no un cierre.
    value = int(getattr(settings, name))
    if value < 1:
        raise ImproperlyConfigured(
            _("%(name)s must be at least 1 (got %(value)d).") % {"name": name, "value": value}
        )
    return value
