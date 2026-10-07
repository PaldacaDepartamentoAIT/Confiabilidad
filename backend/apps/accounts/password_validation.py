import hashlib
import http.client
import logging
import urllib.request

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.accounts import conf

logger = logging.getLogger(__name__)

RANGE_URL = "https://api.pwnedpasswords.com/range/{prefix}"


class PwnedPasswordValidator:
    def validate(self, password: str, user: object | None = None) -> None:
        if not getattr(settings, "PWNED_PASSWORDS_ENABLED", True):
            return
        digest = hashlib.sha1(password.encode(), usedforsecurity=False).hexdigest().upper()
        prefix, suffix = digest[:5], digest[5:]
        try:
            count = _breach_count(_fetch_range(prefix), suffix)
        except (OSError, ValueError, http.client.HTTPException) as error:
            logger.warning("Pwned Passwords check skipped: %s", type(error).__name__)
            return
        if count > 0:
            raise ValidationError(
                _("This password has appeared in a data breach and cannot be used."),
                code="password_pwned",
            )

    def get_help_text(self) -> str:
        return gettext("Your password can't be one that has appeared in a known data breach.")


def _fetch_range(prefix: str) -> str:
    request = urllib.request.Request(
        RANGE_URL.format(prefix=prefix),
        headers={"Add-Padding": "true", "User-Agent": "confiabilidad"},
    )
    with urllib.request.urlopen(request, timeout=conf.pwned_timeout()) as response:
        body: bytes = response.read()
    return body.decode()


def _breach_count(body: str, suffix: str) -> int:
    for line in body.splitlines():
        candidate, _separator, count = line.partition(":")
        if candidate.strip().upper() == suffix:
            return int(count)
    return 0
