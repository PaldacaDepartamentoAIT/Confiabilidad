from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.consents.models import MarketingConsent, Terms, UserTerms
from apps.consents.versions import current_version


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
