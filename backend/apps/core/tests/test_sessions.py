from importlib import import_module

from django.conf import settings


def test_session_engine_uses_isolated_cache() -> None:
    assert settings.SESSION_ENGINE == "django.contrib.sessions.backends.cache"
    assert settings.SESSION_CACHE_ALIAS == "sessions"
    assert "sessions" in settings.CACHES
    assert settings.CACHES["sessions"]["LOCATION"] != settings.CACHES["default"]["LOCATION"]


def test_session_persists_and_reads_back() -> None:
    engine = import_module(settings.SESSION_ENGINE)
    store = engine.SessionStore()
    store["user_id"] = 42
    store.save()

    reloaded = engine.SessionStore(session_key=store.session_key)
    assert reloaded["user_id"] == 42
