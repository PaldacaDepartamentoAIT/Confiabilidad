from datetime import date, timedelta
from typing import Any
from unittest import mock

import pytest
from allauth.account.models import EmailAddress
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts import codes, registration
from apps.accounts.models import PendingRegistration, PhantomProcess, User
from apps.accounts.tests.factories import (
    StartedWithCode,
    code_sent_to,
    make_pending,
    make_user,
)
from apps.consents import services as consents
from apps.consents.models import UserTerms
from apps.consents.tests.factories import publish_version
from apps.core import fingerprints
from apps.emails.models import OutboundEmail

pytestmark = pytest.mark.django_db

DATA: dict[str, Any] = {"name": "Ana García", "birthdate": date(1990, 5, 10), "country": "ES"}


def _start(email: str = "ana@x.com", **overrides: Any) -> StartedWithCode:
    return make_pending(email, **{**DATA, **overrides})


def test_start_leaves_a_slot_with_the_data_and_returns_only_the_public_id() -> None:
    before = timezone.now()
    result = registration.start(
        email=" Ana@X.com ",
        name=" Ana García ",
        birthdate=date(1990, 5, 10),
        country="es",
        language="pt_br",
    )

    assert result == registration.Started(public_id=result.public_id)
    slot = PhantomProcess.objects.get()
    assert (slot.public_id, slot.purpose, slot.email, slot.code_hash) == (
        result.public_id,
        PhantomProcess.Purpose.REGISTRATION,
        "ana@x.com",
        "",
    )
    assert slot.payload == {
        "name": "Ana García",
        "birthdate": "1990-05-10",
        "country": "ES",
        "language": "pt-BR",
    }
    assert (
        before + timedelta(minutes=15)
        <= slot.code_expires_at
        <= timezone.now() + timedelta(minutes=15)
    )
    assert not PendingRegistration.objects.exists()


def test_start_without_language_uses_the_default_one() -> None:
    registration.start(email="ana@x.com", **DATA)

    payload = PhantomProcess.objects.get().payload
    assert payload is not None and payload["language"] == "es"


def test_start_queues_the_resolution_once_committed(
    django_capture_on_commit_callbacks: Any,
) -> None:
    with mock.patch("celery.current_app.send_task") as send_task:
        with django_capture_on_commit_callbacks() as callbacks:
            result = registration.start(email="ana@x.com", **DATA)
        send_task.assert_not_called()
        for callback in callbacks:
            callback()

    send_task.assert_called_once_with(
        "apps.accounts.tasks.resolve_registration", args=[result.public_id]
    )


def test_start_succeeds_and_warns_when_the_queue_is_down(
    django_capture_on_commit_callbacks: Any, caplog: pytest.LogCaptureFixture
) -> None:
    with mock.patch("celery.current_app.send_task", side_effect=ConnectionError("down")):
        with django_capture_on_commit_callbacks(execute=True):
            result = registration.start(email="ana@x.com", **DATA)

    assert PhantomProcess.objects.get().public_id == result.public_id
    assert any(record.levelname == "WARNING" for record in caplog.records)


def _start_queries(email: str) -> list[str]:
    with CaptureQueriesContext(connection) as queries:
        result = registration.start(email=email, **DATA)
    assert isinstance(result, registration.Started)
    return [query["sql"].split(" ")[0] for query in queries.captured_queries]


@pytest.mark.parametrize("is_active", [True, False])
def test_start_does_the_same_work_whether_or_not_the_email_has_an_account(
    is_active: bool,
) -> None:
    make_user(email="ana@x.com", is_active=is_active)

    assert _start_queries("ANA@x.com") == _start_queries("bea@x.com")


def test_resolved_registration_stores_the_code_only_as_a_hash() -> None:
    before = timezone.now()
    result = _start(" Ana@X.com ")

    pending = PendingRegistration.objects.get()
    assert pending.public_id == result.public_id
    assert (pending.email, pending.failed_attempts, pending.code_validated_at) == (
        "ana@x.com",
        0,
        None,
    )
    assert fingerprints.code_matches(
        codes.Purpose.REGISTRATION, result.public_id, result.code, pending.code_hash
    )
    stored = PendingRegistration.objects.values().get()
    assert result.code not in [str(value) for value in stored.values()]
    assert (
        before + timedelta(minutes=15)
        <= pending.code_expires_at
        <= timezone.now() + timedelta(minutes=15)
    )


