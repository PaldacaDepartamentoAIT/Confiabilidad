import pytest


@pytest.fixture(autouse=True)
def audit_hash_secret(settings: object) -> None:
    settings.AUDIT_HASH_SECRET = "test-audit-key"  # type: ignore[attr-defined]
