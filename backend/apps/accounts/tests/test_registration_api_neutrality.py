from collections.abc import Callable
from typing import Any

import pytest
from django.test import Client

from apps.accounts import registration
from apps.accounts.models import PendingRegistration, PhantomProcess
from apps.accounts.tests.factories import make_pending, make_user
from apps.consents.models import Terms
from apps.consents.tests.factories import publish_version

pytestmark = pytest.mark.django_db

CASES = ["new", "pending", "active_account", "inactive_account"]


@pytest.fixture(autouse=True)
def terms() -> dict[str, Terms]:
    return publish_version(version="1")


def _prepare(case: str) -> str:
    email = f"{case.replace('_', '-')}@example.com"
    if case == "pending":
        make_pending(email)
    elif case == "active_account":
        make_user(email=email)
    elif case == "inactive_account":
        make_user(email=email, is_active=False)
    return email


def _form(email: str) -> dict[str, Any]:
    return {
        "name": "Ana García",
        "birthdate": "1990-05-17",
        "email": email,
        "country": "ES",
        "terms": {"version": "1", "locale": "es", "accepted": True},
    }


def _app(email: str) -> Any:
    return Client(REMOTE_ADDR="192.0.2.1").post(APP, _form(email), content_type="application/json")


def _browser(email: str) -> Any:
    client = Client(enforce_csrf_checks=True, REMOTE_ADDR="192.0.2.2")
    client.get("/_allauth/browser/v1/auth/session")
    token = client.cookies["csrftoken"].value
    return client.post(
        BROWSER, _form(email), content_type="application/json", headers={"X-CSRFToken": token}
    )


APP = "/api/app/v1/registration"
BROWSER = "/api/browser/v1/registration"
ROUTES: dict[str, Callable[[str], Any]] = {"app": _app, "browser": _browser}


def _shape(response: Any) -> tuple[Any, ...]:
    body = dict(response.json())
    public_id = body.pop("public_id", None)
    id_format = (len(public_id), public_id.isascii()) if public_id else None
    cookies = sorted((name, dict(morsel)) for name, morsel in response.cookies.items())
    return response.status_code, body, id_format, dict(response.headers), cookies


@pytest.mark.parametrize("route", ROUTES)
def test_accepted_response_is_the_same_in_every_case(route: str) -> None:
    send = ROUTES[route]
    shapes = {case: _shape(send(_prepare(case))) for case in CASES}

    assert shapes["new"][0] == 202
    for case in CASES:
        assert shapes[case] == shapes["new"], case


@pytest.mark.parametrize("route", ROUTES)
def test_rate_limited_response_is_the_same_in_every_case(route: str) -> None:
    send = ROUTES[route]
    shapes = {}
    for case in CASES:
        email = _prepare(case)
        assert send(email).status_code == 202
        shapes[case] = _shape(send(email))

    assert shapes["new"][0] == 429
    for case in CASES:
        assert shapes[case] == shapes["new"], case


def test_identifier_for_an_email_with_an_account_has_no_registration_behind() -> None:
    email = _prepare("active_account")

    public_id = _app(email).json()["public_id"]
    registration.resolve_registration(public_id)

    assert PhantomProcess.objects.filter(public_id=public_id).exists()
    assert not PendingRegistration.objects.filter(public_id=public_id).exists()