@override_settings(REGISTRATION_CODE_TTL_MINUTES=5)
def test_code_lifetime_follows_settings() -> None:
    _start()

    remaining = PendingRegistration.objects.get().code_expires_at - timezone.now()
    assert timedelta(minutes=4) < remaining <= timedelta(minutes=5)


@pytest.mark.parametrize("is_active", [True, False])
def test_start_with_account_returns_a_public_id_and_stores_no_registration(
    is_active: bool,
) -> None:
    make_user(email="ana@x.com", is_active=is_active)

    result = registration.start(email="ANA@x.com", **DATA)
    registration.resolve_registration(result.public_id)

    assert isinstance(result, registration.Started)
    assert not PendingRegistration.objects.exists()
    assert PhantomProcess.objects.get().public_id == result.public_id


@pytest.mark.parametrize("has_account", [False, True])
def test_invalid_data_is_rejected_whether_or_not_the_email_has_an_account(
    has_account: bool,
) -> None:
    if has_account:
        make_user(email="ana@x.com")

    with pytest.raises(ValidationError) as excinfo:
        registration.start(email="ana@x.com", **{**DATA, "country": "XX"})

    assert set(excinfo.value.error_dict) == {"country"}
    assert not PhantomProcess.objects.exists()


def test_malformed_email_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        registration.start(email="not-an-email", **DATA)

    assert set(excinfo.value.error_dict) == {"email"}
    assert not PhantomProcess.objects.exists()


def test_start_deletes_only_the_expired_registration_of_the_same_email() -> None:
    old = _start("ana@x.com")
    other = _start("bea@x.com")
    PendingRegistration.objects.update(created_at=timezone.now() - timedelta(hours=2))

    new = _start("ANA@x.com")

    assert set(PendingRegistration.objects.values_list("public_id", flat=True)) == {
        new.public_id,
        other.public_id,
    }
    assert new.public_id != old.public_id


def test_repeat_keeps_the_data_and_issues_a_new_public_id_and_code() -> None:
    first = _start("ana@x.com")
    PendingRegistration.objects.update(
        failed_attempts=3,
        code_validated_at=timezone.now(),
        code_expires_at=timezone.now() - timedelta(minutes=1),
    )
    created_at = PendingRegistration.objects.get().created_at

    second = _start("ANA@x.com", name="Otra Persona", country="MX")

    pending = PendingRegistration.objects.get()
    assert (pending.name, pending.country, pending.created_at) == ("Ana García", "ES", created_at)
    assert pending.public_id == second.public_id != first.public_id
    assert (pending.failed_attempts, pending.code_validated_at) == (0, None)
    assert pending.code_expires_at > timezone.now() + timedelta(minutes=14)
    assert fingerprints.code_matches(
        codes.Purpose.REGISTRATION, second.public_id, second.code, pending.code_hash
    )
    assert not fingerprints.code_matches(
        codes.Purpose.REGISTRATION, first.public_id, first.code, pending.code_hash
    )
    if first.code != second.code:
        assert not fingerprints.code_matches(
            codes.Purpose.REGISTRATION, second.public_id, first.code, pending.code_hash
        )


def test_repeat_with_invalid_data_is_rejected_and_changes_nothing() -> None:
    first = _start()

    with pytest.raises(ValidationError) as excinfo:
        registration.start(email="ana@x.com", **{**DATA, "country": "XX"})

    assert set(excinfo.value.error_dict) == {"country"}
    assert PendingRegistration.objects.get().public_id == first.public_id
    assert not PhantomProcess.objects.exists()


def test_repeat_after_the_email_got_an_account_keeps_the_first_registration() -> None:
    first = _start()
    make_user(email="ana@x.com")

    again = registration.start(email="ana@x.com", **DATA)
    registration.resolve_registration(again.public_id)

    assert isinstance(again, registration.Started)
    assert PendingRegistration.objects.get().public_id == first.public_id


