import pytest

from apps.accounts.api import messages
from apps.emails import locales

CODES = [
    "required",
    "null",
    "blank",
    "invalid",
    "email_domain_without_dot",
    "email_ip_domain",
    "name_empty",
    "name_too_long",
    "name_control_char",
    "name_consecutive_spaces",
    "birthdate_in_future",
    "birthdate_under_minimum_age",
    "country_invalid",
    "terms_not_accepted",
    "document_not_found",
    "wrong_kind",
    "no_current_version",
    "not_current_document",
]


@pytest.mark.parametrize("language", locales.SUPPORTED)
@pytest.mark.parametrize("code", CODES)
def test_every_error_code_has_a_text_in_every_language(code: str, language: str) -> None:
    text = messages.error_text(
        code, language, field="name", params={"max": 1, "years": 1, "days": 1}
    )
    assert text.strip()
    assert "%(" not in text


def test_catalog_has_no_language_gaps() -> None:
    for code, texts in {**messages.ERRORS, **messages.FIELD_ERRORS}.items():
        assert set(texts) == set(locales.SUPPORTED), code


@pytest.mark.parametrize("language", locales.SUPPORTED)
def test_neutral_and_rate_limited_texts_exist(language: str) -> None:
    assert messages.neutral_text(language).strip()
    assert "37" in messages.rate_limited_text(language, seconds=37)


@pytest.mark.parametrize("language", locales.SUPPORTED)
def test_parameters_are_substituted(language: str) -> None:
    assert "150" in messages.error_text("name_too_long", language, params={"max": 150})
    age = messages.error_text(
        "birthdate_under_minimum_age", language, params={"years": 18, "days": 5}
    )
    assert "18" in age and "5" in age


def test_texts_differ_by_language() -> None:
    texts = {messages.error_text("required", language) for language in locales.SUPPORTED}
    assert len(texts) == 3


def test_field_specific_text_overrides_the_generic_one() -> None:
    generic = messages.error_text("invalid", "es", field="name")
    assert messages.error_text("invalid", "es", field="email") != generic
    assert messages.error_text("invalid", "es", field="birthdate") != generic


def test_unknown_code_is_an_error() -> None:
    with pytest.raises(KeyError):
        messages.error_text("no_such_code", "es")
