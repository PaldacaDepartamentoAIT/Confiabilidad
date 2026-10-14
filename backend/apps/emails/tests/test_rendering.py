import pytest

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
