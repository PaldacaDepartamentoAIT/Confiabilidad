from datetime import date
from io import StringIO

import pytest
from django.contrib.auth import HASH_SESSION_KEY, SESSION_KEY
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.accounts import conf, profile, sessions, throttling
from apps.accounts.models import User, UserSession
from apps.accounts.tests.factories import make_user
from apps.audit.models import EventType, SecurityEvent
from apps.emails.models import OutboundEmail

pytestmark = pytest.mark.django_db


def test_get_profile_returns_only_expected_fields() -> None:
    user = make_user(
        email="ana@example.com",
        name="Ana Pérez",
        birthdate=date(1992, 4, 15),
        country="es",
        language="en",
    )

    data = profile.get_profile(user)

    assert data == profile.ProfileData(
        email="ana@example.com",
        name="Ana Pérez",
        birthdate=date(1992, 4, 15),
        country="ES",
    )


def test_update_profile_partial_changes_record_history_and_audit() -> None:
    user = make_user(
        email="eva@example.com",
        name="Eva Gómez",
        birthdate=date(1990, 5, 10),
        country="ES",
    )
    initial_history = user.history.count()

    updated = profile.update_profile(user, name="  Eva María Gómez  ", country="br")

    user.refresh_from_db()
    assert updated == profile.ProfileData(
        email="eva@example.com",
        name="Eva María Gómez",
        birthdate=date(1990, 5, 10),
        country="BR",
    )
    assert user.name == "Eva María Gómez"
    assert user.country == "BR"
    assert user.birthdate == date(1990, 5, 10)
    assert user.history.count() == initial_history + 1
    assert (
        SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT, success=True).count() == 1
    )


def test_update_profile_without_real_changes_skips_history_and_audit() -> None:
    user = make_user(
        email="luis@example.com",
        name="Luis Díaz",
        birthdate=date(1988, 2, 20),
        country="PT",
    )
    initial_history = user.history.count()

    updated = profile.update_profile(user, name="  Luis Díaz ", country="pt")

    assert updated == profile.ProfileData(
        email="luis@example.com",
        name="Luis Díaz",
        birthdate=date(1988, 2, 20),
        country="PT",
    )
    assert user.history.count() == initial_history
    assert not SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT).exists()


def test_update_profile_preserves_placeholder_zz_only_while_unchanged() -> None:
    user = make_user(name="Usuario sin nombre", birthdate=date(1900, 1, 1), country="ES")
    User.objects.filter(pk=user.pk).update(country="ZZ")
    user.refresh_from_db()
    before_events = SecurityEvent.objects.filter(
        event_type=EventType.PROFILE_EDIT, success=True
    ).count()

    updated = profile.update_profile(user, name="Nombre Real")
    assert updated.country == "ZZ"
    assert updated.name == "Nombre Real"
    assert (
        SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT, success=True).count()
        == before_events + 1
    )

    updated_country = profile.update_profile(user, country="es")
    assert updated_country.country == "ES"

    with pytest.raises(ValidationError) as exc_info:
        profile.update_profile(user, country="ZZ")
    assert "country" in exc_info.value.error_dict


def test_update_profile_rejects_invalid_values_without_saving_or_auditing() -> None:
    user = make_user(name="Ana", birthdate=date(1990, 1, 1), country="ES")

    with pytest.raises(ValidationError) as name_err:
        profile.update_profile(user, name="Ana  Ruiz")
    assert "name" in name_err.value.error_dict

    with pytest.raises(ValidationError) as age_err:
        profile.update_profile(user, birthdate=date.today())
    assert "birthdate" in age_err.value.error_dict

    with pytest.raises(ValidationError) as country_err:
        profile.update_profile(user, country="XX")
    assert "country" in country_err.value.error_dict

    user.refresh_from_db()
    assert user.name == "Ana"
    assert user.birthdate == date(1990, 1, 1)
    assert user.country == "ES"
    assert not SecurityEvent.objects.filter(event_type=EventType.PROFILE_EDIT).exists()


