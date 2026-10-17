import contextlib
import time
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
    "address",
    [
        "https://otro.com/x",
        "http://app.ejemplo.com.evil.io",
        "www.otro.com",
        "evil.com/login",
        "seguridad-app.com",
        "ftp://evil.com/x",
        "https:/evil.com",
        "HTTPS://EVIL.COM",
        "ftp://app.ejemplo.com/x",
        "soporte@evil.com",
    ],
)
def test_a_link_to_another_domain_is_rejected(address: str) -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template("account_exists", "Aviso", f"Entra en {address} ahora")

    # De una dirección de correo se nombra su dominio, que es lo que el cliente convierte en enlace.
    assert address.split("@")[-1] in _messages(error.value)


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "address",
    [
        "https://app.ejemplo.com/login",
        "app.ejemplo.com/login",
        "APP.EJEMPLO.COM",
        "app.ejemplo.com:8000/x",
        "soporte@app.ejemplo.com",
    ],
)
def test_a_link_to_the_application_domain_is_accepted(address: str) -> None:
    rendering.validate_template("account_exists", "Aviso", f"Entra en {address}, {{{{ name }}}}.")


@pytest.mark.usefixtures("_frontend")
def test_abbreviations_with_one_letter_parts_are_not_addresses() -> None:
    rendering.validate_template("account_exists", "Aviso", "Confiabilidad S.A. y C.V., {{ name }}.")


@pytest.mark.usefixtures("_frontend")
def test_every_foreign_address_is_named_and_a_trailing_period_is_not_part_of_it() -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template(
            "account_exists", "Aviso", "Visita evil.com. Luego otro.org/x, {{ name }}."
        )

    messages = _messages(error.value)
    assert "evil.com" in messages and "evil.com." not in messages
    assert "otro.org/x" in messages


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


NOTICE_KINDS = [
    "account_exists",
    "password_reset_done",
    "password_changed",
    "account_disabled",
    "sessions_closed",
]
FOOTER_HINTS = {"es": "restablece", "pt-BR": "redefina", "en": "reset"}


@pytest.fixture
def _support(settings: object) -> None:
    settings.EMAIL_SUPPORT_ADDRESS = "ayuda@ejemplo.com"  # type: ignore[attr-defined]


@pytest.mark.usefixtures("_support")
@pytest.mark.parametrize("locale", ["es", "pt-BR", "en"])
@pytest.mark.parametrize("kind", NOTICE_KINDS)
def test_a_security_notice_ends_with_the_report_block(kind: str, locale: str) -> None:
    subject, body = rendering.compose(kind, locale, "Aviso", "Hola, {{ name }}.", {"name": "Ana"})

    assert subject == "Aviso"
    assert body.startswith("Hola, Ana.")
    footer = body.removeprefix("Hola, Ana.")
    assert "ayuda@ejemplo.com" in footer
    assert FOOTER_HINTS[locale] in footer.lower()
    assert footer == rendering.report_block(locale)


@pytest.mark.usefixtures("_support")
@pytest.mark.parametrize("kind", ["registration_code", "password_reset_code"])
def test_a_code_email_has_no_report_block(kind: str) -> None:
    _, body = rendering.compose(kind, "es", "Código", "Tu código es {{ code }}.", {"code": "1"})

    assert body == "Tu código es 1."


@pytest.mark.usefixtures("_support")
def test_the_report_blocks_differ_by_language() -> None:
    blocks = {rendering.report_block(locale) for locale in ("es", "pt-BR", "en")}

    assert len(blocks) == 3


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize("subject", ["Aviso\nX-Extra: 1", "Aviso\r\nX-Extra: 1", "Aviso\r"])
def test_a_subject_with_line_breaks_is_rejected_with_the_other_problems(subject: str) -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template("account_exists", subject, "{{ foo }}")

    codes = {problem.code for problem in error.value.error_list}
    assert {"subject_newline", "template_value_not_allowed"} <= codes


