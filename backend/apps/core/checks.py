from typing import Any

from django.conf import settings
from django.core.checks import Error, Tags, register
from django.utils.translation import gettext_lazy as _


@register(Tags.security)
def check_audit_hash_secret(app_configs: Any, **kwargs: Any) -> list[Error]:
    if not str(settings.AUDIT_HASH_SECRET).strip():
        message = _("AUDIT_HASH_SECRET must not be empty.")
        # Django acepta textos perezosos en los checks; los stubs solo admiten str.
        return [Error(message, id="audit.E001")]  # type: ignore[arg-type]
    return []
