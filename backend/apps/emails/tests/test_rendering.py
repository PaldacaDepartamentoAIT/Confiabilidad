from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError

from apps.emails import rendering

UNICODE_NAME = "Zoë 李 👋"


@pytest.mark.parametrize("placeholder", ["{{ name }}", "{{name}}", "{{  name  }}"])
def test_a_placeholder_is_replaced_by_its_value(placeholder: str) -> None:
    assert rendering.render_text(f"Hola, {placeholder}.", {"name": "Ana"}) == "Hola, Ana."


def test_a_unicode_name_comes_out_identical_in_subject_and_body() -> None:
    values = {"name": UNICODE_NAME}

    subject = rendering.render_text("{{ name }}, tu código", values)
    body = rendering.render_text("Hola, {{ name }}:\nGracias.", values)

    assert subject == f"{UNICODE_NAME}, tu código"
    assert body == f"Hola, {UNICODE_NAME}:\nGracias."


@pytest.mark.parametrize(
    "text",
    ["{{ user.__class__ }}", "{% if name %}x{% endif %}", "{name}", "{{ name|upper }}"],
)
def test_template_syntax_other_than_a_plain_variable_is_left_as_text(text: str) -> None:
    assert rendering.render_text(text, {"name": "Ana", "user": "x"}) == text


def test_a_value_that_looks_like_a_placeholder_is_not_replaced_again() -> None:
    values = {"name": "{{ code }}", "code": "123456"}

    assert rendering.render_text("Hola, {{ name }}", values) == "Hola, {{ code }}"


def test_placeholders_of_the_template_are_listed() -> None:
    assert rendering.placeholders("{{ code }} y {{link}} y {{ code }}") == {"code", "link"}


def test_attribute_access_is_not_a_placeholder() -> None:
    assert rendering.placeholders("{{ user.__class__ }} {{ name|upper }}") == set()


@pytest.mark.parametrize("base", ["https://app.ejemplo.com", "https://app.ejemplo.com/"])
@pytest.mark.parametrize(
    ("purpose", "path"),
    [("registration", "/register/continue"), ("password_reset", "/password-reset/continue")],
)
def test_the_link_carries_the_public_id_in_the_fragment(
    settings: object, base: str, purpose: str, path: str
) -> None:
    settings.FRONTEND_BASE_URL = base  # type: ignore[attr-defined]

    link = rendering.process_link(purpose, "abc_DEF-123")

    assert link == f"https://app.ejemplo.com{path}#abc_DEF-123"


def test_a_link_for_an_unknown_purpose_is_refused() -> None:
    with pytest.raises(ValueError):
        rendering.process_link("newsletter", "abc")


CODE_BODY = "Hola, {{ name }}. Tu código es {{ code }}; vence en {{ expires_in }}. {{ link }}"


def _messages(error: ValidationError) -> str:
    return " | ".join(str(message) for message in error.messages)


@pytest.fixture
def _frontend(settings: object) -> None:
    settings.FRONTEND_BASE_URL = "https://app.ejemplo.com"  # type: ignore[attr-defined]


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize("missing", ["code", "link", "expires_in"])
@pytest.mark.parametrize("kind", ["registration_code", "password_reset_code"])
def test_a_code_template_without_a_required_value_is_rejected(kind: str, missing: str) -> None:
    body = CODE_BODY.replace("{{ " + missing + " }}", "")

    with pytest.raises(ValidationError) as error:
        rendering.validate_template(kind, "Tu código", body)

    assert missing in _messages(error.value)


@pytest.mark.usefixtures("_frontend")
def test_required_values_may_be_in_the_subject() -> None:
    rendering.validate_template(
        "registration_code", "{{ code }} es tu código", CODE_BODY.replace("{{ code }}", "")
    )


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "kind",
    [
        "account_exists",
        "password_reset_done",
        "password_changed",
        "account_disabled",
        "sessions_closed",
    ],
)
def test_a_notice_does_not_accept_code_values(kind: str) -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template(
            kind, "Aviso", "Hola, {{ name }}. Código: {{ code }} {{ link }}"
        )

    assert "code" in _messages(error.value)
    assert "link" in _messages(error.value)


@pytest.mark.usefixtures("_frontend")
def test_unsupported_template_syntax_is_rejected() -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template("account_exists", "Aviso", "Hola, {{ user.__class__ }}")

    assert "user.__class__" in _messages(error.value)


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "address", ["https://otro.com/x", "http://app.ejemplo.com.evil.io", "www.otro.com"]
)
def test_a_link_to_another_domain_is_rejected(address: str) -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template("account_exists", "Aviso", f"Entra en {address} ahora")

    assert address in _messages(error.value)


@pytest.mark.usefixtures("_frontend")
def test_a_link_to_the_application_domain_is_accepted() -> None:
    rendering.validate_template(
        "account_exists", "Aviso", "Entra en https://app.ejemplo.com/login, {{ name }}."
    )


@pytest.mark.usefixtures("_frontend")
def test_every_problem_is_listed_at_once() -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template("registration_code", "Código", "{{ foo }} https://otro.com")

    messages = _messages(error.value)
    for expected in ("foo", "code", "link", "expires_in", "https://otro.com"):
        assert expected in messages


@pytest.mark.django_db
@pytest.mark.usefixtures("_frontend")
def test_an_invalid_template_is_not_saved() -> None:
    from apps.emails.models import EmailTemplate

    template, _ = EmailTemplate.objects.get_or_create(
        kind="account_exists", locale="es", defaults={"subject": "Asunto", "body": "Cuerpo"}
    )
    stored = template.body
    template.body = "Hola, {{ code }}"

    with pytest.raises(ValidationError):
        template.save()

    template.refresh_from_db()
    assert template.body == stored


@pytest.mark.parametrize(
    ("remaining", "expected"),
    [
        (
            timedelta(minutes=9, seconds=40),
            {"es": "9 minutos", "pt-BR": "9 minutos", "en": "9 minutes"},
        ),
        (
            timedelta(minutes=1, seconds=30),
            {"es": "1 minuto", "pt-BR": "1 minuto", "en": "1 minute"},
        ),
        (
            timedelta(seconds=59),
            {"es": "menos de un minuto", "pt-BR": "menos de um minuto", "en": "less than a minute"},
        ),
        (
            timedelta(0),
            {"es": "menos de un minuto", "pt-BR": "menos de um minuto", "en": "less than a minute"},
        ),
        (timedelta(minutes=15), {"es": "15 minutos", "pt-BR": "15 minutos", "en": "15 minutes"}),
    ],
)
def test_the_remaining_time_is_relative_and_rounded_down(
    remaining: timedelta, expected: dict[str, str]
) -> None:
    for locale, phrase in expected.items():
        assert rendering.expires_in(locale, remaining) == phrase


def test_the_remaining_time_never_shows_a_clock_time() -> None:
    for locale in ("es", "pt-BR", "en"):
        phrase = rendering.expires_in(locale, timedelta(hours=2, minutes=3))
        assert ":" not in phrase
        assert phrase.startswith("123 ")
