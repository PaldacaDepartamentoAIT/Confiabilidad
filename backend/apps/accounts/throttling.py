import math
import time
from dataclasses import dataclass

from django.core.cache import cache

from apps.accounts import conf
from apps.core.fingerprints import consent_email_fingerprint

_HOUR = 3600.0


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    retry_after: int


def check_email_ip(email: str, ip: str, *, now: float | None = None) -> Verdict:
    # La pareja correo e IP impide que un tercero agote el límite del correo de otra persona (C-01).
    key = f"registration-rate:email-ip:{consent_email_fingerprint(email)}:{ip}"
    return _check(
        key,
        per_hour=conf.rate_email_ip_per_hour(),
        interval=conf.rate_email_ip_interval().total_seconds(),
        now=time.time() if now is None else now,
    )


def check_ip(ip: str, *, now: float | None = None) -> Verdict:
    return _check(
        f"registration-rate:ip:{ip}",
        per_hour=conf.rate_ip_per_hour(),
        interval=0.0,
        now=time.time() if now is None else now,
    )


def _check(key: str, *, per_hour: int, interval: float, now: float) -> Verdict:
    # Sin cerrojo: dos solicitudes simultáneas pueden colarse a la vez (D-09).
    stamps = [stamp for stamp in cache.get(key, []) if stamp > now - _HOUR]
    wait = 0.0
    if stamps and interval:
        wait = max(wait, stamps[-1] + interval - now)
    if len(stamps) >= per_hour:
        wait = max(wait, stamps[-per_hour] + _HOUR - now)
    if wait > 0:
        return Verdict(allowed=False, retry_after=math.ceil(wait))
    cache.set(key, [*stamps, now], timeout=int(_HOUR))
    return Verdict(allowed=True, retry_after=0)
