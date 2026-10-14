import re
from collections.abc import Mapping

from django.conf import settings
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
