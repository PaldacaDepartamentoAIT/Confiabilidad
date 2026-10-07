from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts import codes, registration
from apps.accounts.management.commands.registration import VERIFY_ERRORS
from apps.accounts.models import PendingRegistration
from apps.accounts.tests.factories import make_user

pytestmark = pytest.mark.django_db

START = [
    "start",
    "--email",
    "Ana@X.com",
    "--name",
    "Ana García",
    "--birthdate",
    "1990-05-10",
    "--country",
    "es",
]


def _call(*args: str) -> dict[str, str]:
    out = StringIO()
    call_command("registration", *args, stdout=out)
    return dict(line.split(": ", 1) for line in out.getvalue().splitlines() if ": " in line)


def _wrong(code: str) -> str:
    return "000000" if code != "000000" else "111111"


def test_start_shows_the_public_id_and_the_code() -> None:
    shown = _call(*START)

    pending = PendingRegistration.objects.get()
    assert shown["public_id"] == pending.public_id
    assert codes.verify_code(pending.public_id, shown["code"], pending.code_hash)


def test_start_with_an_account_reports_it_and_stores_nothing() -> None:
    make_user(email="ana@x.com")

    with pytest.raises(CommandError, match="already exists"):
        _call(*START)
    assert not PendingRegistration.objects.exists()


def test_start_reports_every_invalid_field() -> None:
    args = [*START[:4], "Ana  García", "--birthdate", "1990-05-10", "--country", "XX"]

    with pytest.raises(CommandError) as excinfo:
        _call(*args)

    assert "name: " in str(excinfo.value) and "country: " in str(excinfo.value)


def test_start_rejects_a_malformed_birthdate() -> None:
    args = [*START[:6], "10/05/1990", "--country", "es"]

    with pytest.raises(CommandError, match="YYYY-MM-DD"):
        _call(*args)


def test_verify_confirms_the_right_code() -> None:
    started = _call(*START)

    shown = _call("verify", started["public_id"], started["code"])

    assert shown["public_id"] == started["public_id"]
    assert PendingRegistration.objects.get().code_validated_at is not None


def test_verify_reports_a_wrong_code() -> None:
    started = _call(*START)

    with pytest.raises(CommandError, match="Wrong code"):
        _call("verify", started["public_id"], _wrong(started["code"]))


@pytest.mark.parametrize("refusal", [r for r in registration.VerifyResult if r != "verified"])
def test_every_verify_refusal_has_its_own_message(
    monkeypatch: pytest.MonkeyPatch, refusal: registration.VerifyResult
) -> None:
    monkeypatch.setattr(
        "apps.accounts.management.commands.registration.registration.verify",
        lambda **kwargs: refusal,
    )

    with pytest.raises(CommandError) as excinfo:
        _call("verify", "any-id", "123456")

    assert str(excinfo.value) == VERIFY_ERRORS[refusal]


def test_resend_keeps_the_public_id_and_shows_a_new_code() -> None:
    started = _call(*START)

    shown = _call("resend", started["public_id"])

    pending = PendingRegistration.objects.get()
    assert shown["public_id"] == started["public_id"] == pending.public_id
    assert codes.verify_code(pending.public_id, shown["code"], pending.code_hash)


def test_resend_reports_a_refusal() -> None:
    with pytest.raises(CommandError, match="Unknown registration"):
        _call("resend", "unknown")


def test_an_action_is_required() -> None:
    with pytest.raises(CommandError):
        call_command("registration")
