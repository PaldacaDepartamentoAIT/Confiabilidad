import logging
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from allauth.account.models import EmailAddress
from celery import current_app
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts import codes, conf, processes
from apps.accounts.models import PendingRegistration, PhantomProcess, User
from apps.accounts.processes import VerifyResult as VerifyResult
from apps.accounts.validators import normalize_country, normalize_name
from apps.emails import locales, outbox

_PURPOSE = codes.Purpose.REGISTRATION
logger = logging.getLogger(__name__)


RESOLVE_TASK = "apps.accounts.tasks.resolve_registration"


@dataclass(frozen=True)
class Started:
    public_id: str


def validate_registration_data(*, email: str, name: str, birthdate: date, country: str) -> None:
    # Solo las reglas que no consultan la base de datos: que el correo tenga cuenta nunca se
    # indica en la respuesta (RF-024).
    pending = PendingRegistration(email=email, name=name, birthdate=birthdate, country=country)
    pending.email = pending.email.strip().lower()
    pending.name = normalize_name(pending.name)
    pending.country = normalize_country(pending.country)
    pending.full_clean(
        exclude=["public_id", "code_hash", "code_expires_at"],
        validate_unique=False,
        validate_constraints=False,
    )


def start(
    *, email: str, name: str, birthdate: date, country: str, language: str = locales.DEFAULT
) -> Started:
    # La respuesta hace el mismo trabajo tenga o no cuenta el correo: valida los datos y deja una
    # plaza que se resuelve fuera de la respuesta (D-11).
    validate_registration_data(email=email, name=name, birthdate=birthdate, country=country)
    slot = PhantomProcess(
        purpose=_PURPOSE,
        email=email,
        public_id=codes.generate_public_id(),
        code_hash="",
        code_expires_at=timezone.now() + conf.code_ttl(),
        payload={
            "name": normalize_name(name),
            "birthdate": birthdate.isoformat(),
            "country": normalize_country(country),
            "language": locales.normalize(language),
        },
    )
    with transaction.atomic():
        slot.save()
        transaction.on_commit(lambda: _queue_resolution(slot.public_id))
    return Started(public_id=slot.public_id)


def _queue_resolution(public_id: str) -> None:
    # Si la cola no responde, el barrido de plazas la recoge (D-15).
    try:
        current_app.send_task(RESOLVE_TASK, args=[public_id])
    except Exception:
        logger.warning("Could not queue the start of a registration; the sweep will retry it.")


def verify(*, public_id: str, code: str) -> VerifyResult:
    with transaction.atomic():
        pending = (
            PendingRegistration.objects.select_for_update().filter(public_id=public_id).first()
        )
        if pending is None:
            return VerifyResult.NOT_FOUND
        if pending.is_expired:
            return VerifyResult.EXPIRED
        return processes.check_code(pending, _PURPOSE, code)


@dataclass(frozen=True)
class Resent:
    public_id: str
    code: str


class ResendRefusal(StrEnum):
    EXPIRED = "expired"
    ALREADY_VERIFIED = "already_verified"
    NOT_FOUND = "not_found"


def resend(*, public_id: str) -> Resent | ResendRefusal:
    with transaction.atomic():
        pending = (
            PendingRegistration.objects.select_for_update().filter(public_id=public_id).first()
        )
        if pending is None:
            return ResendRefusal.NOT_FOUND
        if pending.is_expired:
            return ResendRefusal.EXPIRED
        if pending.code_validated_at is not None:
            return ResendRefusal.ALREADY_VERIFIED
        code = processes.renew_code(pending, _PURPOSE)
        return Resent(public_id=public_id, code=code)


@dataclass(frozen=True)
class Completed:
    user: User


class CompleteRefusal(StrEnum):
    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    CODE_NOT_VERIFIED = "code_not_verified"
    ACCOUNT_EXISTS = "account_exists"


def complete(*, public_id: str, password: str) -> Completed | CompleteRefusal:
    with transaction.atomic():
        pending = (
            PendingRegistration.objects.select_for_update().filter(public_id=public_id).first()
        )
        if pending is None:
            return CompleteRefusal.NOT_FOUND
        if pending.is_expired:
            return CompleteRefusal.EXPIRED
        if pending.code_validated_at is None:
            return CompleteRefusal.CODE_NOT_VERIFIED
        if User.objects.filter(email__iexact=pending.email).exists():
            pending.delete()
            return CompleteRefusal.ACCOUNT_EXISTS
        user = User(
            email=pending.email,
            name=pending.name,
            birthdate=pending.birthdate,
            country=pending.country,
            language=pending.language,
        )
        validate_password(password, user=user)
        user.set_password(password)
        user.save()
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        pending.delete()
        return Completed(user=user)


def resolve_registration(public_id: str) -> None:
    # Todo lo que depende de que el correo tenga cuenta, fuera de la respuesta (D-16).
    with transaction.atomic():
        slot = (
            PhantomProcess.objects.select_for_update()
            .filter(public_id=public_id, purpose=_PURPOSE, payload__isnull=False)
            .first()
        )
        if slot is None:
            return
        email, data = slot.email, dict(slot.payload or {})
        PhantomProcess.objects.filter(purpose=_PURPOSE, email=email).exclude(pk=slot.pk).delete()
        PendingRegistration.objects.expired().filter(email__iexact=email).delete()
        account = User.objects.filter(email__iexact=email).first()
        if account is not None:
            slot.payload = None
            slot.save(update_fields=["payload"])
            if account.is_active:
                outbox.enqueue(
                    kind="account_exists",
                    recipient=account.email,
                    locale=account.language,
                    context={"name": account.name},
                    account=account,
                )
            return
        slot.delete()
        pending, code = _register_or_repeat(public_id, email, data)
        outbox.enqueue(
            kind="registration_code",
            recipient=pending.email,
            locale=str(data["language"]),
            context={"name": pending.name},
            purpose=_PURPOSE,
            public_id=public_id,
            code=code,
        )


def _register_or_repeat(
    public_id: str, email: str, data: dict[str, object]
) -> tuple[PendingRegistration, str]:
    existing = PendingRegistration.objects.filter(email__iexact=email).select_for_update().first()
    if existing is None:
        pending = PendingRegistration(
            email=email,
            name=str(data["name"]),
            birthdate=date.fromisoformat(str(data["birthdate"])),
            country=str(data["country"]),
            language=str(data["language"]),
        )
        code = processes.issue_code(pending, _PURPOSE, public_id)
        try:
            with transaction.atomic():
                pending.save()
            return pending, code
        except IntegrityError:
            existing = (
                PendingRegistration.objects.select_for_update().filter(email__iexact=email).first()
            )
            if existing is None:
                raise
    # Registro repetido (RF-005): conserva los datos y toma el identificador de la plaza.
    code = processes.issue_code(existing, _PURPOSE, public_id)
    existing.save(update_fields=processes.ISSUED_FIELDS)
    return existing, code


def purge_expired() -> int:
    _total, by_model = PendingRegistration.objects.expired().delete()
    return by_model.get(PendingRegistration._meta.label, 0)
