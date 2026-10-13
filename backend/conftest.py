import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def audit_hash_secret(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = "test-audit-key"  # type: ignore[attr-defined]


@pytest.fixture(autouse=True)
def clear_login_rate_limits() -> None:
    cache.clear()
