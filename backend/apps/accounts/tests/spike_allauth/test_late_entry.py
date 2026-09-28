from dataclasses import dataclass
from typing import Any

import pytest
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.test import RequestFactory

from apps.accounts.models import User
from apps.accounts.tests.spike_allauth.conftest import (
    SPIKE_PASSWORD,
    HeadlessClient,
    pending_flows,
)


@dataclass
class PendingRegistration:
    email: str
    code_confirmed: bool


def _request() -> HttpRequest:
    # En el registro real la conversión ocurre dentro de una vista; aquí se simula su petición
    # con sesión y mensajes, que `confirm_email` necesita.
    request = RequestFactory().post("/")
    SessionMiddleware(lambda r: None).process_request(request)  # type: ignore[arg-type]
    MessageMiddleware(lambda r: None).process_request(request)  # type: ignore[arg-type]
    return request


def _complete_registration(pending: PendingRegistration, password: str) -> User:
    assert pending.code_confirmed
    request = _request()
    adapter = get_adapter(request)
    user = adapter.new_user(request)
    user.email = pending.email
    adapter.set_password(user, password)
    email_address = EmailAddress.objects.add_email(request, user, pending.email)
    adapter.confirm_email(request, email_address)
    assert isinstance(user, User)
    return user


@pytest.mark.django_db
def test_user_converted_through_allauth_can_log_in(
    spike_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    pending = PendingRegistration(email=unique_email, code_confirmed=True)

    _complete_registration(pending, SPIKE_PASSWORD)
    login_status, _ = headless_client.post(
        "/auth/login", {"email": unique_email, "password": SPIKE_PASSWORD}
    )
    session_status, session_body = headless_client.get("/auth/session")

    assert login_status == 200
    assert session_status == 200
    assert session_body["data"]["user"]["email"] == unique_email


@pytest.mark.django_db
def test_user_without_verified_email_cannot_log_in(
    spike_settings: Any, headless_client: HeadlessClient, unique_email: str
) -> None:
    User.objects.create_user(email=unique_email, password=SPIKE_PASSWORD)

    login_status, body = headless_client.post(
        "/auth/login", {"email": unique_email, "password": SPIKE_PASSWORD}
    )

    assert login_status == 401
    assert pending_flows(body) == ["verify_email"]
