import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from apps.consents import conf

BACKEND_DIR = Path(__file__).resolve().parents[3]
_PRINT_SECRET = (
    "import django\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    "print(settings.CONSENT_EMAIL_HASH_SECRET)\n"
)


def _secret_from_environment(**variables: str) -> str:
    env = {key: value for key, value in os.environ.items() if key != "CONSENT_EMAIL_HASH_SECRET"}
    env.update(variables, DJANGO_SETTINGS_MODULE="config.settings")
    result = subprocess.run(
        [sys.executable, "-c", _PRINT_SECRET],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return result.stdout.splitlines()[-1]


def test_secret_defaults_to_secret_key() -> None:
    assert conf.email_hash_secret() == settings.SECRET_KEY


@override_settings(CONSENT_EMAIL_HASH_SECRET="consent-secret")
def test_secret_follows_settings() -> None:
    assert conf.email_hash_secret() == "consent-secret"


@pytest.mark.parametrize("secret", ["", "   "])
def test_empty_secret_is_rejected(secret: str) -> None:
    with override_settings(CONSENT_EMAIL_HASH_SECRET=secret):
        with pytest.raises(ImproperlyConfigured):
            conf.email_hash_secret()


def test_secret_is_read_from_environment_variable() -> None:
    assert _secret_from_environment(CONSENT_EMAIL_HASH_SECRET="from-env") == "from-env"


def test_secret_without_environment_variable_is_secret_key() -> None:
    assert _secret_from_environment(DJANGO_SECRET_KEY="the-key") == "the-key"