@pytest.mark.usefixtures("_frontend")
def test_the_body_still_admits_line_breaks() -> None:
    rendering.validate_template("account_exists", "Aviso", "Hola, {{ name }}:\r\n\nLínea dos.")


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    ("address", "named"),
    [
        ("https://evil.com\\@app.ejemplo.com/login", "https://evil.com\\@app.ejemplo.com/login"),
        ("http://evil.com\\@app.ejemplo.com", "http://evil.com\\@app.ejemplo.com"),
        ("https://evil.com＠app.ejemplo.com", "https://evil.com@app.ejemplo.com"),
        ("https://evil.com@app.ejemplo.com/x", "https://evil.com@app.ejemplo.com/x"),
        ("аррӏе.com", "аррӏе.com"),
        ("пример.рф/login", "пример.рф/login"),
        ("evil.рф", "evil.рф"),
        ("evil。com/login", "evil.com/login"),
        ("1.2.3.4/login", "1.2.3.4/login"),
        ("https://[evil.com/x", "https://[evil.com/x"),
    ],
)
def test_a_disguised_or_malformed_address_is_rejected_by_name(address: str, named: str) -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template("account_exists", "Aviso", f"Entra en {address} ahora")

    assert named in _messages(error.value)


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize("hidden", ["\u00ad", "\u200b", "\u2060"])
def test_an_invisible_character_does_not_hide_a_domain(hidden: str) -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template("account_exists", "Aviso", f"Entra en evil{hidden}.com/login")

    assert "evil.com/login" in _messages(error.value)


@pytest.mark.usefixtures("_frontend")
def test_an_invisible_character_does_not_break_an_application_address() -> None:
    rendering.validate_template(
        "account_exists", "Aviso", "Entra en app.ejemplo\u200b.com/login, {{ name }}."
    )


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "hidden",
    ["\u034f", "\u180b", "\u180d", "\u180f", "\ufe00", "\ufe0f", "\U000e0100", "\U000e01ef"],
)
@pytest.mark.parametrize("shape", ["Entra en evil{}.com/login", "Escribe a soporte@evil{}.com"])
def test_an_invisible_mark_does_not_hide_a_domain(hidden: str, shape: str) -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template("account_exists", "Aviso", shape.format(hidden))

    assert "evil.com" in _messages(error.value)


@pytest.mark.usefixtures("_frontend")
def test_an_invisible_mark_does_not_break_an_application_address() -> None:
    rendering.validate_template(
        "account_exists", "Aviso", "Entra en app.ejemplo\u034f.com/login, {{ name }}."
    )


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "address",
    [
        "app.ejemplo\u0332.com/login",
        "https://app.ejemplo\u0305.com/login",
        "app.ejemplo\u20dd.com/login",
        "app.ejemplo\uff9e.com/login",
    ],
)
def test_a_visible_mark_on_the_application_domain_makes_it_another_domain(address: str) -> None:
    with pytest.raises(ValidationError):
        rendering.validate_template(
            "account_exists", "Aviso", f"Entra en {address}, {{{{ name }}}}."
        )


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "text",
    [
        "Entra en evil\u0332.com/login",
        "Escribe a soporte@evil\u0332.com",
        "Entra en สวัสดี.com/login",
        "Entra en evil\u20dd.com/login",
        "Entra en evil\u17b4.com/login",
        "Entra en हिंदी.com/login",
        "Entra en evil\u0332.app.ejemplo.com/login",
        "Entra en evil.c\u0332om/login",
        "Entra en app.ejemplo.com\u0332/login",
        "Entra en app.ejemplo\u17b4.com/login",
        "Entra en x\u0332app.ejemplo.com/login",
        "Entra en evil\U00011001.com/login",
    ],
)
def test_a_combining_mark_is_part_of_the_domain_it_is_written_in(text: str) -> None:
    with pytest.raises(ValidationError):
        rendering.validate_template("account_exists", "Aviso", f"{text}, {{{{ name }}}}.")


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "text",
    [
        "Entra en evil\u2603.com/login",
        "Escribe a soporte@evil\U0001f600.com",
        "Entra en evil\u00a9.com/login",
        "Entra en evil\u0140.com/login",
        "Entra en \U0002ebf0\U0002ebf1.com/login",
        "Entra en \U0001f600app.ejemplo.com/login",
        "Entra en -evil.com/login",
        "Visita evil.com.x",
    ],
)
def test_anything_but_spaces_and_punctuation_is_part_of_the_domain(text: str) -> None:
    with pytest.raises(ValidationError):
        rendering.validate_template("account_exists", "Aviso", f"{text}, {{{{ name }}}}.")


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "text",
    [
        "Entra en «app.ejemplo.com/login»",
        "¿Has entrado en app.ejemplo.com?",
        "Visita col·legi i al·lot",
        "Hola \U0001f600 qué tal. Bien",
        "Ya está la versión 2.10 del servicio",
        "Entra en\u00a0app.ejemplo.com/login",
        "Entra en [app.ejemplo.com/login]",
        "Enlaces: {app.ejemplo.com/login}",
    ],
)
def test_punctuation_and_spaces_around_words_are_not_part_of_a_domain(text: str) -> None:
    rendering.validate_template("account_exists", "Aviso", f"{text}, {{{{ name }}}}.")