def test_cli_profile_show_and_edit() -> None:
    user = make_user(
        email="cli@example.com",
        name="Cli User",
        birthdate=date(1991, 6, 7),
        country="ES",
    )
    out = StringIO()
    call_command("profile", "show", "--email", " CLI@example.com ", stdout=out)
    shown = out.getvalue()
    assert "email: cli@example.com" in shown
    assert "name: Cli User" in shown
    assert "birthdate: 1991-06-07" in shown
    assert "country: ES" in shown

    edit_out = StringIO()
    call_command(
        "profile",
        "edit",
        "--email",
        "cli@example.com",
        "--name",
        "Cli Updated",
        "--birthdate",
        "1992-07-08",
        "--country",
        "br",
        stdout=edit_out,
    )
    assert "name: Cli Updated" in edit_out.getvalue()
    assert "birthdate: 1992-07-08" in edit_out.getvalue()
    assert "country: BR" in edit_out.getvalue()
    user.refresh_from_db()
    assert user.name == "Cli Updated"
    assert user.birthdate == date(1992, 7, 8)
    assert user.country == "BR"

    with pytest.raises(CommandError):
        call_command("profile", "edit", "--email", "cli@example.com")

    with pytest.raises(CommandError):
        call_command("profile", "edit", "--email", "cli@example.com", "--country", "XX")

    with pytest.raises(CommandError):
        call_command("profile", "edit", "--email", "cli@example.com", "--birthdate", "not-a-date")

    with pytest.raises(CommandError):
        call_command("profile", "show", "--email", "missing@example.com")


def test_password_change_throttle_defaults_settings_and_clear() -> None:
    cache.clear()
    assert conf.password_change_max_failed_attempts() == 5
    assert conf.password_change_attempt_window().total_seconds() == 300
    assert conf.password_change_lockout_duration().total_seconds() == 300

    base = 1000.0
    for offset in range(4):
        verdict = throttling.record_password_change_failure(42, now=base + offset)
        assert verdict.allowed
    assert throttling.check_password_change(42, now=base + 5).allowed

    armed = throttling.record_password_change_failure(42, now=base + 10)
    assert not armed.allowed and armed.retry_after == 300
    blocked = throttling.check_password_change(42, now=base + 20)
    assert not blocked.allowed and blocked.retry_after == 290
    assert throttling.check_password_change(42, now=base + 310).allowed

    throttling.clear_password_change_failures(42)
    assert throttling.check_password_change(42, now=base + 20).allowed

    with (
        override_settings(
            PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS=2,
            PASSWORD_CHANGE_ATTEMPT_WINDOW_MINUTES=10,
            PASSWORD_CHANGE_LOCKOUT_MINUTES=3,
        ),
    ):
        assert conf.password_change_max_failed_attempts() == 2
        assert throttling.record_password_change_failure(99, now=base).allowed
        assert not throttling.record_password_change_failure(99, now=base + 1).allowed
        assert throttling.check_password_change(99, now=base + 2).retry_after == 179

    with override_settings(PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS=0):
        with pytest.raises(ImproperlyConfigured):
            conf.password_change_max_failed_attempts()


def _create_app_session(user: User, key: str) -> str:
    store = sessions._session_store()
    store[SESSION_KEY] = str(user.pk)
    store[HASH_SESSION_KEY] = user.get_session_auth_hash()
    store.save()
    raw_key = str(store.session_key)
    from django.http import HttpRequest

    req = HttpRequest()
    req.session = store
    req.META["REMOTE_ADDR"] = "127.0.0.1"
    req.META["HTTP_USER_AGENT"] = key
    sessions.register_session(req, user)
    return raw_key


def test_password_change_keeps_current_session_closes_others_audits_and_emails() -> None:
    cache.clear()
    user = make_user(
        email="pw@example.com", name="Ana", password="OldStrongPassword1!", language="pt-BR"
    )
    current_key = _create_app_session(user, "current-agent")
    other_key = _create_app_session(user, "other-agent")
    before_pw = SecurityEvent.objects.filter(event_type=EventType.PASSWORD_CHANGE).count()
    before_out = OutboundEmail.objects.count()

    result = profile.change_password(
        user,
        current_password="OldStrongPassword1!",
        new_password="NewStrongPassword2!",
        current_session_key=current_key,
    )
    assert isinstance(result, profile.PasswordChanged)
    assert result.revoked_sessions == 1
    user.refresh_from_db()
    assert user.check_password("NewStrongPassword2!")
    assert sessions.is_session_active(current_key, user.pk)
    assert (
        sessions._session_store(current_key).load()[HASH_SESSION_KEY]
        == user.get_session_auth_hash()
    )
    assert not sessions.is_session_active(other_key, user.pk)
    assert UserSession.objects.filter(user=user).count() == 1
    assert (
        SecurityEvent.objects.filter(event_type=EventType.PASSWORD_CHANGE).count() == before_pw + 1
    )
    assert SecurityEvent.objects.filter(event_type=EventType.LOGOUT).count() >= 1

    queued = list(OutboundEmail.objects.order_by("pk")[before_out:])
    assert [(item.kind, item.locale) for item in queued] == [
        ("password_changed", "pt-BR"),
        ("sessions_closed", "pt-BR"),
    ]

    # Sin otras sesiones abiertas: admite la misma contraseña válida y no envía sessions_closed.
    before_second = OutboundEmail.objects.count()
    same = profile.change_password(
        user,
        current_password="NewStrongPassword2!",
        new_password="NewStrongPassword2!",
        current_session_key=current_key,
    )
    assert isinstance(same, profile.PasswordChanged)
    assert same.revoked_sessions == 0
    assert [item.kind for item in OutboundEmail.objects.order_by("pk")[before_second:]] == [
        "password_changed"
    ]


