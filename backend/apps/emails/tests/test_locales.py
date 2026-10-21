import pytest

from apps.emails import locales


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("es", "es"),
        ("pt-BR", "pt-BR"),
        ("pt-br", "pt-BR"),
        ("pt_BR", "pt-BR"),
        ("EN", "en"),
        (" en ", "en"),
        (None, "es"),
        ("", "es"),
        ("fr", "es"),
        ("pt", "es"),
        ("es-MX", "es"),
    ],
)
def test_a_language_is_normalized_to_a_supported_one(value: str | None, expected: str) -> None:
    assert locales.normalize(value) == expected


def test_the_supported_languages_and_the_default() -> None:
    assert locales.SUPPORTED == ("es", "pt-BR", "en")
    assert locales.DEFAULT == "es"
