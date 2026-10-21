import pytest

from apps.accounts.api.language import request_language


@pytest.mark.parametrize("field", ["pt-BR", "pt_BR", "pt-br", " PT_br ", "es", "en", "EN"])
def test_supported_field_wins_over_header(field: str) -> None:
    expected = {"pt": "pt-BR", "es": "es", "en": "en"}[field.strip()[:2].lower()]
    assert request_language(field, "fr-FR") == expected
    assert request_language(field, "de, en;q=0.9, es;q=0.8") == expected


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("pt-PT", "pt-BR"),
        ("pt", "pt-BR"),
        ("es-MX", "es"),
        ("en-GB", "en"),
        ("fr, en;q=0.8", "en"),
        ("en;q=0.5, pt-PT;q=0.9", "pt-BR"),
        ("de-DE, es-AR;q=0.3", "es"),
    ],
)
def test_header_is_read_by_base_language_in_preference_order(header: str, expected: str) -> None:
    assert request_language(None, header) == expected


@pytest.mark.parametrize("field", [None, "", "fr", "pt-PT", "es-MX", "xx"])
def test_unsupported_field_falls_back_to_the_header(field: str | None) -> None:
    assert request_language(field, "en-US") == "en"


@pytest.mark.parametrize("header", [None, "", "fr, de", "*", "not a header;;q="])
def test_without_field_or_known_header_spanish_is_used(header: str | None) -> None:
    assert request_language(None, header) == "es"
