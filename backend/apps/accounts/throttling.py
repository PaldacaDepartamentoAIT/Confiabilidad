import math
import time
from dataclasses import dataclass

from django.core.cache import cache

from apps.accounts import conf
from apps.core.fingerprints import consent_email_fingerprint

_MINUTE = 60.0
_HOUR = 3600.0


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    retry_after: int


def check_email_ip(email: str, ip: str, *, now: float | None = None) -> Verdict:
    # La pareja correo e IP impide que un tercero agote el límite del correo de otra persona (C-01).
    # upper() antes de lower() pliega "ı" y "ſ" como el iexact de Postgres que usa el registro.
    folded = email.strip().upper().lower()
    key = f"registration-rate:email-ip:{consent_email_fingerprint(folded)}:{ip}"
    return _check(
        key,
        per_hour=conf.rate_email_ip_per_hour(),
        interval=conf.rate_email_ip_interval().total_seconds(),
        now=time.time() if now is None else now,
    )


def check_ip(ip: str, *, now: float | None = None, record: bool = True) -> Verdict:
    # Sin apuntar, la vista decide después si la solicitud cuenta (S-06, D-12).
    return _check(
        _ip_key(ip),
        per_hour=conf.rate_ip_per_hour(),
        interval=0.0,
        now=time.time() if now is None else now,
        record=record,
    )


def check_flow_ip(ip: str, *, now: float | None = None) -> Verdict:
    # Verificar, reenviar y completar comparten un límite propio, aparte del formulario (RF-019).
    return _check(
        f"registration-rate:flow-ip:{ip}",
        per_hour=conf.rate_flow_ip_per_hour(),
        interval=0.0,
        now=time.time() if now is None else now,
    )


def check_login_ip(ip: str, *, now: float | None = None) -> Verdict:
    return _check(
        f"login-rate:ip:{ip}",
        per_hour=conf.login_rate_ip_per_minute(),
        interval=0.0,
        now=time.time() if now is None else now,
        window=_MINUTE,
    )


def _user_attempts_key(prefix: str, user_id: int) -> str:
    return f"{prefix}:attempts:{user_id}"


def _user_lock_key(prefix: str, user_id: int) -> str:
    return f"{prefix}:lock:{user_id}"


def _check_user_lock(prefix: str, user_id: int, *, now: float | None = None) -> Verdict:
    moment = time.time() if now is None else now
    locked_until = cache.get(_user_lock_key(prefix, user_id))
    if isinstance(locked_until, (int, float)) and locked_until > moment:
        return Verdict(allowed=False, retry_after=math.ceil(locked_until - moment))
    return Verdict(allowed=True, retry_after=0)


def _record_user_failure(
    prefix: str,
    user_id: int,
    *,
    window: float,
    max_attempts: int,
    lockout: float,
    now: float | None = None,
) -> Verdict:
    moment = time.time() if now is None else now
    key = _user_attempts_key(prefix, user_id)
    stamps = [*_recent(key, moment, window), moment]
    if len(stamps) >= max_attempts:
        cache.set(_user_lock_key(prefix, user_id), moment + lockout, timeout=int(lockout))
        cache.delete(key)
        return Verdict(allowed=False, retry_after=math.ceil(lockout))
    cache.set(key, stamps, timeout=int(window))
    return Verdict(allowed=True, retry_after=0)


def _clear_user_failures(prefix: str, user_id: int) -> None:
    cache.delete(_user_attempts_key(prefix, user_id))
    cache.delete(_user_lock_key(prefix, user_id))


def check_password_change(user_id: int, *, now: float | None = None) -> Verdict:
    return _check_user_lock("password-change", user_id, now=now)


def record_password_change_failure(user_id: int, *, now: float | None = None) -> Verdict:
    return _record_user_failure(
        "password-change",
        user_id,
        window=conf.password_change_attempt_window().total_seconds(),
        max_attempts=conf.password_change_max_failed_attempts(),
        lockout=conf.password_change_lockout_duration().total_seconds(),
        now=now,
    )


def clear_password_change_failures(user_id: int) -> None:
    _clear_user_failures("password-change", user_id)


def check_account_disable(user_id: int, *, now: float | None = None) -> Verdict:
    return _check_user_lock("account-disable", user_id, now=now)


def record_account_disable_failure(user_id: int, *, now: float | None = None) -> Verdict:
    return _record_user_failure(
        "account-disable",
        user_id,
        window=conf.account_disable_attempt_window().total_seconds(),
        max_attempts=conf.account_disable_max_failed_attempts(),
        lockout=conf.account_disable_lockout_duration().total_seconds(),
        now=now,
    )


def clear_account_disable_failures(user_id: int) -> None:
    _clear_user_failures("account-disable", user_id)


def record_ip(ip: str, *, now: float | None = None) -> None:
    key = _ip_key(ip)
    moment = time.time() if now is None else now
    _record(key, _recent(key, moment), moment)


def _ip_key(ip: str) -> str:
    return f"registration-rate:ip:{ip}"


def _recent(key: str, now: float, window: float = _HOUR) -> list[float]:
    return [stamp for stamp in cache.get(key, []) if stamp > now - window]


def _record(key: str, stamps: list[float], now: float, window: float = _HOUR) -> None:
    cache.set(key, [*stamps, now], timeout=int(window))


def _check(
    key: str,
    *,
    per_hour: int,
    interval: float,
    now: float,
    record: bool = True,
    window: float = _HOUR,
) -> Verdict:
    # Sin cerrojo: dos solicitudes simultáneas pueden colarse a la vez (D-09).
    stamps = _recent(key, now, window)
    wait = 0.0
    if stamps and interval:
        wait = max(wait, stamps[-1] + interval - now)
    if len(stamps) >= per_hour:
        wait = max(wait, stamps[-per_hour] + window - now)
    if wait > 0:
        return Verdict(allowed=False, retry_after=math.ceil(wait))
    if record:
        _record(key, stamps, now, window)
    return Verdict(allowed=True, retry_after=0)