@pytest.mark.usefixtures("_frontend")
def test_an_address_found_in_both_readings_is_named_once() -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template("account_exists", "Aviso", "Visita evil.com, {{ name }}.")

    assert len(error.value.messages) == 1


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "word",
    ["a" * 20000, "a-" * 10000, "a." * 10000, "a-." * 7000],
    ids=["letters", "hyphens", "dots", "hyphens-and-dots"],
)
def test_a_long_word_is_validated_quickly(word: str) -> None:
    started = time.monotonic()

    rendering.validate_template("account_exists", "Aviso", f"Hola {word} {{{{ name }}}}")

    assert time.monotonic() - started < 1


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "text",
    [
        "Entra en https://app.ejemplo.com/login{www.evil.com/x ahora",
        "Entra en app.ejemplo.com/login{www.evil.com/x ahora",
        "Entra en https://app.ejemplo.com/login\ufeffwww.evil.com/x ahora",
        "Entra en https://app.ejemplo.com/login\u00bbwww.evil.com/x",
        "Entra en https://app.ejemplo.com/login?a{www.evil.com/x",
        "Entra en https://app.ejemplo.com/login#a{www.evil.com/x",
        "Entra en www.1evil.\u1e9e/login ahora",
        "Escribe a soporte@evil.\u1e9e",
    ],
)
def test_an_address_hidden_after_an_application_link_is_rejected(text: str) -> None:
    with pytest.raises(ValidationError):
        rendering.validate_template("account_exists", "Aviso", f"{text}, {{{{ name }}}}.")


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "address",
    ["https://app.ejemplo.com/login?next=/cuenta", "https://app.ejemplo.com/registro#abc_123"],
)
def test_an_application_link_with_query_or_fragment_is_accepted(address: str) -> None:
    rendering.validate_template("account_exists", "Aviso", f"Entra en {address} {{{{ name }}}}")


