from django.core.cache import cache
from django.test import override_settings

from apps.accounts import throttling
from apps.core import fingerprints

T0 = 1_000_000.0
HOUR = 3600


def _email_ip(
    email: str = "ana@x.com", ip: str = "192.0.2.1", at: float = T0
) -> throttling.Verdict:
    return throttling.check_email_ip(email, ip, now=at)


def test_first_request_is_allowed() -> None:
    assert _email_ip() == throttling.Verdict(allowed=True, retry_after=0)


def test_same_email_and_ip_within_the_interval_waits_the_rest() -> None:
    _email_ip(at=T0)
    assert _email_ip(at=T0 + 20) == throttling.Verdict(allowed=False, retry_after=40)
    assert _email_ip(at=T0 + 60).allowed


def test_sixth_request_in_an_hour_waits_until_the_first_leaves_the_window() -> None:
    for minute in range(5):
        assert _email_ip(at=T0 + minute * 60).allowed
    assert _email_ip(at=T0 + 10 * 60) == throttling.Verdict(
        allowed=False, retry_after=HOUR - 10 * 60
    )
    assert _email_ip(at=T0 + HOUR).allowed


def test_rejected_requests_are_not_counted() -> None:
    _email_ip(at=T0)
    for second in range(1, 60):
        assert not _email_ip(at=T0 + second).allowed
    assert _email_ip(at=T0 + 60).allowed


def test_same_email_from_another_ip_is_independent() -> None:
    _email_ip(ip="192.0.2.1", at=T0)
    assert _email_ip(ip="198.51.100.7", at=T0 + 1).allowed


def test_email_is_normalized_before_counting() -> None:
    _email_ip(email=" Ana@X.com ", at=T0)
    assert not _email_ip(email="ana@x.com", at=T0 + 1).allowed


def test_cache_key_uses_the_email_fingerprint_not_the_email() -> None:
    _email_ip(email="ana@x.com", ip="192.0.2.1", at=T0)
    fingerprint = fingerprints.consent_email_fingerprint("ana@x.com")
    assert cache.get(f"registration-rate:email-ip:{fingerprint}:192.0.2.1") == [T0]
    assert cache.get("registration-rate:email-ip:ana@x.com:192.0.2.1") is None


def test_ip_is_rejected_after_twenty_requests_in_an_hour() -> None:
    for second in range(20):
        assert throttling.check_ip("192.0.2.1", now=T0 + second).allowed
    assert throttling.check_ip("192.0.2.1", now=T0 + 30) == throttling.Verdict(
        allowed=False, retry_after=HOUR - 30
    )
    assert throttling.check_ip("198.51.100.7", now=T0 + 30).allowed
    assert throttling.check_ip("192.0.2.1", now=T0 + HOUR).allowed


def test_rejected_ip_requests_are_not_counted() -> None:
    for second in range(20):
        throttling.check_ip("192.0.2.1", now=T0 + second)
    for second in range(100):
        throttling.check_ip("192.0.2.1", now=T0 + 100 + second)
    assert throttling.check_ip("192.0.2.1", now=T0 + HOUR).allowed


def test_wait_is_rounded_up_to_whole_seconds() -> None:
    _email_ip(at=T0)
    assert _email_ip(at=T0 + 59.2).retry_after == 1


@override_settings(
    REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS=10,
    REGISTRATION_RATE_EMAIL_IP_PER_HOUR=2,
    REGISTRATION_RATE_IP_PER_HOUR=1,
)
def test_configured_limits_are_applied() -> None:
    assert _email_ip(at=T0).allowed
    assert _email_ip(at=T0 + 10).allowed
    assert _email_ip(at=T0 + 20) == throttling.Verdict(allowed=False, retry_after=HOUR - 20)
    assert throttling.check_ip("192.0.2.9", now=T0).allowed
    assert not throttling.check_ip("192.0.2.9", now=T0 + 1).allowed


def test_checking_the_ip_without_recording_does_not_use_the_quota() -> None:
    for second in range(100):
        assert throttling.check_ip("192.0.2.1", now=T0 + second, record=False).allowed
    assert cache.get("registration-rate:ip:192.0.2.1") is None
    for second in range(20):
        assert throttling.check_ip("192.0.2.1", now=T0 + 200 + second).allowed


def test_recorded_ip_requests_count_for_the_quota() -> None:
    for second in range(20):
        throttling.record_ip("192.0.2.1", now=T0 + second)
    assert throttling.check_ip("192.0.2.1", now=T0 + 30, record=False) == throttling.Verdict(
        allowed=False, retry_after=HOUR - 30
    )
