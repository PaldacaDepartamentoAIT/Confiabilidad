from django.core.cache import cache
from django.test import override_settings

from apps.accounts import throttling

T0 = 1_000_000.0
MINUTE = 60


def _login_ip(ip: str = "192.0.2.1", at: float = T0) -> throttling.Verdict:
    return throttling.check_login_ip(ip, now=at)


def test_login_ip_allows_thirty_requests_per_minute_and_rejects_thirty_first() -> None:
    for second in range(30):
        assert _login_ip(at=T0 + second) == throttling.Verdict(allowed=True, retry_after=0)

    assert _login_ip(at=T0 + 20) == throttling.Verdict(allowed=False, retry_after=MINUTE - 20)
    assert _login_ip(at=T0 + MINUTE).allowed


def test_rejected_login_ip_requests_do_not_consume_quota() -> None:
    for second in range(30):
        _login_ip(at=T0 + second)
    for second in range(30, 55):
        assert not _login_ip(at=T0 + second).allowed

    assert _login_ip(at=T0 + MINUTE).allowed


def test_login_ip_limit_follows_configured_setting() -> None:
    with override_settings(LOGIN_RATE_IP_PER_MINUTE=2):
        assert _login_ip(at=T0).allowed
        assert _login_ip(at=T0 + 1).allowed
        assert _login_ip(at=T0 + 2) == throttling.Verdict(allowed=False, retry_after=MINUTE - 2)


def test_login_ip_limit_is_independent_per_ip_and_from_registration_limits() -> None:
    for second in range(20):
        throttling.check_ip("192.0.2.1", now=T0 + second)
    for second in range(60):
        throttling.check_flow_ip("192.0.2.1", now=T0 + second)

    assert _login_ip("192.0.2.1", at=T0 + 10).allowed
    assert cache.get("login-rate:ip:192.0.2.1") == [T0 + 10]
    with override_settings(LOGIN_RATE_IP_PER_MINUTE=1):
        assert not _login_ip("192.0.2.1", at=T0 + 11).allowed
        assert _login_ip("198.51.100.7", at=T0 + 11).allowed
