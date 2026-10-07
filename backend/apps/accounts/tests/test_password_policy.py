import hashlib
import http.client
import logging
import urllib.error
import urllib.request
from datetime import date

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.test import override_settings

import config.settings as project_settings
from apps.accounts.models import User
from apps.accounts.password_validation import PwnedPasswordValidator


def _user(email: str = "x@example.com", name: str = "Bea Ruiz") -> User:
    return User(email=email, name=name, birthdate=date(1990, 5, 10), country="ES")


def _rejection_codes(password: str, user: User) -> set[str | None]:
    with pytest.raises(ValidationError) as excinfo:
        validate_password(password, user=user)
    return {error.code for error in excinfo.value.error_list}


def test_good_password_of_twelve_characters_is_accepted() -> None:
    validate_password("Kq7#mZ2!vR9p", user=_user())


def test_eleven_characters_are_rejected() -> None:
    assert "password_too_short" in _rejection_codes("Kq7#mZ2!vR9", _user())


def test_password_similar_to_the_email_is_rejected() -> None:
    user = _user(email="ana.garcia@example.com")
    assert "password_too_similar" in _rejection_codes("ana.garcia@example", user)


def test_password_similar_to_the_name_is_rejected() -> None:
    user = _user(name="Ana García")
    assert "password_too_similar" in _rejection_codes("anagarcía1990", user)


def test_common_password_is_rejected() -> None:
    assert "password_too_common" in _rejection_codes("qwerty123456", _user())


PASSWORD = "Kq7#mZ2!vR9p"
SHA1 = hashlib.sha1(PASSWORD.encode()).hexdigest().upper()


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode()

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _record(
    monkeypatch: pytest.MonkeyPatch, body: str = "", error: Exception | None = None
) -> list[tuple[urllib.request.Request, float]]:
    sent: list[tuple[urllib.request.Request, float]] = []

    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        sent.append((request, timeout))
        if error is not None:
            raise error
        return _FakeResponse(body)

    monkeypatch.setattr("apps.accounts.password_validation.urllib.request.urlopen", fake_urlopen)
    return sent


def _serve(
    monkeypatch: pytest.MonkeyPatch, body: str = "", error: Exception | None = None
) -> list[tuple[urllib.request.Request, float]]:
    monkeypatch.setattr(django_settings, "PWNED_PASSWORDS_ENABLED", True)
    return _record(monkeypatch, body, error)


def test_pwned_password_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _serve(monkeypatch, f"0123456789ABCDEF0123456789ABCDEF012:7\r\n{SHA1[5:]}:3\r\n")

    with pytest.raises(ValidationError) as excinfo:
        PwnedPasswordValidator().validate(PASSWORD)
    assert excinfo.value.code == "password_pwned"


@pytest.mark.parametrize(
    "body",
    [
        pytest.param("0123456789ABCDEF0123456789ABCDEF012:7\r\n", id="absent"),
        pytest.param(f"{SHA1[5:]}:0\r\n", id="padding-with-zero-count"),
    ],
)
def test_password_absent_or_padding_only_is_accepted(
    monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    _serve(monkeypatch, body)

    PwnedPasswordValidator().validate(PASSWORD)


@override_settings(PWNED_PASSWORDS_TIMEOUT_SECONDS=0.5)
def test_only_the_first_five_characters_of_the_hash_are_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _serve(monkeypatch)

    PwnedPasswordValidator().validate(PASSWORD)

    ((request, timeout),) = sent
    assert request.full_url == f"https://api.pwnedpasswords.com/range/{SHA1[:5]}"
    assert request.get_header("Add-padding") == "true"
    assert timeout == 0.5


@pytest.mark.parametrize(
    ("error", "body"),
    [
        pytest.param(TimeoutError(), "", id="timeout"),
        pytest.param(urllib.error.URLError("unreachable"), "", id="network"),
        pytest.param(None, f"{SHA1[5:]}:not-a-number\r\n", id="malformed"),
        pytest.param(http.client.IncompleteRead(b"partial"), "", id="cut-response"),
    ],
)
def test_service_failure_accepts_and_logs_a_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    error: Exception | None,
    body: str,
) -> None:
    _serve(monkeypatch, body, error)

    with caplog.at_level(logging.WARNING, logger="apps.accounts.password_validation"):
        PwnedPasswordValidator().validate(PASSWORD)

    assert any("Pwned Passwords check skipped" in r.getMessage() for r in caplog.records)
    assert PASSWORD not in caplog.text and SHA1 not in caplog.text


def test_disabled_validator_makes_no_request(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = _serve(monkeypatch, f"{SHA1[5:]}:3\r\n")
    monkeypatch.setattr(django_settings, "PWNED_PASSWORDS_ENABLED", False)

    PwnedPasswordValidator().validate(PASSWORD)

    assert sent == []


def test_help_text_mentions_breaches() -> None:
    assert "breach" in PwnedPasswordValidator().get_help_text()


def test_pwned_check_is_part_of_the_project_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    _serve(monkeypatch, f"{SHA1[5:]}:3\r\n")

    assert "password_pwned" in _rejection_codes(PASSWORD, _user())


def test_the_test_suite_never_queries_the_service(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = _record(monkeypatch, f"{SHA1[5:]}:3\r\n")

    validate_password(PASSWORD, user=_user())

    assert sent == []


def test_service_is_enabled_by_default() -> None:
    assert project_settings.PWNED_PASSWORDS_ENABLED is True
