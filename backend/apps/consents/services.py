from dataclasses import dataclass
from enum import StrEnum

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.consents.models import MarketingConsent, Terms, UserTerms
from apps.consents.versions import InForceVersion, current_version, in_force_versions


class TermsState(StrEnum):
    ACCEPTED = "accepted"
    NOT_ACCEPTED = "not_accepted"
    NO_CURRENT_VERSION = "no_current_version"


@dataclass(frozen=True)
class ConsentStatus:
    terms: TermsState
    marketing: MarketingConsent | None


def consent_status(user: User) -> ConsentStatus:
    return ConsentStatus(
        terms=_terms_state(user),
        marketing=MarketingConsent.objects.filter(user=user, granted=True).first(),
    )


def _terms_state(user: User) -> TermsState:
    versions = in_force_versions(Terms.Kind.TERMS)
    if not versions:
        return TermsState.NO_CURRENT_VERSION
    required = _required_version(versions)
    valid = [v.version for v in versions if v.in_force_at >= required.in_force_at]
    accepted = (
        UserTerms.objects.filter(user=user, revoked_at__isnull=True)
        .annotate(version_key=Lower("terms__version"))
        .filter(version_key__in=valid)
        .exists()
    )
    return TermsState.ACCEPTED if accepted else TermsState.NOT_ACCEPTED


def _required_version(versions: list[InForceVersion]) -> InForceVersion:
    # Las versiones vienen de la más reciente a la más antigua; la primera en vigor siempre exige
    # aceptación (RF-017).
    for version in versions:
        if version.requires_reacceptance:
            return version
    return versions[-1]


def accept_terms(user: User, *, version: str, locale: str) -> UserTerms:
    _check_active(user)
    document = _current_document_shown(Terms.Kind.TERMS, version=version, locale=locale)
    with transaction.atomic():
        existing = _active_acceptance(user, document)
        if existing is not None:
            return existing
        acceptance = UserTerms(user=user, terms=document)
        try:
            with transaction.atomic():
                acceptance.save()
        except (IntegrityError, ValidationError):
            # Otra aceptación simultánea ganó la carrera: se devuelve esa (D-10).
            winner = UserTerms.objects.filter(
                user=user, terms=document, revoked_at__isnull=True
            ).first()
            if winner is None:
                raise
            return winner
    return acceptance


def grant_marketing(user: User, *, version: str, locale: str) -> MarketingConsent:
    _check_active(user)
    document = _current_document_shown(Terms.Kind.MARKETING, version=version, locale=locale)
    with transaction.atomic():
        active = _active_consent(user)
        if active is not None and active.terms_id == document.pk:
            return active
        if active is not None:
            _revoke(active)
        consent = MarketingConsent(user=user, terms=document)
        try:
            with transaction.atomic():
                consent.save()
        except (IntegrityError, ValidationError):
            winner = MarketingConsent.objects.filter(user=user, granted=True).first()
            if winner is None or winner.terms_id != document.pk:
                raise
            return winner
    return consent


def revoke_marketing(user: User) -> MarketingConsent | None:
    with transaction.atomic():
        active = _active_consent(user)
        if active is not None:
            _revoke(active)
    return active


def _active_consent(user: User) -> MarketingConsent | None:
    return MarketingConsent.objects.select_for_update().filter(user=user, granted=True).first()


def _revoke(consent: MarketingConsent) -> None:
    consent.granted = False
    consent.revoked_at = timezone.now()
    consent.save()


def _active_acceptance(user: User, document: Terms) -> UserTerms | None:
    return (
        UserTerms.objects.select_for_update()
        .filter(user=user, terms=document, revoked_at__isnull=True)
        .first()
    )


def _check_active(user: User) -> None:
    if not user.is_active:
        raise ValidationError(_("The account is inactive."), code="inactive_account")


def _current_document_shown(kind: str, *, version: str, locale: str) -> Terms:
    candidates = Terms.objects.filter(version__iexact=version, locale=locale)
    document = candidates.filter(kind=kind).first()
    if document is None:
        if candidates.exists():
            raise ValidationError(
                _("The document is not of kind %(kind)s."),
                code="wrong_kind",
                params={"kind": kind},
            )
        raise ValidationError(_("The document does not exist."), code="document_not_found")
    current = current_version(kind)
    if current is None:
        raise ValidationError(
            _("There is no current version of this document."), code="no_current_version"
        )
    if document.version.lower() != current.version:
        raise ValidationError(
            _("The document is not the current version."), code="not_current_document"
        )
    return document
