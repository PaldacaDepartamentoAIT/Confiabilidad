import hashlib
import hmac
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class _KeyPolicy:
    current: Callable[[], str]
    previous_in_transition: Callable[[], str | None]


def _code_key() -> str:
    key = str(settings.REGISTRATION_CODE_SECRET)
    if not key.strip():
        raise ImproperlyConfigured(_("REGISTRATION_CODE_SECRET must not be empty."))
    if key == settings.REGISTRATION_CODE_SECRET_PREVIOUS:
        raise ImproperlyConfigured(
            _("REGISTRATION_CODE_SECRET_PREVIOUS must differ from REGISTRATION_CODE_SECRET.")
        )
    return key


def _previous_code_key_in_transition() -> str | None:
    raw_rotated_at = settings.REGISTRATION_CODE_SECRET_ROTATED_AT
    if not raw_rotated_at:
        return None
    rotated_at = parse_datetime(raw_rotated_at)
    if rotated_at is None or rotated_at.tzinfo is None:
        raise ImproperlyConfigured(
            _("REGISTRATION_CODE_SECRET_ROTATED_AT must be an ISO 8601 datetime with a timezone.")
        )
    previous = settings.REGISTRATION_CODE_SECRET_PREVIOUS
    if not previous:
        return None
    transition = timedelta(minutes=settings.REGISTRATION_SECRET_TRANSITION_MINUTES)
    if timezone.now() > rotated_at + transition:
        return None
    return str(previous)


_CODE_KEYS = _KeyPolicy(_code_key, _previous_code_key_in_transition)


def _consent_key() -> str:
    key = str(settings.CONSENT_EMAIL_HASH_SECRET)
    if not key.strip():
        raise ImproperlyConfigured(_("CONSENT_EMAIL_HASH_SECRET must not be empty."))
    return key


# Las huellas de consentimiento son pruebas permanentes: su clave nunca rota (S-09).
_CONSENT_KEYS = _KeyPolicy(_consent_key, lambda: None)


def _sign(key: str, message: str) -> str:
    return hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()


def _matches(keys: _KeyPolicy, message: str, fingerprint: str) -> bool:
    # La clave anterior se lee siempre para que una configuración rota falle en cada comprobación.
    previous = keys.previous_in_transition()
    if hmac.compare_digest(_sign(keys.current(), message), fingerprint):
        return True
    return previous is not None and hmac.compare_digest(_sign(previous, message), fingerprint)


def _code_message(purpose: str, public_id: str, code: str) -> str:
    return f"{purpose}:{public_id}:{code}"


def code_fingerprint(purpose: str, public_id: str, code: str) -> str:
    return _sign(_CODE_KEYS.current(), _code_message(purpose, public_id, code))


def code_matches(purpose: str, public_id: str, code: str, fingerprint: str) -> bool:
    return _matches(_CODE_KEYS, _code_message(purpose, public_id, code), fingerprint)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _account_message(email: str, password_hash: str) -> str:
    return f"password_reset_account:{_normalize_email(email)}:{password_hash}"


def account_stamp(email: str, password_hash: str) -> str:
    return _sign(_CODE_KEYS.current(), _account_message(email, password_hash))


def account_stamp_matches(stamp: str, email: str, password_hash: str) -> bool:
    return _matches(_CODE_KEYS, _account_message(email, password_hash), stamp)


def consent_email_fingerprint(email: str) -> str:
    return _sign(_CONSENT_KEYS.current(), _normalize_email(email))


def consent_email_matches(email: str, fingerprint: str) -> bool:
    return _matches(_CONSENT_KEYS, _normalize_email(email), fingerprint)
