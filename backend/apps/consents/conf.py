from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


def email_hash_secret() -> str:
    secret = str(settings.CONSENT_EMAIL_HASH_SECRET)
    if not secret.strip():
        raise ImproperlyConfigured(_("CONSENT_EMAIL_HASH_SECRET must not be empty."))
    return secret
