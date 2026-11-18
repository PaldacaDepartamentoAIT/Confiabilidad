import secrets
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from importlib import import_module
from typing import Any

from django.conf import settings
from django.contrib.auth.signals import user_logged_out
from django.contrib.sessions.backends.base import SessionBase
from django.core.cache import caches
from django.http import HttpRequest
from django.utils import timezone

from apps.accounts import conf
from apps.accounts.models import DEFAULT_USER_AGENT, User, UserSession
from apps.core.fingerprints import audit_session_fingerprint

_REVERSE_KEY_PREFIX = "user-session-key:"


class RevokeResult(StrEnum):
    REVOKED = "revoked"
    CURRENT_SESSION = "cannot_revoke_current_session"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class ActiveSession:
    id: int
    ip: str
    user_agent: str
    created_at: datetime
    last_seen_at: datetime
    is_current: bool


def _session_cache() -> Any:
    return caches[settings.SESSION_CACHE_ALIAS]


def _session_store(session_key: str | None = None) -> SessionBase:
    engine = import_module(settings.SESSION_ENGINE)
    store_cls: type[SessionBase] = engine.SessionStore
    return store_cls(session_key=session_key)


def _reverse_key(key_hash: str) -> str:
    return f"{_REVERSE_KEY_PREFIX}{key_hash}"


def _store_reverse_key(key_hash: str, raw_key: str) -> None:
    ttl = int(conf.session_lifetime().total_seconds())
    _session_cache().set(_reverse_key(key_hash), raw_key, timeout=ttl)


def _delete_from_store(raw_key: str) -> None:
    _session_store(raw_key).delete()


def _raw_key(key_hash: str) -> str | None:
    raw = _session_cache().get(_reverse_key(key_hash))
    return raw if isinstance(raw, str) and raw else None


def _exists_in_store(key_hash: str) -> bool:
    raw_key = _raw_key(key_hash)
    return raw_key is not None and _session_store(raw_key).exists(raw_key)


def _evict_from_store(key_hash: str) -> str | None:
    raw_key = _raw_key(key_hash)
    _session_cache().delete(_reverse_key(key_hash))
    if raw_key is None or not _session_store(raw_key).exists(raw_key):
        return None
    _delete_from_store(raw_key)
    return raw_key


def _logout_request(
    acting_request: HttpRequest | None, row: UserSession, raw_key: str
) -> HttpRequest:
    request = HttpRequest()
    request.session = _session_store(raw_key)
    request.META["REMOTE_ADDR"] = _request_ip(acting_request) if acting_request else row.ip
    request.META["HTTP_USER_AGENT"] = (
        _request_user_agent(acting_request) if acting_request else row.user_agent
    )
    return request


def _request_ip(request: HttpRequest) -> str:
    ip = str(request.META.get("REMOTE_ADDR") or "").strip()
    return ip or "127.0.0.1"


def _request_user_agent(request: HttpRequest) -> str:
    agent = str(request.META.get("HTTP_USER_AGENT") or "")
    return agent if agent.strip() else DEFAULT_USER_AGENT


def register_session(request: HttpRequest, user: User) -> UserSession | None:
    raw_key = request.session.session_key
    if not raw_key:
        return None
    key_hash = audit_session_fingerprint(raw_key)
    now = timezone.now()
    row, _ = UserSession.objects.update_or_create(
        session_key=key_hash,
        defaults={
            "user": user,
            "ip": _request_ip(request),
            "user_agent": _request_user_agent(request),
            "last_seen_at": now,
        },
    )
    _store_reverse_key(key_hash, raw_key)
    return row


def is_session_active(raw_key: str, user_id: int) -> bool:
    if not raw_key:
        return False
    key_hash = audit_session_fingerprint(raw_key)
    cutoff = timezone.now() - conf.session_lifetime()
    exists = UserSession.objects.filter(
        user_id=user_id,
        session_key=key_hash,
        last_seen_at__gt=cutoff,
    ).exists()
    return exists and _exists_in_store(key_hash)


def touch_session(request: HttpRequest, user: User) -> bool:
    raw_key = request.session.session_key
    if not raw_key:
        return False
    key_hash = audit_session_fingerprint(raw_key)
    row = UserSession.objects.filter(user=user, session_key=key_hash).first()
    if row is None:
        return False
    now = timezone.now()
    if now - row.last_seen_at < conf.session_activity_update_interval():
        return False
    row.last_seen_at = now
    row.ip = _request_ip(request)
    row.user_agent = _request_user_agent(request)
    row.save(update_fields=["last_seen_at", "ip", "user_agent"])
    _store_reverse_key(key_hash, raw_key)
    return True