@pytest.mark.usefixtures("_frontend")
def test_each_unsupported_block_is_named_in_order_up_to_its_first_closing() -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template(
            "account_exists",
            "Aviso",
            "{{ a.b }} y {{% x }} y {%} y {% if %}}} y {{{ name }}}} y {% sin cierre {{ name }}",
        )

    assert error.value.messages == [
        "Unsupported template syntax: {{ a.b }}",
        "Unsupported template syntax: {{% x }}",
        "Unsupported template syntax: {%} y {% if %}",
        "Unsupported template syntax: {{{ name }}",
    ]


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(("body", "block"), [("{{ a {% b %}", "{% b %}"), ("{{% x %}", "{% x %}")])
def test_an_opening_without_closing_does_not_hide_a_block_of_the_other_kind(
    body: str, block: str
) -> None:
    with pytest.raises(ValidationError) as error:
        rendering.validate_template("account_exists", "Aviso", body)

    assert error.value.messages == [f"Unsupported template syntax: {block}"]


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "body",
    ["{{" * 50000, "{%" * 50000, "{{ a" * 25000, "}}{{" * 25000],
    ids=["openings", "tag-openings", "unclosed-values", "closed-blocks"],
)
def test_template_syntax_is_checked_quickly(body: str) -> None:
    started = time.monotonic()

    with contextlib.suppress(ValidationError):
        rendering.validate_template("account_exists", "Aviso", body)

    assert time.monotonic() - started < 1


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "text",
    [
        "Entra en app.ejemplo.com:evil.com/x ahora",
        "Entra en app.ejemplo.com::evil.com/x ahora",
        "Escribe a soporte@app.ejemplo.com:evil.com",
        "Entra en https://app.ejemplo.com:443:evil.com/x",
        "Entra en app.ejemplo.com:www.evil.com ahora",
        "Entra en https://app.ejemplo.com/login\u0085evil.com/x ahora",
        "Entra en https://app.ejemplo.com\u0085evil.com/login",
        "Entra en //93.184.216/x ahora",
        "Entra en https://app.ejemplo.com/login{//93.184.216/x",
    ],
)
def test_only_a_port_may_follow_the_application_domain(text: str) -> None:
    with pytest.raises(ValidationError):
        rendering.validate_template("account_exists", "Aviso", f"{text}, {{{{ name }}}}.")


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "text",
    [
        "Entra en https://app.ejemplo.com:443/login",
        "Visita https://app.ejemplo.com.",
        "Entra en //app.ejemplo.com/login",
        "Visita //app.ejemplo.com.",
    ],
)
def test_a_port_a_final_sign_or_a_relative_scheme_keep_the_application_link(text: str) -> None:
    rendering.validate_template("account_exists", "Aviso", f"{text} {{{{ name }}}}")


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize("body", ["/" * 100000, "a//" * 33000], ids=["slashes", "double-slashes"])
def test_many_slashes_are_validated_quickly(body: str) -> None:
    started = time.monotonic()

    with contextlib.suppress(ValidationError):
        rendering.validate_template("account_exists", "Aviso", body)

    assert time.monotonic() - started < 1


@pytest.mark.parametrize(
    "text",
    [
        "Entra en https://app.conf\u0131abilidad.com/login ahora",
        "Entra en app.conf\u0130abilidad.com/login ahora",
        "Escribe a soporte@app.conf\u0131abilidad.com",
    ],
)
def test_a_lookalike_letter_does_not_pass_for_the_application_domain(
    settings: object, text: str
) -> None:
    settings.FRONTEND_BASE_URL = "https://app.confiabilidad.com"  # type: ignore[attr-defined]

    with pytest.raises(ValidationError):
        rendering.validate_template("account_exists", "Aviso", f"{text} {{{{ name }}}}")


def test_the_application_domain_in_capitals_is_accepted(settings: object) -> None:
    settings.FRONTEND_BASE_URL = "https://app.confiabilidad.com"  # type: ignore[attr-defined]

    rendering.validate_template(
        "account_exists", "Aviso", "Entra en https://APP.CONFIABILIDAD.COM:443/login {{ name }}"
    )


@pytest.mark.usefixtures("_frontend")
@pytest.mark.parametrize(
    "text",
    [
        "Entra en app.ejemplo.com: verás tu panel",
        "Entra en https://app.ejemplo.com:/login",
        "Visita https://app.ejemplo.com;",
        "Visita https://app.ejemplo.com:",
        "Visita https://app.ejemplo.com!",
        "Visita https://app.ejemplo.com?",
    ],
)
def test_an_empty_port_or_a_final_sign_keep_the_application_link(text: str) -> None:
    rendering.validate_template("account_exists", "Aviso", f"{text} {{{{ name }}}}")


@pytest.mark.usefixtures("_frontend")
def test_accents_are_kept_when_looking_for_addresses() -> None:
    rendering.validate_template("account_exists", "Aviso", "Café y pingüino, {{ name }}.")
