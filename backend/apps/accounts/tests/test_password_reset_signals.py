from collections.abc import Generator
from datetime import date
from typing import Any

import pytest

from apps.accounts import password_reset, signals
from apps.accounts.models import User
from apps.accounts.tests.factories import StartedWithCode, make_reset_request

pytestmark = pytest.mark.django_db

EMAIL = "ana@x.com"
PASSWORD = "Clave-segura-2026!"
NEW_PASSWORD = "Otra-clave-segura-2026!"
NAMES = [
    "password_reset_code_sent",
    "password_reset_code_verified",
    "password_reset_completed",
]


@pytest.fixture
def captured() -> Generator[dict[str, list[dict[str, Any]]], None, None]:
    calls: dict[str, list[dict[str, Any]]] = {name: [] for name in NAMES}
    receivers = {}
    for name in NAMES:

        def receiver(sender: object, _name: str = name, **kwargs: Any) -> None:
            calls[_name].append({k: v for k, v in kwargs.items() if k != "signal"})

        receivers[name] = receiver
        getattr(signals, name).connect(receiver, weak=False)
    yield calls
    for name, receiver in receivers.items():
        getattr(signals, name).disconnect(receiver)


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        EMAIL, PASSWORD, name="Ana", birthdate=date(1990, 1, 1), country="ES"
    )


def _start() -> StartedWithCode:
    return make_reset_request(EMAIL)


def test_start_emits_code_sent(user: User, captured: dict[str, list[dict[str, Any]]]) -> None:
    _start()
    assert captured["password_reset_code_sent"] == [{"email": EMAIL, "success": True}]


def test_start_for_unknown_email_emits_the_same_event(
    captured: dict[str, list[dict[str, Any]]],
) -> None:
    password_reset.start(email="nadie@x.com")
    assert captured["password_reset_code_sent"] == [{"email": "nadie@x.com", "success": True}]


def test_resend_emits_code_sent(user: User, captured: dict[str, list[dict[str, Any]]]) -> None:
    started = _start()
    captured["password_reset_code_sent"].clear()
    password_reset.resend(public_id=started.public_id)
    assert captured["password_reset_code_sent"] == [{"email": EMAIL, "success": True}]


def test_verify_emits_success_or_failure(
    user: User, captured: dict[str, list[dict[str, Any]]]
) -> None:
    started = _start()
    wrong = "000000" if started.code != "000000" else "111111"
    password_reset.verify(public_id=started.public_id, code=wrong)
    password_reset.verify(public_id=started.public_id, code=started.code)
    assert captured["password_reset_code_verified"] == [
        {"email": EMAIL, "success": False},
        {"email": EMAIL, "success": True},
    ]


def test_complete_emits_password_reset_completed(
    user: User, captured: dict[str, list[dict[str, Any]]]
) -> None:
    started = _start()
    password_reset.verify(public_id=started.public_id, code=started.code)
    result = password_reset.complete(public_id=started.public_id, password=NEW_PASSWORD)
    assert isinstance(result, password_reset.Completed)
    assert captured["password_reset_completed"] == [{"email": EMAIL, "success": True}]


def test_verify_after_grace_period_emits_failed_verification(
    user: User, captured: dict[str, list[dict[str, Any]]]
) -> None:
    from datetime import timedelta

    from django.utils import timezone

    from apps.accounts import conf
    from apps.accounts.models import PasswordResetRequest

    started = _start()
    PasswordResetRequest.objects.filter(public_id=started.public_id).update(
        code_expires_at=timezone.now() - conf.grace_period() - timedelta(minutes=1)
    )
    captured["password_reset_code_verified"].clear()
    password_reset.verify(public_id=started.public_id, code=started.code)
    assert captured["password_reset_code_verified"] == [{"email": EMAIL, "success": False}]
