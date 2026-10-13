from collections.abc import Generator
from datetime import date
from typing import Any

import pytest

from apps.accounts import registration, signals
from apps.accounts.models import User

pytestmark = pytest.mark.django_db

EMAIL = "ana@x.com"
PASSWORD = "Clave-segura-2026!"


@pytest.fixture
def captured() -> Generator[dict[str, list[dict[str, Any]]], None, None]:
    calls: dict[str, list[dict[str, Any]]] = {}
    receivers = {}
    for name in [
        "pending_registration_requested",
        "registration_code_sent",
        "registration_code_verified",
        "account_created",
    ]:
        calls[name] = []

        def receiver(sender: object, _name: str = name, **kwargs: Any) -> None:
            calls[_name].append({k: v for k, v in kwargs.items() if k != "signal"})

        receivers[name] = receiver
        getattr(signals, name).connect(receiver, weak=False)
    yield calls
    for name, receiver in receivers.items():
        getattr(signals, name).disconnect(receiver)


def _start() -> registration.Started:
    result = registration.start(email=EMAIL, name="Ana", birthdate=date(1990, 1, 1), country="ES")
    assert isinstance(result, registration.Started)
    return result


def test_start_emits_pending_request_and_code_sent(
    captured: dict[str, list[dict[str, Any]]],
) -> None:
    _start()
    assert captured["pending_registration_requested"] == [{"email": EMAIL, "success": True}]
    assert captured["registration_code_sent"] == [{"email": EMAIL, "success": True}]


def test_start_for_existing_account_emits_refused_request(
    captured: dict[str, list[dict[str, Any]]],
) -> None:
    User.objects.create_user(EMAIL, PASSWORD, name="Ana", birthdate=date(1990, 1, 1), country="ES")
    result = registration.start(email=EMAIL, name="Ana", birthdate=date(1990, 1, 1), country="ES")
    assert isinstance(result, registration.AccountExists)
    assert captured["pending_registration_requested"] == [{"email": EMAIL, "success": False}]


def test_resend_emits_code_sent(captured: dict[str, list[dict[str, Any]]]) -> None:
    started = _start()
    captured["registration_code_sent"].clear()
    registration.resend(public_id=started.public_id)
    assert captured["registration_code_sent"] == [{"email": EMAIL, "success": True}]


def test_verify_emits_success_or_failure(captured: dict[str, list[dict[str, Any]]]) -> None:
    started = _start()
    registration.verify(
        public_id=started.public_id, code="000000" if started.code != "000000" else "111111"
    )
    registration.verify(public_id=started.public_id, code=started.code)
    assert captured["registration_code_verified"] == [
        {"email": EMAIL, "success": False},
        {"email": EMAIL, "success": True},
    ]


def test_complete_emits_account_created(captured: dict[str, list[dict[str, Any]]]) -> None:
    started = _start()
    registration.verify(public_id=started.public_id, code=started.code)
    result = registration.complete(public_id=started.public_id, password=PASSWORD)
    assert isinstance(result, registration.Completed)
    assert captured["account_created"] == [{"email": EMAIL, "success": True}]
