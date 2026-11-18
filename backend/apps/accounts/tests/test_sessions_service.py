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
from apps.core.fingerprints import audit_session_fingerprint

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
