import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

LOCALES = ("es", "pt-BR", "en")
VERSION_MAX_LENGTH = 20
_VERSION_PATTERN = re.compile(rf"[A-Za-z0-9.-]{{1,{VERSION_MAX_LENGTH}}}")
# Etiquetas, comentarios y declaraciones HTML; deja pasar los enlaces automáticos de Markdown
# (<https://…>) y los signos sueltos (a < b).
_HTML_PATTERN = re.compile(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^>]*)?/?>|<!--|<![A-Za-z]|<\?")


def validate_locale(value: str) -> None:
    if value not in LOCALES:
        raise ValidationError(
            _("Unsupported language: %(value)s."),
            code="locale_not_supported",
            params={"value": value},
        )


def validate_version(value: str) -> None:
    if not _VERSION_PATTERN.fullmatch(value):
        raise ValidationError(
            _("Version must have 1 to %(max)d characters: letters, digits, dots or hyphens."),
            code="version_invalid",
            params={"max": VERSION_MAX_LENGTH},
        )


def validate_content(value: str) -> None:
    if not value.strip():
        raise ValidationError(_("Content cannot be empty."), code="content_empty")
    if _HTML_PATTERN.search(value):
        raise ValidationError(_("Content cannot contain HTML."), code="content_has_html")
