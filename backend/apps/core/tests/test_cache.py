from django.conf import settings
from django.core.cache import cache


def test_cache_default_uses_redis_backend() -> None:
    assert settings.CACHES["default"]["BACKEND"] == "django.core.cache.backends.redis.RedisCache"


def test_cache_set_get_roundtrip() -> None:
    cache.set("demo-key", "demo-value", timeout=30)
    assert cache.get("demo-key") == "demo-value"