def test_conflict_not_caused_by_the_email_is_not_treated_as_a_repeat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    taken = _start("bea@x.com").public_id
    monkeypatch.setattr("apps.accounts.registration.codes.generate_public_id", lambda: taken)

    with pytest.raises(IntegrityError):
        make_pending("ana@x.com", **DATA)

    assert not PendingRegistration.objects.filter(email="ana@x.com").exists()


def _wrong(code: str) -> str:
    return "000000" if code != "000000" else "111111"


def _stored() -> PendingRegistration:
    return PendingRegistration.objects.get()


def test_right_code_marks_the_code_as_validated() -> None:
    started = _start()

    assert registration.verify(public_id=started.public_id, code=started.code) == "verified"
    assert _stored().code_validated_at is not None
    assert _stored().failed_attempts == 0


def test_wrong_code_adds_a_failed_attempt() -> None:
    started = _start()

    for expected_attempts in (1, 2):
        result = registration.verify(public_id=started.public_id, code=_wrong(started.code))
        assert result == registration.VerifyResult.WRONG_CODE
        assert _stored().failed_attempts == expected_attempts
    assert _stored().code_validated_at is None


def test_code_of_another_process_is_wrong() -> None:
    ana, bea = _start("ana@x.com"), _start("bea@x.com")
    if ana.code != bea.code:
        result = registration.verify(public_id=ana.public_id, code=bea.code)
        assert result == registration.VerifyResult.WRONG_CODE


@pytest.mark.parametrize(
    ("limit", "settings_override"),
    [(5, {}), (2, {"REGISTRATION_MAX_FAILED_ATTEMPTS": 2})],
)
def test_after_max_failures_even_the_right_code_is_rejected(
    limit: int, settings_override: dict[str, int]
) -> None:
    with override_settings(**settings_override):
        started = _start()
        for _ in range(limit):
            registration.verify(public_id=started.public_id, code=_wrong(started.code))

        result = registration.verify(public_id=started.public_id, code=started.code)

    assert result == registration.VerifyResult.LOCKED
    assert (_stored().failed_attempts, _stored().code_validated_at) == (limit, None)


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        pytest.param({"created_at": 120}, registration.VerifyResult.EXPIRED, id="process-expired"),
        pytest.param(
            {"code_expires_at": 1},
            registration.VerifyResult.CODE_EXPIRED,
            id="code-expired-in-grace",
        ),
    ],
)
def test_expired_code_or_process_is_rejected_without_counting(
    changes: dict[str, int], expected: registration.VerifyResult
) -> None:
    started = _start()
    PendingRegistration.objects.update(
        **{field: timezone.now() - timedelta(minutes=m) for field, m in changes.items()}
    )

    for code in (started.code, _wrong(started.code)):
        assert registration.verify(public_id=started.public_id, code=code) == expected
    assert (_stored().failed_attempts, _stored().code_validated_at) == (0, None)


def test_already_validated_code_rejects_any_code_without_counting() -> None:
    started = _start()
    registration.verify(public_id=started.public_id, code=started.code)

    for code in (started.code, _wrong(started.code)):
        result = registration.verify(public_id=started.public_id, code=code)
        assert result == registration.VerifyResult.ALREADY_VERIFIED
    assert _stored().failed_attempts == 0


def test_unknown_public_id_is_rejected() -> None:
    started = _start()

    result = registration.verify(public_id="unknown", code=started.code)

    assert result == registration.VerifyResult.NOT_FOUND


def _resend(public_id: str) -> StartedWithCode:
    # El código nuevo lo emite la tarea y llega por correo (D-13).
    result = registration.resend(public_id=public_id)
    assert result == registration.Resent(public_id=public_id)
    registration.reissue_code(public_id)
    return StartedWithCode(public_id=public_id, code=code_sent_to(public_id))


