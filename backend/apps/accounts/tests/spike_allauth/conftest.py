import importlib
import re
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from django.conf import settings as django_settings
from django.core import mail
from django.test import Client
from django.urls import clear_url_caches

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
    settings.ACCOUNT_PREVENT_ENUMERATION = True
    # Todas las peticiones de test vienen de 127.0.0.1, así que el límite de allauth de 20
    # registros por minuto e IP se agota con la propia suite; no es objeto del spike.
    settings.ACCOUNT_RATE_LIMITS = {"signup": None}
    return settings


def _rebuild_headless_urls() -> None:
    # allauth registra las rutas de login por código al importar su módulo de URLs, y el urlconf
    # raíz guarda en caché las rutas incluidas; tras cambiar el setting hay que recargar ambos.
    importlib.reload(importlib.import_module("allauth.headless.urls"))
    importlib.reload(importlib.import_module(django_settings.ROOT_URLCONF))
    clear_url_caches()


@pytest.fixture
def login_by_code_settings(spike_settings: Any) -> Iterator[Any]:
    spike_settings.ACCOUNT_LOGIN_BY_CODE_ENABLED = True
    spike_settings.HEADLESS_FRONTEND_URLS = {"account_signup": "https://app.example.com/signup"}
    _rebuild_headless_urls()
    yield spike_settings
    spike_settings.ACCOUNT_LOGIN_BY_CODE_ENABLED = False
    _rebuild_headless_urls()


@pytest.fixture(params=["browser", "app"])
def headless_client(request: pytest.FixtureRequest) -> HeadlessClient:
    return HeadlessClient(kind=request.param)


@pytest.fixture
def unique_email() -> str:
    # allauth limita el reenvío por correo con un cooldown guardado en la caché (Redis), que no
    # se reinicia entre tests; un correo único evita que un test herede el límite de otro.
    return f"spike-{uuid.uuid4().hex[:12]}@example.com"
