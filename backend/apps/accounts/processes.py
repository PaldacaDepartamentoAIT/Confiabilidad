from enum import StrEnum

from django.utils import timezone

from apps.accounts import codes, conf
from apps.accounts.models import CodeProcess

ISSUED_FIELDS = [
    "public_id",
    "code_hash",
    "code_expires_at",
    "failed_attempts",
    "code_validated_at",
]


class VerifyResult(StrEnum):
    VERIFIED = "verified"
    WRONG_CODE = "wrong_code"
    LOCKED = "locked"
    CODE_EXPIRED = "code_expired"
    EXPIRED = "expired"
    ALREADY_VERIFIED = "already_verified"
    NOT_FOUND = "not_found"


def issue_code(process: CodeProcess, purpose: codes.Purpose) -> str:
    process.public_id = codes.generate_public_id()
    process.failed_attempts = 0
    process.code_validated_at = None
    return _set_new_code(process, purpose)


def renew_code(process: CodeProcess, purpose: codes.Purpose) -> str:
    process.failed_attempts = 0
    code = _set_new_code(process, purpose)
    process.save(update_fields=["code_hash", "code_expires_at", "failed_attempts"])
    return code


def check_code(process: CodeProcess, purpose: codes.Purpose, code: str) -> VerifyResult:
    if process.code_validated_at is not None:
        return VerifyResult.ALREADY_VERIFIED
    if process.is_locked:
        return VerifyResult.LOCKED
    if timezone.now() >= process.code_expires_at:
        return VerifyResult.CODE_EXPIRED
    if not codes.verify_code(purpose, process.public_id, code, process.code_hash):
        process.failed_attempts += 1
        process.save(update_fields=["failed_attempts"])
        return VerifyResult.WRONG_CODE
    process.code_validated_at = timezone.now()
    process.save(update_fields=["code_validated_at"])
    return VerifyResult.VERIFIED


def _set_new_code(process: CodeProcess, purpose: codes.Purpose) -> str:
    code = codes.generate_code()
    process.code_hash = codes.code_fingerprint(purpose, process.public_id, code)
    process.code_expires_at = timezone.now() + conf.code_ttl()
    return code
