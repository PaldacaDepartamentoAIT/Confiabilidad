from importlib import import_module

import pytest
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.sessions.backends.base import SessionBase
from django.http import HttpRequest
from django.test import RequestFactory

from apps.accounts import password_reset, sessions
from apps.accounts.models import UserSession
from apps.accounts.tests.factories import make_reset_request, make_user

pytestmark = pytest.mark.django_db


def _store(session_key: str | None = None) -> SessionBase:
    engine = import_module(settings.SESSION_ENGINE)
    store_cls: type[SessionBase] = engine.SessionStore
    return store_cls(session_key=session_key)


def _request(session_key: str | None = None) -> HttpRequest:
    request = RequestFactory().post("/", REMOTE_ADDR="192.0.2.20")
    request.META["HTTP_USER_AGENT"] = "LifecycleTest/1.0"
    store = _store(session_key)
    if session_key is None:
        store.create()
    request.session = store
    return request


def test_login_and_logout_signals_sync_user_session() -> None:
    user = make_user()
    request = _request()

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    raw_key = request.session.session_key
    assert raw_key is not None
    assert UserSession.objects.filter(user=user).count() == 1
    assert sessions.is_session_active(raw_key, user.pk)

    logout(request)
    assert not UserSession.objects.filter(user=user).exists()
    assert not sessions.is_session_active(raw_key, user.pk)


def test_deactivating_and_deleting_user_revokes_all_sessions() -> None:
    user = make_user()
    req_1 = _request()
    req_2 = _request()
    login(req_1, user, backend="django.contrib.auth.backends.ModelBackend")
    login(req_2, user, backend="django.contrib.auth.backends.ModelBackend")
    key_1 = req_1.session.session_key
    key_2 = req_2.session.session_key
    assert key_1 and key_2

    user.is_active = False
    user.save(update_fields=["is_active"])

    assert not UserSession.objects.filter(user=user).exists()
    assert not _store(key_1).exists(key_1)
    assert not _store(key_2).exists(key_2)

    user.is_active = True
    user.save(update_fields=["is_active"])
    req_3 = _request()
    login(req_3, user, backend="django.contrib.auth.backends.ModelBackend")
    key_3 = req_3.session.session_key
    assert key_3 is not None

    user.delete()
    assert not UserSession.objects.exists()
    assert not _store(key_3).exists(key_3)


def test_changing_password_or_completing_reset_revokes_all_sessions() -> None:
    user = make_user()
    req_save = _request()
    login(req_save, user, backend="django.contrib.auth.backends.ModelBackend")
    key_save = req_save.session.session_key
    assert key_save is not None

    user.set_password("N3w-Strong-Pass-2026!")
    user.save()

    assert not UserSession.objects.filter(user=user).exists()
    assert not _store(key_save).exists(key_save)

    req_reset = _request()
    login(req_reset, user, backend="django.contrib.auth.backends.ModelBackend")
    key_reset = req_reset.session.session_key
    assert key_reset is not None
    started = make_reset_request(user.email)
    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        password_reset.VerifyResult.VERIFIED
    )
    password_reset.complete(public_id=started.public_id, password="An0ther-Strong-2026!")

    assert not UserSession.objects.filter(user=user).exists()
    assert not _store(key_reset).exists(key_reset)
