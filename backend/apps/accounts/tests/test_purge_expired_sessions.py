from datetime import timedelta
from importlib import import_module
from io import StringIO
from unittest import mock

import pytest
from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.core.management import call_command
from django.http import HttpRequest
from django.test import RequestFactory
from django.utils import timezone

from apps.accounts import sessions, tasks
from apps.accounts.models import UserSession
from apps.accounts.tests.factories import make_user

pytestmark = pytest.mark.django_db


def _store(session_key: str | None = None) -> SessionBase:
    engine = import_module(settings.SESSION_ENGINE)
    store_cls: type[SessionBase] = engine.SessionStore
    return store_cls(session_key=session_key)


def _request() -> HttpRequest:
    request = RequestFactory().get("/", REMOTE_ADDR="192.0.2.30")
    store = _store()
    store.create()
    request.session = store
    return request


def test_purge_expired_sessions_command_deletes_only_expired_and_reports_count() -> None:
    user = make_user()
    active_row = sessions.register_session(_request(), user)
    expired_row = sessions.register_session(_request(), user)
    evicted_req = _request()
    evicted_row = sessions.register_session(evicted_req, user)
    assert active_row and expired_row and evicted_row and evicted_req.session.session_key

    UserSession.objects.filter(pk=expired_row.pk).update(
        last_seen_at=timezone.now() - timedelta(days=15)
    )
    _store(evicted_req.session.session_key).delete()

    stdout = StringIO()
    call_command("purge_expired_sessions", stdout=stdout)

    assert stdout.getvalue().strip() == "2 expired user sessions deleted."
    assert list(UserSession.objects.values_list("pk", flat=True)) == [active_row.pk]


def test_purge_expired_sessions_task_delegates_and_runs_hourly() -> None:
    with mock.patch.object(sessions, "purge_expired", return_value=4) as purge:
        assert tasks.purge_expired_sessions() == 4
    purge.assert_called_once_with()

    entries = [
        entry
        for entry in settings.CELERY_BEAT_SCHEDULE.values()
        if entry["task"] == "apps.accounts.tasks.purge_expired_sessions"
    ]
    assert [entry["schedule"] for entry in entries] == [3600.0]