def test_resend_keeps_the_public_id_and_replaces_the_code() -> None:
    started = _start()

    resent = _resend(started.public_id)

    assert resent.public_id == started.public_id == _stored().public_id
    assert fingerprints.code_matches(
        codes.Purpose.REGISTRATION, started.public_id, resent.code, _stored().code_hash
    )
    if resent.code != started.code:
        assert registration.verify(public_id=started.public_id, code=started.code) == "wrong_code"


def test_resend_unlocks_a_locked_process() -> None:
    started = _start()
    for _ in range(5):
        registration.verify(public_id=started.public_id, code=_wrong(started.code))

    resent = _resend(started.public_id)

    assert _stored().failed_attempts == 0
    assert registration.verify(public_id=started.public_id, code=resent.code) == "verified"


@override_settings(REGISTRATION_CODE_TTL_MINUTES=5)
def test_resend_renews_an_expired_code_within_the_grace_period() -> None:
    started = _start()
    PendingRegistration.objects.update(code_expires_at=timezone.now() - timedelta(minutes=1))

    resent = _resend(started.public_id)

    remaining = _stored().code_expires_at - timezone.now()
    assert timedelta(minutes=4) < remaining <= timedelta(minutes=5)
    assert registration.verify(public_id=started.public_id, code=resent.code) == "verified"


def test_resend_is_refused_once_the_code_is_validated() -> None:
    started = _start()
    registration.verify(public_id=started.public_id, code=started.code)
    code_hash = _stored().code_hash

    result = registration.resend(public_id=started.public_id)

    assert result == registration.ResendRefusal.ALREADY_VERIFIED
    assert _stored().code_hash == code_hash


def test_resend_is_refused_for_an_expired_process() -> None:
    started = _start()
    PendingRegistration.objects.update(created_at=timezone.now() - timedelta(hours=2))
    code_hash = _stored().code_hash

    result = registration.resend(public_id=started.public_id)

    assert result == registration.ResendRefusal.EXPIRED
    assert _stored().code_hash == code_hash


def test_resend_with_unknown_public_id_is_refused() -> None:
    assert registration.resend(public_id="unknown") == registration.ResendRefusal.NOT_FOUND


GOOD_PASSWORD = "Kq7#mZ2!vR9p"


def _verified(email: str = "ana@x.com") -> StartedWithCode:
    started = _start(email)
    assert registration.verify(public_id=started.public_id, code=started.code) == "verified"
    return started


def _complete(public_id: str, password: str = GOOD_PASSWORD) -> registration.Completed:
    result = registration.complete(public_id=public_id, password=password)
    assert isinstance(result, registration.Completed)
    return result


def test_complete_creates_the_account_and_deletes_the_registration() -> None:
    user = _complete(_verified().public_id).user

    stored = User.objects.get(pk=user.pk)
    assert (stored.email, stored.name, stored.birthdate, stored.country) == (
        "ana@x.com",
        "Ana García",
        date(1990, 5, 10),
        "ES",
    )
    assert stored.check_password(GOOD_PASSWORD)
    address = EmailAddress.objects.get(user=stored)
    assert (address.email, address.verified, address.primary) == ("ana@x.com", True, True)
    assert not PendingRegistration.objects.exists()


@pytest.mark.parametrize("language", ["pt-BR", "en", "es"])
def test_complete_keeps_the_language_of_the_registration(language: str) -> None:
    public_id = _verified().public_id
    PendingRegistration.objects.filter(public_id=public_id).update(language=language)

    user = _complete(public_id).user

    assert User.objects.get(pk=user.pk).language == language


