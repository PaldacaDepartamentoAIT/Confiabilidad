from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client
from django.utils import timezone

from apps.accounts import codes, registration
from apps.accounts.management.commands.registration import COMPLETE_ERRORS, VERIFY_ERRORS
from apps.accounts.models import PendingRegistration, User
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


GOOD_PASSWORD = "Kq7#mZ2!vR9p"


def _verified() -> str:
    started = _call(*START)
    _call("verify", started["public_id"], started["code"])
    return started["public_id"]


def test_complete_with_the_password_option_creates_the_account() -> None:
    public_id = _verified()

    shown = _call("complete", public_id, "--password", GOOD_PASSWORD)

    assert shown == {"public_id": public_id, "account": "ana@x.com"}
    assert User.objects.get(email="ana@x.com").check_password(GOOD_PASSWORD)
    assert not PendingRegistration.objects.exists()


def test_complete_asks_for_the_password_without_echo(monkeypatch: pytest.MonkeyPatch) -> None:
    prompts: list[str] = []

    def fake_getpass(prompt: str) -> str:
        prompts.append(prompt)
        return GOOD_PASSWORD

    monkeypatch.setattr(
        "apps.accounts.management.commands.registration.getpass.getpass", fake_getpass
    )
    public_id = _verified()

    _call("complete", public_id)

    assert len(prompts) == 1
    assert User.objects.get(email="ana@x.com").check_password(GOOD_PASSWORD)


def test_complete_reports_every_broken_password_rule() -> None:
    public_id = _verified()

    with pytest.raises(CommandError) as excinfo:
        _call("complete", public_id, "--password", "12345678")

    assert len(str(excinfo.value).splitlines()) >= 3
    assert PendingRegistration.objects.exists()


@pytest.mark.parametrize("refusal", list(registration.CompleteRefusal))
def test_every_complete_refusal_has_its_own_message(
    monkeypatch: pytest.MonkeyPatch, refusal: registration.CompleteRefusal
) -> None:
    monkeypatch.setattr(
        "apps.accounts.management.commands.registration.registration.complete",
        lambda **kwargs: refusal,
    )

    with pytest.raises(CommandError) as excinfo:
        _call("complete", "any-id", "--password", GOOD_PASSWORD)

    assert str(excinfo.value) == COMPLETE_ERRORS[refusal]


def test_purge_shows_how_many_were_deleted() -> None:
    _call(*START)
    _call(*[*START[:2], "bea@x.com", *START[3:]])
    PendingRegistration.objects.filter(email="bea@x.com").update(
        created_at=timezone.now() - timedelta(hours=2)
    )

    assert _call("purge") == {"deleted": "1"}
    assert PendingRegistration.objects.get().email == "ana@x.com"


def test_console_journey_creates_an_account_that_logs_in() -> None:
    _call("complete", _verified(), "--password", GOOD_PASSWORD)

    response = Client().post(
        "/_allauth/app/v1/auth/login",
        data={"email": "ana@x.com", "password": GOOD_PASSWORD},
        content_type="application/json",
    )
    assert response.status_code == 200
