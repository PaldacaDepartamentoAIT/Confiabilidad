import re
from collections.abc import Mapping
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Solo variables simples: sin atributos, filtros ni etiquetas que alguien pueda usar desde el panel.
_PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def placeholders(text: str) -> set[str]:
    return set(_PLACEHOLDER.findall(text))


def render_text(text: str, values: Mapping[str, str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        return values[name] if name in values else match.group(0)

    return _PLACEHOLDER.sub(_replace, text)


# El identificador va en el fragmento: no viaja al servidor ni queda en registros (D-09).
_PROCESS_PATHS = {
    "registration": "/register/continue",
    "password_reset": "/password-reset/continue",
}


def process_link(purpose: str, public_id: str) -> str:
    path = _PROCESS_PATHS.get(purpose)
    if path is None:
        raise ValueError(_("Unknown process purpose: %(purpose)s") % {"purpose": purpose})
    base = str(settings.FRONTEND_BASE_URL).rstrip("/")
    return f"{base}{path}#{public_id}"


CODE_KINDS = frozenset({"registration_code", "password_reset_code"})
_CODE_VALUES = frozenset({"code", "link", "expires_in"})
_ANY_BRACES = re.compile(r"\{\{(.*?)\}\}|\{%.*?%\}", re.S)
_ADDRESS = re.compile(r"(?:https?://|www\.)[^\s<>\"')]+", re.I)


def allowed_values(kind: str) -> frozenset[str]:
    return frozenset({"name"}) | (_CODE_VALUES if kind in CODE_KINDS else frozenset())


def required_values(kind: str) -> frozenset[str]:
    return _CODE_VALUES if kind in CODE_KINDS else frozenset()


def validate_template(kind: str, subject: str, body: str) -> None:
    text = f"{subject}\n{body}"
    used = placeholders(text)
    problems: list[ValidationError] = []
    for match in _ANY_BRACES.finditer(text):
        if not _PLACEHOLDER.fullmatch(match.group(0)):
            problems.append(
                ValidationError(
                    _("Unsupported template syntax: %(syntax)s"),
                    code="template_syntax",
                    params={"syntax": match.group(0)},
                )
            )
    for name in sorted(used - allowed_values(kind)):
        problems.append(
            ValidationError(
                _("This kind of email does not accept {{ %(name)s }}."),
                code="template_value_not_allowed",
                params={"name": name},
            )
        )
    for name in sorted(required_values(kind) - used):
        problems.append(
            ValidationError(
                _("This kind of email requires {{ %(name)s }}."),
                code="template_value_missing",
                params={"name": name},
            )
        )
    for address in _ADDRESS.findall(text):
        if not _is_application_address(address):
            problems.append(
                ValidationError(
                    _("Links may only point to the application: %(address)s"),
                    code="template_foreign_link",
                    params={"address": address},
                )
            )
    if problems:
        raise ValidationError(problems)


def _is_application_address(address: str) -> bool:
    if not address.lower().startswith(("http://", "https://")):
        address = f"https://{address}"
    host = urlsplit(address).hostname
    application_host = urlsplit(str(settings.FRONTEND_BASE_URL)).hostname
    return host is not None and host == application_host


# Frases del plazo por idioma: (un minuto, varios minutos, menos de un minuto) (D-08).
_EXPIRY_PHRASES = {
    "es": ("1 minuto", "{n} minutos", "menos de un minuto"),
    "pt-BR": ("1 minuto", "{n} minutos", "menos de um minuto"),
    "en": ("1 minute", "{n} minutes", "less than a minute"),
}


def expires_in(locale: str, remaining: timedelta) -> str:
    one, many, under_one = _EXPIRY_PHRASES[locale]
    minutes = int(remaining.total_seconds() // 60)
    if minutes < 1:
        return under_one
    if minutes == 1:
        return one
    return many.format(n=minutes)


# Bloque fijo de los avisos de seguridad: lo añade el sistema y no se edita en el panel (RF-010).
_REPORT_BLOCKS = {
    "es": "Si no fuiste tú, escríbenos a {support} y restablece tu contraseña cuanto antes.",
    "pt-BR": "Se não foi você, escreva para {support} e redefina sua senha o quanto antes.",
    "en": "If this wasn't you, write to {support} and reset your password as soon as possible.",
}


def report_block(locale: str) -> str:
    support = str(settings.EMAIL_SUPPORT_ADDRESS)
    return "\n\n" + _REPORT_BLOCKS[locale].format(support=support)


def compose(
    kind: str, locale: str, subject: str, body: str, values: Mapping[str, str]
) -> tuple[str, str]:
    rendered_body = render_text(body, values)
    if kind not in CODE_KINDS:
        rendered_body += report_block(locale)
    return render_text(subject, values), rendered_body