@override_settings(PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS=2)
def test_password_change_rejections_lockout_and_external_save() -> None:
    cache.clear()
    user = make_user(password="ValidPass1234!")
    key = _create_app_session(user, "agent-1")
    before_pw = SecurityEvent.objects.filter(event_type=EventType.PASSWORD_CHANGE).count()
    before_mail = OutboundEmail.objects.count()

    weak = profile.change_password(
        user, current_password="ValidPass1234!", new_password="123", current_session_key=key
    )
    assert isinstance(weak, profile.PasswordChangeInvalid)
    assert not weak.current_password_incorrect and "password_too_short" in weak.new_password_codes
    assert throttling.check_password_change(user.pk).allowed

    bad_and_missing_new = profile.change_password(
        user, current_password="Wrong!", new_password="", current_session_key=key
    )
    assert isinstance(bad_and_missing_new, profile.PasswordChangeInvalid)
    assert bad_and_missing_new.current_password_incorrect

    second_bad = profile.change_password(
        user,
        current_password="WrongAgain!",
        new_password="ValidNewPass99!",
        current_session_key=key,
    )
    assert (
        isinstance(second_bad, profile.PasswordChangeInvalid)
        and second_bad.current_password_incorrect
    )

    locked = profile.change_password(
        user,
        current_password="ValidPass1234!",
        new_password="ValidNewPass99!",
        current_session_key=key,
    )
    assert isinstance(locked, profile.PasswordChangeLocked) and locked.retry_after > 0
    assert sessions.is_session_active(key, user.pk)
    assert SecurityEvent.objects.filter(event_type=EventType.PASSWORD_CHANGE).count() == before_pw
    assert OutboundEmail.objects.count() == before_mail

    # Guardado externo directo sigue revocando todas las sesiones (RF-010 de inicio-cierre-sesion).
    user.set_password("ExternalChange99!")
    user.save(update_fields=["password"])
    assert not UserSession.objects.filter(user=user).exists()


def test_cli_password_change_keeps_selected_session_and_reports_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache.clear()
    user = make_user(email="clipw@example.com", password="OldCliPassword1!")
    keep_key = _create_app_session(user, "cli-keep")
    drop_key = _create_app_session(user, "cli-drop")

    out = StringIO()
    call_command(
        "profile",
        "change-password",
        "--email",
        "clipw@example.com",
        "--current-password",
        "OldCliPassword1!",
        "--new-password",
        "NewCliPassword2!",
        "--keep-session-key",
        keep_key,
        stdout=out,
    )
    assert "account: clipw@example.com" in out.getvalue()
    assert "revoked_sessions: 1" in out.getvalue()
    assert sessions.is_session_active(keep_key, user.pk)
    assert not sessions.is_session_active(drop_key, user.pk)

    answers = iter(["WrongPass!", "NewCliPassword3!"])
    monkeypatch.setattr("getpass.getpass", lambda _prompt="": next(answers))
    with override_settings(PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS=1):
        with pytest.raises(CommandError, match="incorrect"):
            call_command("profile", "change-password", "--email", "clipw@example.com")
        with pytest.raises(CommandError, match="Wait"):
            call_command(
                "profile",
                "change-password",
                "--email",
                "clipw@example.com",
                "--current-password",
                "NewCliPassword2!",
                "--new-password",
                "NewCliPassword3!",
            )
