from dataclasses import dataclass
from datetime import datetime

from django.contrib.postgres.aggregates import BoolOr
from django.db.models import Count, Max
from django.db.models.functions import Lower
from django.utils import timezone

from apps.consents.models import Terms
from apps.consents.validators import LOCALES


@dataclass(frozen=True)
class InForceVersion:
    # Versión en minúsculas: "V1" y "v1" son la misma versión (RF-002).
    version: str
    in_force_at: datetime
    requires_reacceptance: bool


def in_force_versions(kind: str) -> list[InForceVersion]:
    rows = (
        Terms.objects.filter(kind=kind, published_at__lte=timezone.now())
        .values(key=Lower("version"))
        .annotate(
            languages=Count("id"),
            in_force_at=Max("published_at"),
            last_created_at=Max("created_at"),
            requires_reacceptance=BoolOr("requires_reacceptance"),
        )
        .filter(languages=len(LOCALES))
        .order_by("-in_force_at", "-last_created_at")
    )
    return [
        InForceVersion(
            version=row["key"],
            in_force_at=row["in_force_at"],
            requires_reacceptance=row["requires_reacceptance"],
        )
        for row in rows
    ]


def current_version(kind: str) -> InForceVersion | None:
    versions = in_force_versions(kind)
    return versions[0] if versions else None


def current_document(kind: str, locale: str) -> Terms | None:
    current = current_version(kind)
    if current is None:
        return None
    return Terms.objects.filter(kind=kind, locale=locale, version__iexact=current.version).first()
