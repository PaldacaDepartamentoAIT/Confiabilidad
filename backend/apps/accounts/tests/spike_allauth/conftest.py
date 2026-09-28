import re
import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest
from django.core import mail
from django.test import Client

SPIKE_PASSWORD = "Spike-Passw0rd!"
CODE_PATTERN = re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}$", re.MULTILINE)


@dataclass
class HeadlessClient:
    kind: str
    http: Client = field(default_factory=Client)
    session_token: str | None = None

    @property
    def base(self) -> str:
        return f"/_allauth/{self.kind}/v1"

    def _headers(self) -> dict[str, str]:
        return {"X-Session-Token": self.session_token} if self.session_token else {}

    def post(self, path: str, payload: dict[str, str]) -> tuple[int, dict[str, Any]]:
        resp = self.http.post(
            f"{self.base}{path}",
            data=payload,
            content_type="application/json",
            headers=self._headers(),
        )
        body: dict[str, Any] = resp.json()
        token = body.get("meta", {}).get("session_token")
        if token:
            self.session_token = token
        return resp.status_code, body

    def get(self, path: str) -> tuple[int, dict[str, Any]]:
        resp = self.http.get(f"{self.base}{path}", headers=self._headers())
        body: dict[str, Any] = resp.json()
        return resp.status_code, body

    def fresh(self) -> "HeadlessClient":
        return HeadlessClient(kind=self.kind)


def pending_flows(body: dict[str, Any]) -> list[str]:
    return [flow["id"] for flow in body["data"]["flows"] if flow.get("is_pending")]


def latest_code(email: str) -> str:
    messages = [m for m in mail.outbox if email in m.to]
    assert messages, f"no se envió ningún correo a {email}"
    match = CODE_PATTERN.search(str(messages[-1].body))
    assert match, "el correo no contiene un código"
    return match.group(0)


@pytest.fixture
def spike_settings(settings: Any) -> Any:
    settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
    settings.ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
    return settings


@pytest.fixture(params=["browser", "app"])
def headless_client(request: pytest.FixtureRequest) -> HeadlessClient:
    return HeadlessClient(kind=request.param)


@pytest.fixture
def unique_email() -> str:
    # allauth limita el reenvío por correo con un cooldown guardado en la caché (Redis), que no
    # se reinicia entre tests; un correo único evita que un test herede el límite de otro.
    return f"spike-{uuid.uuid4().hex[:12]}@example.com"
