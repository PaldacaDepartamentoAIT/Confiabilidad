from datetime import timedelta
from importlib import import_module

import pytest
from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.core.cache import caches
from django.http import HttpRequest
from django.test import RequestFactory, override_settings
from django.utils import timezone

from apps.accounts import sessions
from apps.accounts.models import DEFAULT_USER_AGENT, UserSession
from apps.accounts.tests.factories import make_user
from apps.audit.models import EventType, SecurityEvent
from apps.core.fingerprints import audit_email_fingerprint, audit_session_fingerprint

pytestmark = pytest.mark.django_db


def _store(session_key: str | None = None) -> SessionBase:
    engine = import_module(settings.SESSION_ENGINE)
    store_cls: type[SessionBase] = engine.SessionStore
    return store_cls(session_key=session_key)


def _request(
    *, ip: str = "192.0.2.10", user_agent: str = "Browser/1.0", session_key: str | None = None
) -> HttpRequest:
    request = RequestFactory().get("/", REMOTE_ADDR=ip)
    if user_agent:
        request.META["HTTP_USER_AGENT"] = user_agent
    store = _store(session_key)
    if session_key is None:
        store.create()
    request.session = store
    return request


def test_register_session_stores_hmac_fingerprint_and_reverse_key() -> None:
    user = make_user()
    request = _request(ip="203.0.113.5", user_agent="")
    raw_key = request.session.session_key
    assert raw_key is not None

    row = sessions.register_session(request, user)

    assert row is not None
    assert row.session_key == audit_session_fingerprint(raw_key)
    assert row.session_key != raw_key
    assert row.ip == "203.0.113.5"
    assert row.user_agent == DEFAULT_USER_AGENT
    assert sessions.is_session_active(raw_key, user.pk)


def test_touch_session_updates_only_after_configured_interval() -> None:
    user = make_user()
    request = _request(ip="192.0.2.1", user_agent="First/1.0")
    raw_key = request.session.session_key
    assert raw_key is not None
    row = sessions.register_session(request, user)
    assert row is not None

    initial_seen = row.last_seen_at
    assert not sessions.touch_session(
        _request(ip="192.0.2.2", user_agent="Second/2.0", session_key=raw_key),
        user,
    )
    row.refresh_from_db()
    assert (row.last_seen_at, row.ip, row.user_agent) == (initial_seen, "192.0.2.1", "First/1.0")

    UserSession.objects.filter(pk=row.pk).update(
        last_seen_at=timezone.now() - timedelta(seconds=61)
    )
    assert sessions.touch_session(
        _request(ip="192.0.2.2", user_agent="Second/2.0", session_key=raw_key),
        user,
    )
    row.refresh_from_db()
    assert row.last_seen_at > initial_seen
    assert row.ip == "192.0.2.2"
    assert row.user_agent == "Second/2.0"


def test_list_active_sessions_cleans_expired_and_orders_recent_first() -> None:
    user = make_user()
    req_old = _request(ip="192.0.2.1", user_agent="Old")
    req_new = _request(ip="192.0.2.2", user_agent="New")
    req_expired = _request(ip="192.0.2.3", user_agent="Expired")
    req_evicted = _request(ip="192.0.2.4", user_agent="Evicted")

    old_row = sessions.register_session(req_old, user)
    new_row = sessions.register_session(req_new, user)
    expired_row = sessions.register_session(req_expired, user)
    evicted_row = sessions.register_session(req_evicted, user)
    assert old_row and new_row and expired_row and evicted_row

    now = timezone.now()
    UserSession.objects.filter(pk=old_row.pk).update(last_seen_at=now - timedelta(hours=2))
    UserSession.objects.filter(pk=new_row.pk).update(last_seen_at=now - timedelta(minutes=5))
    UserSession.objects.filter(pk=expired_row.pk).update(last_seen_at=now - timedelta(days=15))
    _store(req_evicted.session.session_key).delete()

    listed = sessions.list_active_sessions(user, req_new.session.session_key)

    assert [item.id for item in listed] == [new_row.pk, old_row.pk]
    assert [item.is_current for item in listed] == [True, False]
    assert not UserSession.objects.filter(pk__in=[expired_row.pk, evicted_row.pk]).exists()


def test_close_current_session_deletes_row_and_invalidates_store() -> None:
    user = make_user()
    request = _request()
    raw_key = request.session.session_key
    assert raw_key is not None
    sessions.register_session(request, user)

    sessions.close_current_session(user, raw_key)

    assert not UserSession.objects.filter(user=user).exists()
    assert not _store(raw_key).exists(raw_key)
    assert not sessions.is_session_active(raw_key, user.pk)
    assert (
        caches[settings.SESSION_CACHE_ALIAS].get(
            f"user-session-key:{audit_session_fingerprint(raw_key)}"
        )
        is None
    )