def list_active_sessions(user: User, current_session_key: str | None) -> list[ActiveSession]:
    cutoff = timezone.now() - conf.session_lifetime()
    UserSession.objects.filter(user=user, last_seen_at__lte=cutoff).delete()
    rows = list(UserSession.objects.filter(user=user).order_by("-last_seen_at", "-id"))
    stale_ids = [row.pk for row in rows if not _exists_in_store(row.session_key)]
    if stale_ids:
        UserSession.objects.filter(pk__in=stale_ids).delete()
        stale_set = set(stale_ids)
        rows = [row for row in rows if row.pk not in stale_set]
    current_hash = audit_session_fingerprint(current_session_key) if current_session_key else None
    return [
        ActiveSession(
            id=row.pk,
            ip=row.ip,
            user_agent=row.user_agent,
            created_at=row.created_at,
            last_seen_at=row.last_seen_at,
            is_current=current_hash is not None
            and secrets.compare_digest(row.session_key, current_hash),
        )
        for row in rows
    ]


def close_current_session(user: User, session_key: str) -> None:
    if not session_key:
        return
    key_hash = audit_session_fingerprint(session_key)
    UserSession.objects.filter(user=user, session_key=key_hash).delete()
    _session_cache().delete(_reverse_key(key_hash))
    _delete_from_store(session_key)


def revoke_other_session(
    user: User,
    current_session_key: str | None,
    session_id: int,
    *,
    request: HttpRequest | None = None,
) -> RevokeResult:
    row = UserSession.objects.filter(pk=session_id, user=user).first()
    if row is None:
        return RevokeResult.NOT_FOUND
    if current_session_key and secrets.compare_digest(
        row.session_key, audit_session_fingerprint(current_session_key)
    ):
        return RevokeResult.CURRENT_SESSION
    expired = row.last_seen_at <= timezone.now() - conf.session_lifetime()
    raw_key = _evict_from_store(row.session_key)
    row.delete()
    if expired or raw_key is None:
        return RevokeResult.NOT_FOUND
    user_logged_out.send(sender=User, request=_logout_request(request, row, raw_key), user=user)
    return RevokeResult.REVOKED


def revoke_all_other_sessions(
    user: User,
    current_session_key: str | None,
    *,
    request: HttpRequest | None = None,
) -> int:
    cutoff = timezone.now() - conf.session_lifetime()
    current_hash = audit_session_fingerprint(current_session_key) if current_session_key else None
    rows = list(UserSession.objects.filter(user=user))
    targets = [
        row
        for row in rows
        if current_hash is None or not secrets.compare_digest(row.session_key, current_hash)
    ]
    if not targets:
        return 0
    revoked = 0
    for row in targets:
        raw_key = _evict_from_store(row.session_key)
        if row.last_seen_at > cutoff and raw_key is not None:
            user_logged_out.send(
                sender=User, request=_logout_request(request, row, raw_key), user=user
            )
            revoked += 1
    UserSession.objects.filter(pk__in=[row.pk for row in targets]).delete()
    return revoked


def revoke_all_user_sessions(user: User, *, clear_only: bool = False) -> int:
    rows = list(UserSession.objects.filter(user=user))
    for row in rows:
        if clear_only:
            _clear_in_store(row.session_key)
        else:
            _evict_from_store(row.session_key)
    deleted, _ = UserSession.objects.filter(user=user).delete()
    return deleted


def _clear_in_store(key_hash: str) -> None:
    raw_key = _raw_key(key_hash)
    _session_cache().delete(_reverse_key(key_hash))
    if raw_key is None:
        return
    store = _session_store(raw_key)
    if store.exists(raw_key):
        store.clear()
        store.save()


def purge_expired() -> int:
    cutoff = timezone.now() - conf.session_lifetime()
    expired_rows = list(UserSession.objects.filter(last_seen_at__lte=cutoff))
    for row in expired_rows:
        _evict_from_store(row.session_key)
    deleted = 0
    if expired_rows:
        deleted, _ = UserSession.objects.filter(pk__in=[row.pk for row in expired_rows]).delete()
    evicted_ids = [
        row.pk for row in UserSession.objects.all() if not _exists_in_store(row.session_key)
    ]
    if evicted_ids:
        evicted_deleted, _ = UserSession.objects.filter(pk__in=evicted_ids).delete()
        deleted += evicted_deleted
    return deleted
