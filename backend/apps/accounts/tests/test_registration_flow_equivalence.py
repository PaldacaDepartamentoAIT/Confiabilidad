from collections.abc import Callable
from datetime import timedelta
from typing import Any
from unittest import mock

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts import conf, registration
from apps.accounts.models import PendingRegistration, PhantomProcess
from apps.accounts.tests.factories import DEFAULT_PROFILE, make_pending, make_user

pytestmark = pytest.mark.django_db

WRONG = "000000"
PASSWORD = "Kq7#mZ2!vR9p"


def _real(email: str = "ana@x.com") -> str:
    # Registro real cuyo código nunca se acierta.
    started = make_pending(email)
    assert started.code != WRONG
    return started.public_id


def _phantom(email: str = "bea@x.com") -> str:
    # Correo con cuenta: la plaza queda como identificador sin registro detrás.
    make_user(email=email)
    started = registration.start(email=email, **DEFAULT_PROFILE)
    registration.resolve_registration(started.public_id)
    return started.public_id


def _process(public_id: str) -> Any:
    return PendingRegistration.objects.filter(public_id=public_id) or PhantomProcess.objects.filter(
        public_id=public_id
    )


def _pin(public_id: str, **changes: Any) -> None:
    # Fija los instantes para que los temporizadores no dependan de lo que tarda el test.
    _process(public_id).update(**changes)


Step = tuple[int, Any, dict[str, str], dict[str, Any], int]


def _browser() -> Client:
    # Cliente web con CSRF: la consulta de opciones le da la cookie que exigen los POST (D-09).
    client = Client(enforce_csrf_checks=True)
    client.get("/api/browser/v1/registration/options")
    return client


def _post(action: str, body: dict[str, str], browser: Client | None = None) -> Step:
    # `response.headers` no incluye `Set-Cookie`: las cookies se comparan aparte (RF-017).
    client, route = Client(), "app"
    sent: dict[str, str] = {}
    if browser is not None:
        client, route = browser, "browser"
        sent = {"X-CSRFToken": browser.cookies["csrftoken"].value}
    with CaptureQueriesContext(connection) as queries:
        response = client.post(
            f"/api/{route}/v1/registration/{action}",
            body,
            content_type="application/json",
            headers=sent,
        )
    headers = {name: value for name, value in response.headers.items()}
    cookies = {name: (morsel.value, dict(morsel)) for name, morsel in response.cookies.items()}
    return response.status_code, response.json(), headers, cookies, len(queries.captured_queries)


def _journey(public_id: str) -> list[Step]:
    now = timezone.now()
    ident = {"public_id": public_id}
    wrong = {**ident, "code": WRONG}
    browser = _browser()
    steps = []
    _pin(public_id, code_expires_at=now + timedelta(minutes=10), last_sent_at=now)
    steps.append(_post("status", ident, browser))
    steps.append(_post("resend", ident))
    steps.append(_post("verify", wrong, browser))
    for _ in range(4):
        steps.append(_post("verify", wrong))
    steps.append(_post("verify", wrong))
    _pin(public_id, code_expires_at=now + timedelta(minutes=10), last_sent_at=now)
    steps.append(_post("status", ident))
    steps.append(_post("complete", {**wrong, "password": PASSWORD}))
    _pin(public_id, last_sent_at=now - timedelta(minutes=2))
    # Entre el reenvío aceptado y la emisión (que aquí no corre), el estado ya da el plazo completo
    # (RF-006). El reloj se fija para que los segundos no dependan de lo que tarda cada recorrido.
    with mock.patch.object(timezone, "now", return_value=timezone.now()):
        steps.append(_post("resend", ident))
        steps.append(_post("status", ident))
    _pin(public_id, code_expires_at=now + timedelta(minutes=10), last_sent_at=now)
    steps.append(_post("status", ident))
    steps.append(_post("verify", wrong))
    _pin(public_id, resend_count=5, last_sent_at=now - timedelta(minutes=2))
    steps.append(_post("resend", ident))
    _pin(public_id, code_expires_at=now - timedelta(minutes=1))
    steps.append(_post("verify", wrong))
    _pin(public_id, code_expires_at=now - timedelta(minutes=20))
    steps.append(_post("status", ident))
    steps.append(_post("verify", wrong))
    steps.append(_post("resend", ident))
    steps.append(_post("complete", {**wrong, "password": PASSWORD}))
    return steps


def test_a_phantom_and_a_real_registration_answer_the_same_through_the_whole_flow() -> None:
    real, phantom = _journey(_real()), _journey(_phantom())

    assert real == phantom
    assert real[8][1]["locked"] is True
    assert real[11][1]["code_expires_in"] == conf.code_ttl().total_seconds()
    codes = [step[1].get("code", step[0]) for step in real]
    assert codes == [
        200,
        "resend_unavailable",
        *["wrong_code"] * 5,
        "locked",
        200,
        "locked",
        202,
        200,
        200,
        "wrong_code",
        "resend_unavailable",
        "code_expired",
        200,
        "expired",
        "expired",
        "expired",
    ]


def _status(public_id: str) -> int:
    return _post("status", {"public_id": public_id})[0]


@pytest.mark.parametrize(
    ("source", "email"), [(_real, "ana@x.com"), (_phantom, "bea@x.com")], ids=["real", "phantom"]
)
def test_a_repeated_registration_turns_the_old_identifier_into_not_found(
    source: Callable[[str], str], email: str
) -> None:
    old = source(email)
    repeated = registration.start(email=email, **DEFAULT_PROFILE)
    assert _status(old) == 200

    registration.resolve_registration(repeated.public_id)

    assert (_status(old), _status(repeated.public_id)) == (404, 200)


def test_purge_turns_a_phantom_and_a_real_registration_into_not_found_together() -> None:
    real, phantom = _real(), _phantom()
    stale = timezone.now() - timedelta(hours=24, minutes=1)
    _pin(real, code_expires_at=stale)
    _pin(phantom, code_expires_at=stale)
    assert (_status(real), _status(phantom)) == (200, 200)

    registration.purge_stale()

    assert (_status(real), _status(phantom)) == (404, 404)


@pytest.mark.parametrize("public_id", ["unknown", "", "x" * 500, "a\x00b"])
@pytest.mark.parametrize("action", ["status", "verify", "resend", "complete"])
def test_an_unknown_identifier_is_not_found_and_writes_nothing(public_id: str, action: str) -> None:
    body = {"public_id": public_id, "code": WRONG, "password": PASSWORD}
    with CaptureQueriesContext(connection) as queries:
        response = Client().post(
            f"/api/app/v1/registration/{action}", body, content_type="application/json"
        )

    assert response.status_code == 404
    writes = [
        query["sql"]
        for query in queries.captured_queries
        if query["sql"].split(" ")[0] in {"INSERT", "UPDATE", "DELETE"}
    ]
    assert writes == []
    assert not PendingRegistration.objects.exists() and not PhantomProcess.objects.exists()
