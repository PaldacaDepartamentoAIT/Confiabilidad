import pytest
from django.db import IntegrityError

from apps.accounts.models import DEFAULT_USER_AGENT, UserSession
from apps.accounts.tests.factories import make_user
from apps.core.fingerprints import audit_session_fingerprint

pytestmark = pytest.mark.django_db


def test_user_session_stores_default_and_full_length_user_agent() -> None:
    user = make_user()
    blank = UserSession.objects.create(
        user=user,
        session_key=audit_session_fingerprint("raw-key-1"),
        ip="192.0.2.10",
        user_agent="   ",
    )
    long_ua = "Mozilla/5.0 " + ("X" * 1200)
    full = UserSession.objects.create(
        user=user,
        session_key=audit_session_fingerprint("raw-key-2"),
        ip="2001:db8::1",
        user_agent=long_ua,
    )

    assert blank.user_agent == DEFAULT_USER_AGENT
    assert full.user_agent == long_ua
    assert len(full.user_agent) > 1000
    assert str(blank) == f"{user.email}:192.0.2.10"


def test_user_session_key_is_unique() -> None:
    user = make_user()
    key_hash = audit_session_fingerprint("same-session-key")
    UserSession.objects.create(user=user, session_key=key_hash, ip="192.0.2.10")

    with pytest.raises(IntegrityError):
        UserSession.objects.create(user=user, session_key=key_hash, ip="192.0.2.11")
