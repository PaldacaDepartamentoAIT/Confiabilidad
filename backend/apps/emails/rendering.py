import re
from collections.abc import Mapping

# Solo variables simples: sin atributos, filtros ni etiquetas que alguien pueda usar desde el panel.
_PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def placeholders(text: str) -> set[str]:
    return set(_PLACEHOLDER.findall(text))


def render_text(text: str, values: Mapping[str, str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        return values[name] if name in values else match.group(0)

    return _PLACEHOLDER.sub(_replace, text)
