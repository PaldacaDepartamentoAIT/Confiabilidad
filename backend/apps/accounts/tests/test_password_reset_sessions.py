import secrets
from collections.abc import Callable
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import Client

from apps.accounts import password_reset
from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user

pytestmark = pytest.mark.django_db

APP = "/_allauth/app/v1"
BROWSER = "/_allauth/browser/v1"
NEW_PASSWORD = "Kq7#mZ2!vR9p"
CaptureOnCommit = Callable[..., Any]


@pytest.fixture
def user() -> User:
    # Correo e IP únicos: los contadores de allauth viven en Redis y sobreviven entre ejecuciones.
    return make_user(email=f"reset-{secrets.token_hex(6)}@x.com")


@pytest.fixture
def client() -> Client:
    return Client(REMOTE_ADDR=f"10.{secrets.randbelow(255)}.{secrets.randbelow(255)}.1")


def _app_login(client: Client, email: str, password: str) -> Any:
    return client.post(
        f"{APP}/auth/login",
        data={"email": email, "password": password},
        content_type="application/json",
    )


def _validated(user: User) -> str:
    started = password_reset.start(email=user.email)
    assert isinstance(started, password_reset.Started)
    assert password_reset.verify(public_id=started.public_id, code=started.code) == (
        password_reset.VerifyResult.VERIFIED
    )
    return started.public_id


def _lock_out(client: Client, user: User) -> None:
    for _ in range(5):
        assert _app_login(client, user.email, "wrong-password").status_code != 200
    blocked = _app_login(client, user.email, DEFAULT_PASSWORD)
    assert blocked.status_code != 200
    assert "too_many_login_attempts" in {error["code"] for error in blocked.json()["errors"]}


def test_completing_clears_the_failed_login_counter(
    user: User, client: Client, django_capture_on_commit_callbacks: CaptureOnCommit
) -> None:
    _lock_out(client, user)
    public_id = _validated(user)

    with django_capture_on_commit_callbacks(execute=True):
        result = password_reset.complete(public_id=public_id, password=NEW_PASSWORD)

    assert isinstance(result, password_reset.Completed)
    assert _app_login(client, user.email, NEW_PASSWORD).status_code == 200


def test_a_failed_completion_keeps_the_failed_login_counter(
    user: User, client: Client, django_capture_on_commit_callbacks: CaptureOnCommit
) -> None:
    _lock_out(client, user)
    public_id = _validated(user)

    with django_capture_on_commit_callbacks(execute=True), pytest.raises(ValidationError):
        password_reset.complete(public_id=public_id, password="12345678")

    assert _app_login(client, user.email, DEFAULT_PASSWORD).status_code != 200


def test_sessions_opened_before_completing_stop_authenticating(user: User) -> None:
    browser = Client()
    browser.get(f"{BROWSER}/auth/session")
    assert (
        browser.post(
            f"{BROWSER}/auth/login",
            data={"email": user.email, "password": DEFAULT_PASSWORD},
            content_type="application/json",
            headers={"X-CSRFToken": browser.cookies["csrftoken"].value},
        ).status_code
        == 200
    )
    token = _app_login(Client(), user.email, DEFAULT_PASSWORD).json()["meta"]["session_token"]
    app = Client()
    assert browser.get(f"{BROWSER}/auth/session").status_code == 200
    assert app.get(f"{APP}/auth/session", headers={"X-Session-Token": token}).status_code == 200

    password_reset.complete(public_id=_validated(user), password=NEW_PASSWORD)

    assert browser.get(f"{BROWSER}/auth/session").status_code == 401
    assert app.get(f"{APP}/auth/session", headers={"X-Session-Token": token}).status_code == 401


def test_a_rolled_back_completion_keeps_the_failed_login_counter(
    user: User, client: Client, django_capture_on_commit_callbacks: CaptureOnCommit
) -> None:
    _lock_out(client, user)
    public_id = _validated(user)

    with (
        django_capture_on_commit_callbacks(execute=True),
        pytest.raises(RuntimeError),
        transaction.atomic(),
    ):
        password_reset.complete(public_id=public_id, password=NEW_PASSWORD)
        raise RuntimeError

    assert User.objects.get(pk=user.pk).check_password(DEFAULT_PASSWORD)
    assert _app_login(client, user.email, DEFAULT_PASSWORD).status_code != 200
