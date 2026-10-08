import pytest
from django.core.exceptions import ValidationError

from apps.consents.validators import (
    LOCALES,
    VERSION_MAX_LENGTH,
    validate_content,
    validate_locale,
    validate_version,
)


def test_supported_locales_are_spanish_brazilian_portuguese_and_english() -> None:
    assert set(LOCALES) == {"es", "pt-BR", "en"}


@pytest.mark.parametrize("locale", ["es", "pt-BR", "en"])
def test_supported_locales_are_accepted(locale: str) -> None:
    validate_locale(locale)


@pytest.mark.parametrize("locale", ["pt", "es-ES", "fr", "EN", "pt-br", ""])
def test_other_locales_are_rejected(locale: str) -> None:
    with pytest.raises(ValidationError) as error:
        validate_locale(locale)
    assert error.value.code == "locale_not_supported"


@pytest.mark.parametrize("version", ["1", "2.1", "2026-10", "v1.0-rc", "a" * VERSION_MAX_LENGTH])
def test_valid_versions_are_accepted(version: str) -> None:
    validate_version(version)


@pytest.mark.parametrize(
    "version",
    ["", "a" * (VERSION_MAX_LENGTH + 1), "1 0", " 1", "1_0", "v1/2", "versión", "1\n"],
)
def test_invalid_versions_are_rejected(version: str) -> None:
    with pytest.raises(ValidationError) as error:
        validate_version(version)
    assert error.value.code == "version_invalid"


def test_version_max_length_is_twenty() -> None:
    assert VERSION_MAX_LENGTH == 20


@pytest.mark.parametrize(
    "content",
    [
        "# Terms\n\nPlain **Markdown** text.",
        "See <https://x.com> for details.",
        "Contact <mailto:legal@x.com>.",
        "a < b and c > d",
        "1 <2 and 3> 0",
        "Use the <- arrow",
        "Write to <legal@x.com>.",
        "<https://x.com/path?q=1&r=2#frag>",
        "<ftp://files.x.com>",
        "a < b",
        "<3 hearts",
    ],
)
def test_markdown_without_html_is_accepted(content: str) -> None:
    validate_content(content)


@pytest.mark.parametrize(
    "content",
    [
        "<p>Hello</p>",
        "Text </a>",
        "<br/>",
        "<br />",
        "<img src=x onerror=alert(1)>",
        "<script>alert(1)</script>",
        "<!-- hidden -->",
        "<!DOCTYPE html>",
        "<?xml version='1.0'?>",
        "<DIV class='x'>",
        "<svg/onload=alert(1)>",
        "<img/src=x/onerror=alert(1)>",
        "<details/open/ontoggle=alert(1)>",
        "<x_y onmouseover=alert(1)>hover</x_y>",
        "<x_y autofocus tabindex=1 onfocus=alert(1)></x_y>",
        "<a:b onclick=alert(1)>click</a:b>",
        "<scr\x00ipt>alert(1)</scr\x00ipt>",
        "<![CDATA[x]]>",
        "a<b",
        "</x_y>",
        "<https://x.com onclick=alert(1)>",
        "<a:b>",
    ],
)
def test_content_with_html_is_rejected(content: str) -> None:
    with pytest.raises(ValidationError) as error:
        validate_content(content)
    assert error.value.code == "content_has_html"


@pytest.mark.parametrize("content", ["", "   ", "\n\t"])
def test_empty_content_is_rejected(content: str) -> None:
    with pytest.raises(ValidationError) as error:
        validate_content(content)
    assert error.value.code == "content_empty"