@override_settings(SESSION_LIFETIME_DAYS=1)
def test_session_expiry_respects_configured_lifetime() -> None:
    user = make_user()
    request = _request()
    raw_key = request.session.session_key
    assert raw_key is not None
    row = sessions.register_session(request, user)
    assert row is not None
    UserSession.objects.filter(pk=row.pk).update(
        last_seen_at=timezone.now() - timedelta(days=1, seconds=1)
    )

    assert not sessions.is_session_active(raw_key, user.pk)
    assert sessions.list_active_sessions(user, raw_key) == []


def test_revoke_other_session_closes_only_target_and_records_logout() -> None:
    user = make_user()
    other_user = make_user()
    req_current = _request(ip="192.0.2.1", user_agent="Current")
    req_other = _request(ip="192.0.2.2", user_agent="Other")
    req_foreign = _request(ip="192.0.2.3", user_agent="Foreign")
    current_row = sessions.register_session(req_current, user)
    other_row = sessions.register_session(req_other, user)
    foreign_row = sessions.register_session(req_foreign, other_user)
    assert current_row and other_row and foreign_row

    current_key = req_current.session.session_key
    other_key = req_other.session.session_key
    assert current_key and other_key

    assert (
        sessions.revoke_other_session(user, current_key, current_row.pk)
        == sessions.RevokeResult.CURRENT_SESSION
    )
    assert (
        sessions.revoke_other_session(user, current_key, foreign_row.pk)
        == sessions.RevokeResult.NOT_FOUND
    )
    assert (
        sessions.revoke_other_session(user, current_key, 999_999) == sessions.RevokeResult.NOT_FOUND
    )
    assert (
        sessions.revoke_other_session(user, current_key, other_row.pk, request=req_current)
        == sessions.RevokeResult.REVOKED
    )

    assert sessions.is_session_active(current_key, user.pk)
    assert not sessions.is_session_active(other_key, user.pk)
    assert not _store(other_key).exists(other_key)
    assert not UserSession.objects.filter(pk=other_row.pk).exists()
    event = SecurityEvent.objects.get(event_type=EventType.LOGOUT)
    assert event.user_email_hash == audit_email_fingerprint(user.email)
    assert event.session_key == audit_session_fingerprint(other_key)


def test_revoke_all_other_sessions_handles_empty_and_multiple_sessions() -> None:
    user = make_user()
    req_current = _request(ip="192.0.2.1", user_agent="Current")
    sessions.register_session(req_current, user)
    current_key = req_current.session.session_key
    assert current_key is not None

    assert sessions.revoke_all_other_sessions(user, current_key, request=req_current) == 0
    assert not SecurityEvent.objects.filter(event_type=EventType.LOGOUT).exists()

    req_a = _request(ip="192.0.2.2", user_agent="A")
    req_b = _request(ip="192.0.2.3", user_agent="B")
    sessions.register_session(req_a, user)
    sessions.register_session(req_b, user)

    assert sessions.revoke_all_other_sessions(user, current_key, request=req_current) == 2
    assert sessions.is_session_active(current_key, user.pk)
    assert UserSession.objects.filter(user=user).count() == 1
    assert SecurityEvent.objects.filter(event_type=EventType.LOGOUT).count() == 2


def test_revoke_all_user_sessions_and_purge_expired() -> None:
    user = make_user()
    other_user = make_user()
    req_1 = _request()
    req_2 = _request()
    req_other_active = _request()
    req_other_expired = _request()
    req_other_evicted = _request()

    sessions.register_session(req_1, user)
    sessions.register_session(req_2, user)
    active_row = sessions.register_session(req_other_active, other_user)
    expired_row = sessions.register_session(req_other_expired, other_user)
    evicted_row = sessions.register_session(req_other_evicted, other_user)
    assert active_row and expired_row and evicted_row

    assert sessions.revoke_all_user_sessions(user) == 2
    assert not UserSession.objects.filter(user=user).exists()
    assert req_1.session.session_key and not _store(req_1.session.session_key).exists(
        req_1.session.session_key
    )

    UserSession.objects.filter(pk=expired_row.pk).update(
        last_seen_at=timezone.now() - timedelta(days=15)
    )
    assert req_other_evicted.session.session_key
    _store(req_other_evicted.session.session_key).delete()

    assert sessions.purge_expired() == 2
    assert list(UserSession.objects.values_list("pk", flat=True)) == [active_row.pk]
