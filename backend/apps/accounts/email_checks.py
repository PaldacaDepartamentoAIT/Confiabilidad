from datetime import datetime

from django.utils import timezone

from apps.accounts import codes
from apps.accounts.models import CodeProcess, PasswordResetRequest, PendingRegistration
from apps.core import fingerprints


def registration_code_expiry(public_id: str, code: str) -> datetime | None:
    pending = PendingRegistration.objects.filter(public_id=public_id).first()
    return _expiry(pending, codes.Purpose.REGISTRATION, code)


def password_reset_code_expiry(public_id: str, code: str) -> datetime | None:
    request = PasswordResetRequest.objects.filter(public_id=public_id).first()
    return _expiry(request, codes.Purpose.PASSWORD_RESET, code)


def _expiry(process: CodeProcess | None, purpose: codes.Purpose, code: str) -> datetime | None:
    # El correo de un código solo sirve si es el código vigente, sin validar y sin caducar (RF-015).
    if process is None or process.code_validated_at is not None or process.is_expired:
        return None
    if timezone.now() >= process.code_expires_at:
        return None
    if not fingerprints.code_matches(purpose, process.public_id, code, process.code_hash):
        return None
    return process.code_expires_at
