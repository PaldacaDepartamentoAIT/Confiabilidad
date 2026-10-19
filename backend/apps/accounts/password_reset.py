import logging
from dataclasses import dataclass
from enum import StrEnum

from allauth.account import app_settings as allauth_account_settings
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.core.internal import ratelimit as allauth_ratelimit
from celery import current_app
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import HttpRequest
from django.utils import timezone

from apps.accounts import codes, conf, processes, signals
from apps.accounts.models import PasswordResetRequest, PhantomProcess, User
from apps.accounts.processes import VerifyResult as VerifyResult
from apps.core import fingerprints
from apps.emails import locales, outbox

_PURPOSE = codes.Purpose.PASSWORD_RESET
_REPLACED_FIELDS = [*processes.ISSUED_FIELDS, "created_at", "account_stamp", "language"]
RESOLVE_TASK = "apps.accounts.tasks.resolve_password_reset"
REISSUE_TASK = "apps.accounts.tasks.reissue_code"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Started:
    public_id: str


def start(*, email: str, language: str = locales.DEFAULT) -> Started:
    # Solo se valida el formato del correo; si tiene cuenta se decide fuera de la respuesta (D-13).
    email = email.strip()
    try:
        validate_email(email)
    except ValidationError as error:
        raise ValidationError({"email": error.error_list}) from error
    slot = PhantomProcess(
        purpose=_PURPOSE,
        email=email,
        public_id=codes.generate_public_id(),
        code_hash="",
        code_expires_at=timezone.now() + conf.code_ttl(),
        payload={"language": locales.normalize(language)},
    )
    with transaction.atomic():
        slot.save()
        transaction.on_commit(lambda: _queue(RESOLVE_TASK, [slot.public_id]))
    # Auditoría en la petición, igual con plaza o con solicitud real (D-14).
    signals.password_reset_code_sent.send(sender=PasswordResetRequest, email=email, success=True)
    return Started(public_id=slot.public_id)


def _leave_as_issued(slot: PhantomProcess) -> None:
    # Queda como una solicitud recién emitida (D-13): intentos, plazos y vida desde la resolución.
    now = timezone.now()
    slot.payload = None
    slot.failed_attempts = 0
    slot.code_validated_at = None
    slot.code_expires_at = now + conf.code_ttl()
    slot.created_at = now
    slot.save(
        update_fields=[
            "payload",
            "failed_attempts",
            "code_validated_at",
            "code_expires_at",
            "created_at",
        ]
    )


def _queue(task: str, args: list[str]) -> None:
    # Si la cola no responde, la respuesta no cambia: el barrido recoge las plazas (D-15 de
    # procesos-pendientes).
    try:
        current_app.send_task(task, args=args)
    except Exception:
        logger.warning("Could not queue %s; the process keeps waiting.", task)


def _create_or_replace(
    user: User, public_id: str, language: str
) -> tuple[PasswordResetRequest, str]:
    request = _locked_request(user)
    if request is None:
        request = PasswordResetRequest(user=user)
        code = _issue(request, public_id, language)
        try:
            with transaction.atomic():
                request.save()
            return request, code
        except IntegrityError:
            request = _locked_request(user)
            if request is None:
                raise
    code = _issue(request, public_id, language)
    request.save(update_fields=_REPLACED_FIELDS)
    return request, code


def resolve_password_reset(public_id: str) -> None:
    # Todo lo que depende de que el correo tenga cuenta, fuera de la respuesta (D-13).
    with transaction.atomic():
        slot = (
            PhantomProcess.objects.select_for_update()
            .filter(public_id=public_id, purpose=_PURPOSE, payload__isnull=False)
            .first()
        )
        if slot is None:
            return
        email, language = slot.email, str((slot.payload or {}).get("language"))
        # El mismo criterio que la cuenta: Postgres pliega `ı`→`I` y `ſ`→`S` (D-13).
        same_email = PhantomProcess.objects.filter(purpose=_PURPOSE, email__iexact=email)
        # Manda la petición más reciente (D-17 de procesos-pendientes).
        if same_email.filter(pk__gt=slot.pk, payload__isnull=False).exists():
            slot.delete()
            return
        same_email.filter(pk__lt=slot.pk).delete()
        user = User.objects.select_for_update().filter(email__iexact=email).first()
        if user is None or not user.is_active:
            _leave_as_issued(slot)
            return
        slot.delete()
        _request, code = _create_or_replace(user, public_id, language)
        outbox.enqueue(
            kind="password_reset_code",
            recipient=user.email,
            locale=language,
            context={"name": user.name},
            purpose=_PURPOSE,
            public_id=public_id,
            code=code,
        )


