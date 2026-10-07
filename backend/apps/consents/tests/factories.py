from datetime import datetime, timedelta
from itertools import count
from typing import Any

from django.utils import timezone

from apps.consents.models import Terms
from apps.consents.validators import LOCALES

_version_sequence = count(1)


def make_document(**overrides: Any) -> Terms:
    fields: dict[str, Any] = {
        "kind": Terms.Kind.TERMS,
        "content": "Legal **text**.",
        "version": f"f{next(_version_sequence)}",
        "locale": "es",
    }
    fields.update(overrides)
    document = Terms(**fields)
    document.save()
    return document


def publish_version(
    kind: str = Terms.Kind.TERMS,
    version: str | None = None,
    published_at: datetime | None = None,
    **overrides: Any,
) -> dict[str, Terms]:
    version = version or f"f{next(_version_sequence)}"
    published_at = published_at or timezone.now() - timedelta(days=1)
    return {
        locale: make_document(
            kind=kind, version=version, locale=locale, published_at=published_at, **overrides
        )
        for locale in LOCALES
    }
