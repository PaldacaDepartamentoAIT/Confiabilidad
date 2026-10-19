import json
import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings

BACKEND_DIR = Path(__file__).resolve().parents[3]
SMTP = "django.core.mail.backends.smtp.EmailBackend"
CONSOLE = "django.core.mail.backends.console.EmailBackend"
FEATURE_VARIABLES = [
    "EMAIL_BACKEND",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "EMAIL_USE_SSL",
    "EMAIL_USE_TLS",
    "EMAIL_TIMEOUT",
    "DEFAULT_FROM_EMAIL",
    "EMAIL_SUPPORT_ADDRESS",
    "FRONTEND_BASE_URL",
    "EMAIL_NOTICE_RETRY_HOURS",
    "EMAIL_ACCOUNT_EXISTS_WINDOW_MINUTES",
    "EMAIL_CODE_SECRET",
]
_READ_CONNECTION = (
    "import django, json\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    "from django.core.mail import get_connection\n"
    "c = get_connection()\n"
    "print(json.dumps({'backend': f'{type(c).__module__}.{type(c).__name__}',"
    " 'host': getattr(c, 'host', None), 'port': getattr(c, 'port', None),"
    " 'username': getattr(c, 'username', None), 'password': getattr(c, 'password', None),"
    " 'use_ssl': getattr(c, 'use_ssl', None), 'use_tls': getattr(c, 'use_tls', None),"
    " 'timeout': getattr(c, 'timeout', None), 'from': settings.DEFAULT_FROM_EMAIL}))\n"
)


def _connection(**variables: str) -> dict[str, object]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("EMAIL_") and key != "DEFAULT_FROM_EMAIL"
    }
    env.update(variables, DJANGO_SETTINGS_MODULE="config.settings")
    result = subprocess.run(
        [sys.executable, "-c", _READ_CONNECTION],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    data: dict[str, object] = json.loads(result.stdout.splitlines()[-1])
    return data


def test_the_smtp_provider_is_configured_from_the_environment() -> None:
    connection = _connection(
        EMAIL_BACKEND=SMTP,
        EMAIL_HOST="smtp.ejemplo.com",
        EMAIL_PORT="465",
        EMAIL_HOST_USER="no-responder@notificaciones.ejemplo.com",
        EMAIL_HOST_PASSWORD="secreta",
        EMAIL_USE_SSL="true",
        EMAIL_TIMEOUT="7",
        DEFAULT_FROM_EMAIL="Confiabilidad <no-responder@notificaciones.ejemplo.com>",
    )

    assert connection == {
        "backend": SMTP,
        "host": "smtp.ejemplo.com",
        "port": 465,
        "username": "no-responder@notificaciones.ejemplo.com",
        "password": "secreta",
        "use_ssl": True,
        "use_tls": False,
        "timeout": 7,
        "from": "Confiabilidad <no-responder@notificaciones.ejemplo.com>",
    }


def test_without_a_provider_the_emails_go_to_the_console() -> None:
    assert _connection()["backend"] == CONSOLE


def test_the_sweep_runs_every_thirty_seconds() -> None:
    entries = [
        entry
        for entry in settings.CELERY_BEAT_SCHEDULE.values()
        if entry["task"] == "apps.emails.tasks.dispatch_due"
    ]

    assert [entry["schedule"] for entry in entries] == [30.0]


def test_every_variable_of_the_feature_is_documented() -> None:
    example = (BACKEND_DIR / ".env.example").read_text()

    missing = [name for name in FEATURE_VARIABLES if f"# {name}=" not in example]
    assert missing == []


def test_starttls_on_port_587_can_be_chosen_instead_of_ssl() -> None:
    connection = _connection(
        EMAIL_BACKEND=SMTP, EMAIL_PORT="587", EMAIL_USE_SSL="false", EMAIL_USE_TLS="true"
    )

    assert (connection["port"], connection["use_ssl"], connection["use_tls"]) == (587, False, True)
