from typing import Any

from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.security)
def check_audit_hash_secret(app_configs: Any, **kwargs: Any) -> list[Error]:
    if not str(settings.AUDIT_HASH_SECRET).strip():
        return [Error("AUDIT_HASH_SECRET must not be empty.", id="audit.E001")]
    return []