def verify(*, public_id: str, code: str) -> VerifyResult:
    with transaction.atomic():
        process = _locked_process(public_id)
        if process is None:
            return VerifyResult.NOT_FOUND
        if _answers_expired(process):
            signals.password_reset_code_verified.send(
                sender=PasswordResetRequest, email=_audit_email(process), success=False
            )
            return VerifyResult.EXPIRED
        result = processes.check_code(process, _PURPOSE, code)
        signals.password_reset_code_verified.send(
            sender=PasswordResetRequest,
            email=_audit_email(process),
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
        if _answers_expired(process):
            return ResendRefusal.EXPIRED
        if process.code_validated_at is not None:
            return ResendRefusal.ALREADY_VERIFIED
        # Sin save(): una solicitud real no admite la huella vacía en su validación.
        type(process).objects.filter(pk=process.pk).update(code_hash="", failed_attempts=0)
        transaction.on_commit(lambda: _queue(REISSUE_TASK, [_PURPOSE, public_id]))
        signals.password_reset_code_sent.send(
            sender=PasswordResetRequest, email=_audit_email(process), success=True
        )
        return Resent(public_id=public_id)


def reissue_code(public_id: str) -> None:
    # La plaza recibe también un código nuevo, que nunca se envía (D-13).
    with transaction.atomic():
        process = _locked_process(public_id)
        if process is None or _answers_expired(process) or process.code_validated_at is not None:
            return
        code = processes.renew_code(process, _PURPOSE)
        if isinstance(process, PasswordResetRequest):
            outbox.enqueue(
                kind="password_reset_code",
                recipient=process.user.email,
                locale=process.language,
                context={"name": process.user.name},
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


def complete(*, public_id: str, password: str) -> Completed | CompleteRefusal:
    with transaction.atomic():
        # Plaza, cuenta y solicitud, el mismo orden que la resolución, para no interbloquearse ni
        # leer la solicitud antes de que la resolución la confirme (D-05). Sin solicitud se bloquea
        # una cuenta inexistente: las mismas consultas (D-14).
        slot = _locked_slot(public_id)
        user_id = _owner_id(public_id)
        locked_user = User.objects.select_for_update().filter(pk=user_id or 0).first()
        request = (
            PasswordResetRequest.objects.select_for_update(of=("self",))
            .select_related("user")
            .filter(public_id=public_id, user=locked_user)
            .first()
        )
        process = request or slot
        if process is None:
            return CompleteRefusal.NOT_FOUND
        if _answers_expired(process):
            return CompleteRefusal.EXPIRED
        if process.code_validated_at is None or not isinstance(process, PasswordResetRequest):
            return CompleteRefusal.CODE_NOT_VERIFIED
        user = process.user
        validate_password(password, user=user)
        user.set_password(password)
        user.save(update_fields=["password"])
        _mark_email_verified(user)
        # En la misma transacción: si algo falla, no queda ni la contraseña ni el aviso (D-16).
        outbox.enqueue(
            kind="password_reset_done",
            recipient=user.email,
            locale=user.language,
            context={"name": user.name},
            account=user,
        )
        process.delete()
        email = user.email
        transaction.on_commit(lambda: _clear_failed_logins(email))
        signals.password_reset_completed.send(sender=User, email=email, success=True)
        return Completed(user=user)


def purge_expired() -> int:
    requests, _by_model = PasswordResetRequest.objects.expired().delete()
    # Las tumbas también se borran al llegar su caducidad natural (D-15).
    slots, _by_model = PhantomProcess.objects.expired().filter(purpose=_PURPOSE).delete()
    return requests + slots


def _audit_email(process: PasswordResetRequest | PhantomProcess) -> str:
    return process.user.email if isinstance(process, PasswordResetRequest) else process.email


def _owner_id(public_id: str) -> int | None:
    owner: int | None = (
        PasswordResetRequest.objects.filter(public_id=public_id)
        .values_list("user_id", flat=True)
        .first()
    )
    return owner


def _mark_email_verified(user: User) -> None:
    address = EmailAddress.objects.filter(user=user, email__iexact=user.email).first()
    if address is None:
        has_primary = EmailAddress.objects.filter(user=user, primary=True).exists()
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=not has_primary
        )
    elif not address.verified:
        address.verified = True
        address.save(update_fields=["verified"])


def _clear_failed_logins(email: str) -> None:
    # Solo las tasas por correo: la tasa por IP no es de la cuenta (S-12). Con SITE_ID, allauth no
    # necesita una petición real para calcular la clave.
    request = HttpRequest()
    key = get_adapter()._get_login_attempts_cache_key(request, email=email)
    rates = allauth_ratelimit.parse_rates(allauth_account_settings.RATE_LIMITS.get("login_failed"))
    for rate in rates:
        if rate.per == "key":
            cache.delete(
                allauth_ratelimit.get_cache_key(request, action="login_failed", rate=rate, key=key)
            )


def _locked_by_public_id(public_id: str) -> PasswordResetRequest | None:
    return (
        PasswordResetRequest.objects.select_for_update(of=("self",))
        .select_related("user")
        .filter(public_id=public_id)
        .first()
    )


def _locked_process(public_id: str) -> PasswordResetRequest | PhantomProcess | None:
    # Consulta las dos tablas siempre, para hacer el mismo trabajo con plaza o sin ella (D-14), y
    # primero la plaza, en el orden de la resolución: si la está convirtiendo, se espera (D-05).
    slot = _locked_slot(public_id)
    request = _locked_by_public_id(public_id)
    return request or slot


def _locked_slot(public_id: str) -> PhantomProcess | None:
    return (
        PhantomProcess.objects.select_for_update()
        .filter(public_id=public_id, purpose=_PURPOSE)
        .first()
    )


def _answers_expired(process: PasswordResetRequest | PhantomProcess) -> bool:
    # Cuenta inactiva o cambiada y tumba de una cuenta borrada responden como una solicitud
    # caducada: una plaza nunca da otros rechazos (D-14, D-15).
    if process.is_expired:
        return True
    if isinstance(process, PhantomProcess):
        return process.answers_expired
    user = process.user
    return not user.is_active or not fingerprints.account_stamp_matches(
        process.account_stamp, user.email, user.password
    )


def _locked_request(user: User) -> PasswordResetRequest | None:
    return PasswordResetRequest.objects.select_for_update().filter(user=user).first()


def _issue(request: PasswordResetRequest, public_id: str, language: str) -> str:
    code = processes.issue_code(request, _PURPOSE, public_id)
    request.created_at = timezone.now()
    request.language = locales.normalize(language)
    request.account_stamp = fingerprints.account_stamp(request.user.email, request.user.password)
    return code