def test_completed_account_can_log_in_through_the_app() -> None:
    _complete(_verified().public_id)

    response = Client().post(
        "/_allauth/app/v1/auth/login",
        data={"email": "ana@x.com", "password": GOOD_PASSWORD},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["meta"]["session_token"]


def test_complete_is_allowed_in_the_grace_period_after_the_code_expired() -> None:
    started = _verified()
    PendingRegistration.objects.update(code_expires_at=timezone.now() - timedelta(minutes=10))

    _complete(started.public_id)

    assert User.objects.filter(email="ana@x.com").exists()


def test_invalid_password_reports_every_broken_rule_and_keeps_the_registration() -> None:
    started = _verified()

    with pytest.raises(ValidationError) as excinfo:
        registration.complete(public_id=started.public_id, password="12345678")

    codes_found = {error.code for error in excinfo.value.error_list}
    assert {
        "password_too_short",
        "password_too_common",
        "password_entirely_numeric",
    } <= codes_found
    assert PendingRegistration.objects.filter(public_id=started.public_id).exists()
    assert not User.objects.exists()


def test_password_similar_to_the_registration_data_is_rejected() -> None:
    started = _verified()

    with pytest.raises(ValidationError) as excinfo:
        registration.complete(public_id=started.public_id, password="anagarcía1990")

    assert "password_too_similar" in {error.code for error in excinfo.value.error_list}


@pytest.mark.parametrize(
    ("prepare", "expected"),
    [
        pytest.param("unverified", registration.CompleteRefusal.CODE_NOT_VERIFIED, id="unverified"),
        pytest.param("expired", registration.CompleteRefusal.EXPIRED, id="expired"),
    ],
)
def test_complete_is_refused_and_keeps_the_registration(
    prepare: str, expected: registration.CompleteRefusal
) -> None:
    started = _start() if prepare == "unverified" else _verified()
    if prepare == "expired":
        PendingRegistration.objects.update(created_at=timezone.now() - timedelta(hours=2))

    assert registration.complete(public_id=started.public_id, password=GOOD_PASSWORD) == expected
    assert PendingRegistration.objects.exists()
    assert not User.objects.exists()


def test_complete_with_unknown_public_id_is_refused() -> None:
    result = registration.complete(public_id="unknown", password=GOOD_PASSWORD)

    assert result == registration.CompleteRefusal.NOT_FOUND


@pytest.mark.parametrize("is_active", [True, False])
def test_email_taken_meanwhile_refuses_and_deletes_the_registration(is_active: bool) -> None:
    started = _verified()
    make_user(email="ana@x.com", is_active=is_active)

    result = registration.complete(public_id=started.public_id, password=GOOD_PASSWORD)

    assert result == registration.CompleteRefusal.ACCOUNT_EXISTS
    assert not PendingRegistration.objects.exists()
    assert User.objects.count() == 1


def test_failure_while_creating_the_account_changes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = _verified()

    def broken_create(**kwargs: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(EmailAddress.objects, "create", broken_create)

    with pytest.raises(RuntimeError):
        registration.complete(public_id=started.public_id, password=GOOD_PASSWORD)

    assert not User.objects.exists()
    assert PendingRegistration.objects.filter(public_id=started.public_id).exists()


def _aged(email: str, **minutes_ago: int) -> str:
    public_id = _start(email).public_id
    PendingRegistration.objects.filter(public_id=public_id).update(
        **{field: timezone.now() - timedelta(minutes=m) for field, m in minutes_ago.items()}
    )
    return public_id


def test_purge_deletes_only_expired_registrations_and_counts_them() -> None:
    fresh = _aged("a@x.com")
    in_grace = _aged("b@x.com", code_expires_at=10)
    _aged("c@x.com", code_expires_at=16)
    _aged("d@x.com", created_at=61)

    assert registration.purge_expired() == 2
    assert set(PendingRegistration.objects.values_list("public_id", flat=True)) == {
        fresh,
        in_grace,
    }


def _aged_slot(email: str, purpose: str = "registration", **minutes_ago: int) -> str:
    make_user(email=email)
    public_id = registration.start(email=email, **DATA).public_id
    registration.resolve_registration(public_id)
    PhantomProcess.objects.filter(public_id=public_id).update(
        purpose=purpose,
        **{field: timezone.now() - timedelta(minutes=m) for field, m in minutes_ago.items()},
    )
    return public_id


def test_purge_also_deletes_the_expired_registration_slots_and_counts_them() -> None:
    fresh = _aged_slot("a@x.com")
    in_grace = _aged_slot("b@x.com", code_expires_at=10)
    _aged_slot("c@x.com", code_expires_at=16)
    _aged_slot("d@x.com", created_at=61)
    reset_slot = _aged_slot("e@x.com", purpose="password_reset", created_at=61)
    _aged("f@x.com", created_at=61)

    assert registration.purge_expired() == 3
    assert set(PhantomProcess.objects.values_list("public_id", flat=True)) == {
        fresh,
        in_grace,
        reset_slot,
    }
    assert not PendingRegistration.objects.exists()


def test_purge_with_nothing_expired_returns_zero() -> None:
    _start()

    assert registration.purge_expired() == 0
    assert PendingRegistration.objects.count() == 1


@override_settings(REGISTRATION_GRACE_MINUTES=5)
def test_purge_follows_the_configured_limits() -> None:
    _aged("b@x.com", code_expires_at=10)

    assert registration.purge_expired() == 1


@pytest.mark.parametrize(
    "expired_by",
    [
        pytest.param({"code_expires_at": 16}, id="grace"),
        pytest.param({"created_at": 61}, id="lifetime"),
    ],
)
def test_expired_registration_of_the_same_email_is_replaced_not_repeated(
    expired_by: dict[str, int],
) -> None:
    old = _start("ana@x.com")
    PendingRegistration.objects.update(
        **{field: timezone.now() - timedelta(minutes=m) for field, m in expired_by.items()}
    )

    new = _start("ANA@X.com", name="Bea Ruiz", country="MX")

    pending = PendingRegistration.objects.get()
    assert (pending.public_id, pending.name, pending.country) == (new.public_id, "Bea Ruiz", "MX")
    assert new.public_id != old.public_id
    assert not pending.is_expired
    assert registration.verify(public_id=new.public_id, code=new.code) == "verified"


@override_settings(REGISTRATION_CODE_TTL_MINUTES=5)
def test_repeat_issues_a_code_with_the_configured_lifetime() -> None:
    _start()
    _start()

    remaining = _stored().code_expires_at - timezone.now()
    assert timedelta(minutes=4) < remaining <= timedelta(minutes=5)


def test_expired_registration_is_replaced_even_with_spaces_around_the_email() -> None:
    _start("ana@x.com")
    PendingRegistration.objects.update(code_expires_at=timezone.now() - timedelta(minutes=16))

    new = _start(" ANA@X.com ", name="Bea Ruiz")

    pending = PendingRegistration.objects.get()
    assert (pending.public_id, pending.name) == (new.public_id, "Bea Ruiz")
    assert not pending.is_expired


def _validate(**overrides: Any) -> None:
    registration.validate_registration_data(**{"email": "nueva@x.com", **DATA, **overrides})


def test_valid_data_passes_the_validation_without_queries(
    django_assert_num_queries: Any,
) -> None:
    with django_assert_num_queries(0):
        _validate()


@pytest.mark.parametrize("is_active", [True, False])
def test_an_email_with_an_account_is_not_a_data_error(
    is_active: bool, django_assert_num_queries: Any
) -> None:
    make_user(email="ana@x.com", is_active=is_active)

    with django_assert_num_queries(0):
        _validate(email=" Ana@X.com ")


def test_every_invalid_field_is_reported_at_once() -> None:
    with pytest.raises(ValidationError) as error:
        _validate(email="no-es-correo", name="", birthdate=date(2030, 1, 1), country="ZZ")

    assert set(error.value.error_dict) == {"email", "name", "birthdate", "country"}
    assert all(e.code != "email_has_account" for e in error.value.error_dict["email"])


def test_the_data_is_normalized_before_it_is_validated() -> None:
    _validate(email="  Nueva@X.com ", name="  Ana García ", country=" es ")


TERMS: dict[str, Any] = {"terms_version": "v2", "terms_locale": "pt-BR"}


def test_start_keeps_the_accepted_terms_document_in_the_slot() -> None:
    registration.start(email="ana@x.com", **DATA, **TERMS)

    payload = PhantomProcess.objects.get().payload
    assert payload is not None
    assert (payload["terms_version"], payload["terms_locale"]) == ("v2", "pt-BR")


def test_new_registration_stores_the_accepted_terms_document_and_sends_the_code() -> None:
    started = _start("ana@x.com", **TERMS)

    pending = PendingRegistration.objects.get()
    assert (pending.public_id, pending.terms_version, pending.terms_locale) == (
        started.public_id,
        "v2",
        "pt-BR",
    )


def test_registration_started_without_terms_document_stores_it_empty() -> None:
    _start("ana@x.com")

    pending = PendingRegistration.objects.get()
    assert (pending.terms_version, pending.terms_locale) == ("", "")


def test_repeat_keeps_the_terms_document_of_the_first_registration() -> None:
    _start("ana@x.com", **TERMS)

    _start("ANA@x.com", terms_version="v3", terms_locale="en")

    pending = PendingRegistration.objects.get()
    assert (pending.terms_version, pending.terms_locale) == ("v2", "pt-BR")


@pytest.mark.parametrize("is_active", [True, False])
def test_start_with_terms_and_an_account_stores_no_registration(is_active: bool) -> None:
    make_user(email="ana@x.com", is_active=is_active)

    result = registration.start(email="ana@x.com", **DATA, **TERMS)
    registration.resolve_registration(result.public_id)

    assert not PendingRegistration.objects.filter(public_id=result.public_id).exists()
    notices = OutboundEmail.objects.filter(kind="account_exists", recipient="ana@x.com")
    assert notices.count() == (1 if is_active else 0)


def _verified_with_terms(version: str, locale: str = "es") -> StartedWithCode:
    started = _start("ana@x.com", terms_version=version, terms_locale=locale)
    assert registration.verify(public_id=started.public_id, code=started.code) == "verified"
    return started


def test_complete_accepts_the_stored_terms_document_with_the_completion_date() -> None:
    documents = publish_version(version="v2")
    started = _verified_with_terms("v2", "pt-BR")
    assert not UserTerms.objects.exists()
    before = timezone.now()

    user = _complete(started.public_id).user

    acceptance = UserTerms.objects.get()
    assert (acceptance.user, acceptance.terms) == (user, documents["pt-BR"])
    assert acceptance.terms_accepted_at >= before


def test_complete_with_terms_no_longer_in_force_creates_the_account_without_acceptance() -> None:
    publish_version(version="old", published_at=timezone.now() - timedelta(days=3))
    started = _verified_with_terms("old")
    publish_version(version="new")

    _complete(started.public_id)

    assert User.objects.filter(email="ana@x.com").exists()
    assert not UserTerms.objects.exists()


def test_complete_with_a_deleted_terms_document_creates_the_account_without_acceptance() -> None:
    documents = publish_version(version="v2")
    started = _verified_with_terms("v2")
    documents["es"].delete()

    _complete(started.public_id)

    assert User.objects.filter(email="ana@x.com").exists()
    assert not UserTerms.objects.exists()


def test_complete_without_stored_terms_creates_the_account_without_acceptance() -> None:
    publish_version(version="v2")
    started = _verified()

    _complete(started.public_id)

    assert User.objects.filter(email="ana@x.com").exists()
    assert not UserTerms.objects.exists()


def test_acceptance_of_a_deleted_account_with_the_same_email_is_kept() -> None:
    publish_version(version="v2")
    old_user = make_user(email="ana@x.com")
    old = consents.accept_terms(old_user, version="v2", locale="es")
    old_user.delete()
    started = _verified_with_terms("v2")
    assert UserTerms.objects.count() == 1

    user = _complete(started.public_id).user

    old.refresh_from_db()
    assert old.user is None
    assert UserTerms.objects.filter(user=user).count() == 1


def test_failure_after_the_acceptance_leaves_neither_account_nor_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publish_version(version="v2")
    started = _verified_with_terms("v2")

    def broken_delete(self: PendingRegistration, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(PendingRegistration, "delete", broken_delete)

    with pytest.raises(RuntimeError):
        registration.complete(public_id=started.public_id, password=GOOD_PASSWORD)

    assert not User.objects.exists()
    assert not UserTerms.objects.exists()
