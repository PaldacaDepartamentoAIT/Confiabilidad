import logging
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from allauth.account.models import EmailAddress
from celery import current_app
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts import codes, conf, processes, signals
from apps.accounts.models import PendingRegistration, PhantomProcess, User
from apps.accounts.processes import VerifyResult as VerifyResult
from apps.accounts.validators import normalize_country, normalize_name
from apps.emails import locales, outbox

_PURPOSE = codes.Purpose.REGISTRATION
logger = logging.getLogger(__name__)


RESOLVE_TASK = "apps.accounts.tasks.resolve_registration"
REISSUE_TASK = "apps.accounts.tasks.reissue_code"


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
    *,
    email: str,
    name: str,
    birthdate: date,
    country: str,
    language: str = locales.DEFAULT,
    terms_version: str = "",
    terms_locale: str = "",
) -> Started:
    # La respuesta hace el mismo trabajo tenga o no cuenta el correo: valida los datos y deja una
    # plaza que se resuelve fuera de la respuesta (D-11).
    validate_registration_data(email=email, name=name, birthdate=birthdate, country=country)
    payload: dict[str, str] = {
        "name": normalize_name(name),
        "birthdate": birthdate.isoformat(),
        "country": normalize_country(country),
        "language": locales.normalize(language),
    }
    if terms_version:
        payload.update(terms_version=terms_version, terms_locale=terms_locale)
    slot = PhantomProcess(
        purpose=_PURPOSE,
        email=email,
        public_id=codes.generate_public_id(),
        code_hash="",
        code_expires_at=timezone.now() + conf.code_ttl(),
        payload=payload,
    )
    with transaction.atomic():
        slot.save()
        transaction.on_commit(lambda: _queue(RESOLVE_TASK, [slot.public_id]))
    # Auditoría en la petición, igual con plaza o con registro real (D-14): una fila por petición.
    signals.pending_registration_requested.send(
        sender=PendingRegistration, email=email, success=True
    )
    signals.registration_code_sent.send(sender=PendingRegistration, email=email, success=True)
    return Started(public_id=slot.public_id)


def _queue(task: str, args: list[str]) -> None:
    # Si la cola no responde, la respuesta no cambia: el barrido recoge las plazas (D-15) y un
    # reenvío perdido se repite pidiendo otro.
    try:
        current_app.send_task(task, args=args)
    except Exception:
        logger.warning("Could not queue %s; the process keeps waiting.", task)


def _locked_process(public_id: str) -> PendingRegistration | PhantomProcess | None:
    # Consulta las dos tablas siempre, para hacer el mismo trabajo con plaza o sin ella (D-14), y
    # primero la plaza, en el orden de la resolución: si la está convirtiendo, se espera (D-18).
    slot = (
        PhantomProcess.objects.select_for_update()
        .filter(public_id=public_id, purpose=_PURPOSE)
        .first()
    )
    pending = PendingRegistration.objects.select_for_update().filter(public_id=public_id).first()
    return pending or slot


def verify(*, public_id: str, code: str) -> VerifyResult:
    with transaction.atomic():
        process = _locked_process(public_id)
        if process is None:
            return VerifyResult.NOT_FOUND
        if process.is_expired:
            signals.registration_code_verified.send(
                sender=PendingRegistration, email=process.email, success=False
            )
            return VerifyResult.EXPIRED
        result = processes.check_code(process, _PURPOSE, code)
        signals.registration_code_verified.send(
            sender=PendingRegistration,
            email=process.email,
            success=result is VerifyResult.VERIFIED,
        )
        return result


@dataclass(frozen=True)
class Resent:
    public_id: str


class ResendRefusal(StrEnum):
    EXPIRED = "expired"
    ALREADY_VERIFIED = "already_verified"
    NOT_FOUND = "not_found"


def resend(*, public_id: str) -> Resent | ResendRefusal:
    # En la respuesta solo se anula el código vigente; el nuevo lo emite reissue_code (D-13).
    with transaction.atomic():
        process = _locked_process(public_id)
        if process is None:
            return ResendRefusal.NOT_FOUND
        if process.is_expired:
            return ResendRefusal.EXPIRED
        if process.code_validated_at is not None:
            return ResendRefusal.ALREADY_VERIFIED
        # Sin save(): un registro real no admite la huella vacía en su validación.
        type(process).objects.filter(pk=process.pk).update(code_hash="", failed_attempts=0)
        transaction.on_commit(lambda: _queue(REISSUE_TASK, [_PURPOSE, public_id]))
        signals.registration_code_sent.send(
            sender=PendingRegistration, email=process.email, success=True
        )
        return Resent(public_id=public_id)


def reissue_code(public_id: str) -> None:
    # La plaza recibe también un código nuevo, que nunca se envía (D-13).
    with transaction.atomic():
        process = _locked_process(public_id)
        if process is None or process.is_expired or process.code_validated_at is not None:
            return
        code = processes.renew_code(process, _PURPOSE)
        if isinstance(process, PendingRegistration):
            outbox.enqueue(
                kind="registration_code",
                recipient=process.email,
                locale=process.language,
                context={"name": process.name},
                purpose=_PURPOSE,
                public_id=public_id,
                code=code,
            )


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
        pending = _locked_process(public_id)
        if pending is None:
            return CompleteRefusal.NOT_FOUND
        if pending.is_expired:
            return CompleteRefusal.EXPIRED
        if pending.code_validated_at is None or isinstance(pending, PhantomProcess):
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
        signals.account_created.send(sender=User, email=user.email, success=True)
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
        # El mismo criterio que la cuenta y el registro pendiente: Postgres pliega `ı`→`I`, `ſ`→`S`.
        same_email = PhantomProcess.objects.filter(purpose=_PURPOSE, email__iexact=email)
        # Manda la petición más reciente: con una posterior sin resolver, esta no hace nada (D-17).
        if same_email.filter(pk__gt=slot.pk, payload__isnull=False).exists():
            slot.delete()
            return
        # Solo una plaza resuelta transmite su alta: una abandonada no dejó registro (D-16).
        previous = (
            same_email.filter(pk__lt=slot.pk, resolved_at__isnull=False).order_by("-pk").first()
        )
        same_email.filter(pk__lt=slot.pk).delete()
        PendingRegistration.objects.expired().filter(email__iexact=email).delete()
        account = User.objects.filter(email__iexact=email).first()
        if account is not None:
            signals.pending_registration_requested.send(
                sender=PendingRegistration, email=email, success=False
            )
            _leave_as_issued(slot, previous)
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


def _leave_as_issued(slot: PhantomProcess, previous: PhantomProcess | None) -> None:
    # Queda como un registro recién emitido (D-16): intentos y plazos desde la resolución, y el alta
    # de la plaza vigente que reemplaza, como un registro repetido conserva la suya (RF-005).
    slot.payload = None
    slot.failed_attempts = 0
    slot.code_validated_at = None
    slot.code_expires_at = timezone.now() + conf.code_ttl()
    slot.resolved_at = timezone.now()
    if previous is not None and not previous.is_expired:
        slot.created_at = previous.created_at
    else:
        slot.created_at = timezone.now()
    slot.save(
        update_fields=[
            "payload",
            "resolved_at",
            "failed_attempts",
            "code_validated_at",
            "code_expires_at",
            "created_at",
        ]
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
            terms_version=str(data.get("terms_version", "")),
            terms_locale=str(data.get("terms_locale", "")),
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
    pending, _by_model = PendingRegistration.objects.expired().delete()
    slots, _by_model = PhantomProcess.objects.expired().filter(purpose=_PURPOSE).delete()
    return pending + slots
