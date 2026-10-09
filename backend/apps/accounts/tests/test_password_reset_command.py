from datetime import date, timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client
from django.utils import timezone

from apps.accounts import codes, password_reset, registration
from apps.accounts.management.commands.password_reset import (
    ACCOUNT_ERRORS,
    COMPLETE_ERRORS,
    RESEND_ERRORS,
    VERIFY_ERRORS,
)
from apps.accounts.models import PasswordResetRequest, PendingRegistration, User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user

pytestmark = pytest.mark.django_db

EMAIL = "ana@x.com"
GOOD_PASSWORD = "Kq7#mZ2!vR9p"
COMMAND = "apps.accounts.management.commands.password_reset"


@pytest.fixture(autouse=True)
def user() -> User:
    return make_user(email=EMAIL, name="Ana García")


def _call(*args: str) -> dict[str, str]:
    out = StringIO()
    call_command("password_reset", *args, stdout=out)
    return dict(line.split(": ", 1) for line in out.getvalue().splitlines() if ": " in line)


def _wrong(code: str) -> str:
    return "000000" if code != "000000" else "111111"


def _verified() -> str:
    started = _call("start", "--email", EMAIL)
    _call("verify", started["public_id"], started["code"])
    return started["public_id"]


def _error(*args: str) -> str:
    with pytest.raises(CommandError) as excinfo:
        _call(*args)
    return str(excinfo.value)


def test_start_shows_the_public_id_and_the_code() -> None:
    shown = _call("start", "--email", " Ana@X.com ")

    stored = PasswordResetRequest.objects.get()
    assert shown["public_id"] == stored.public_id
    assert codes.verify_code(
        codes.Purpose.PASSWORD_RESET, stored.public_id, shown["code"], stored.code_hash
    )


@pytest.mark.parametrize("email", ["nobody@x.com", "inactive@x.com"])
def test_start_without_an_eligible_account_says_so(email: str) -> None:
    make_user(email="inactive@x.com", is_active=False)

    assert _error("start", "--email", email) == "No active account with this email."
    assert not PasswordResetRequest.objects.exists()


def test_verify_confirms_the_right_code_and_rejects_a_wrong_one() -> None:
    started = _call("start", "--email", EMAIL)

    assert _error("verify", started["public_id"], _wrong(started["code"])) == "Wrong code."

    out = StringIO()
    call_command("password_reset", "verify", started["public_id"], started["code"], stdout=out)
    assert out.getvalue().splitlines() == [f"public_id: {started['public_id']}", "Code verified."]


VERIFY_REFUSALS = [
    *[refusal for refusal in password_reset.VerifyResult if refusal != "verified"],
    *password_reset.AccountRefusal,
]


@pytest.mark.parametrize("refusal", VERIFY_REFUSALS)
def test_every_verify_refusal_has_its_own_message(
    monkeypatch: pytest.MonkeyPatch, refusal: str
) -> None:
    monkeypatch.setattr(f"{COMMAND}.password_reset.verify", lambda **kwargs: refusal)

    assert _error("verify", "any-id", "123456") == {**VERIFY_ERRORS, **ACCOUNT_ERRORS}[refusal]


def test_resend_keeps_the_public_id_and_shows_a_new_code() -> None:
    started = _call("start", "--email", EMAIL)

    resent = _call("resend", started["public_id"])

    stored = PasswordResetRequest.objects.get()
    assert resent["public_id"] == started["public_id"]
    assert codes.verify_code(
        codes.Purpose.PASSWORD_RESET, stored.public_id, resent["code"], stored.code_hash
    )


@pytest.mark.parametrize("refusal", [*password_reset.ResendRefusal, *password_reset.AccountRefusal])
def test_every_resend_refusal_has_its_own_message(
    monkeypatch: pytest.MonkeyPatch, refusal: str
) -> None:
    monkeypatch.setattr(f"{COMMAND}.password_reset.resend", lambda **kwargs: refusal)

    assert _error("resend", "any-id") == {**RESEND_ERRORS, **ACCOUNT_ERRORS}[refusal]


def test_complete_with_password_shows_the_account() -> None:
    public_id = _verified()

    shown = _call("complete", public_id, "--password", GOOD_PASSWORD)

    assert shown == {"public_id": public_id, "account": EMAIL}
    assert User.objects.get(email=EMAIL).check_password(GOOD_PASSWORD)
    assert not PasswordResetRequest.objects.exists()


def test_complete_asks_for_the_password_without_echo(monkeypatch: pytest.MonkeyPatch) -> None:
    prompts: list[str] = []

    def fake_getpass(prompt: str) -> str:
        prompts.append(prompt)
        return GOOD_PASSWORD

    monkeypatch.setattr(f"{COMMAND}.getpass.getpass", fake_getpass)
    public_id = _verified()

    _call("complete", public_id)

    assert len(prompts) == 1
    assert User.objects.get(email=EMAIL).check_password(GOOD_PASSWORD)


def test_complete_reports_every_broken_password_rule() -> None:
    public_id = _verified()

    message = _error("complete", public_id, "--password", "12345678")

    assert len(message.splitlines()) >= 3
    assert User.objects.get(email=EMAIL).check_password(DEFAULT_PASSWORD)
    assert PasswordResetRequest.objects.exists()


@pytest.mark.parametrize(
    "refusal", [*password_reset.CompleteRefusal, *password_reset.AccountRefusal]
)
def test_every_complete_refusal_has_its_own_message(
    monkeypatch: pytest.MonkeyPatch, refusal: str
) -> None:
    monkeypatch.setattr(f"{COMMAND}.password_reset.complete", lambda **kwargs: refusal)

    message = _error("complete", "any-id", "--password", GOOD_PASSWORD)

    assert message == {**COMPLETE_ERRORS, **ACCOUNT_ERRORS}[refusal]


def test_refusal_messages_are_distinct() -> None:
    for errors in (VERIFY_ERRORS, RESEND_ERRORS, COMPLETE_ERRORS):
        messages = [*errors.values(), *ACCOUNT_ERRORS.values()]
        assert len(set(messages)) == len(messages)


def test_purge_shows_how_many_were_deleted() -> None:
    make_user(email="bea@x.com")
    _call("start", "--email", EMAIL)
    _call("start", "--email", "bea@x.com")
    PasswordResetRequest.objects.filter(user__email="bea@x.com").update(
        created_at=timezone.now() - timedelta(hours=2)
    )

    assert _call("purge") == {"deleted": "1"}
    assert PasswordResetRequest.objects.get().user.email == EMAIL


def test_console_journey_sets_a_password_that_logs_in() -> None:
    started = _call("start", "--email", EMAIL)
    resent = _call("resend", started["public_id"])
    _call("verify", started["public_id"], resent["code"])

    _call("complete", started["public_id"], "--password", GOOD_PASSWORD)

    response = Client().post(
        "/_allauth/app/v1/auth/login",
        data={"email": EMAIL, "password": GOOD_PASSWORD},
        content_type="application/json",
    )
    assert response.status_code == 200


def test_purge_does_not_delete_pending_registrations() -> None:
    _call("start", "--email", EMAIL)
    PasswordResetRequest.objects.update(created_at=timezone.now() - timedelta(hours=2))
    pending = registration.start(
        email="new@x.com", name="Nuevo", birthdate=date(1990, 1, 1), country="ES"
    )
    assert isinstance(pending, registration.Started)
    PendingRegistration.objects.update(created_at=timezone.now() - timedelta(hours=2))

    assert _call("purge") == {"deleted": "1"}
    assert not PasswordResetRequest.objects.exists()
    assert PendingRegistration.objects.get().public_id == pending.public_id
