from django.utils.translation.trans_real import parse_accept_lang_header

from apps.emails import locales

_BY_KEY = {code.lower(): code for code in locales.SUPPORTED}
_BY_BASE = {code.split("-")[0].lower(): code for code in locales.SUPPORTED}


def request_language(field: str | None, accept_language: str | None) -> str:
    # El campo manda porque el idioma se guarda en la cuenta; la cabecera es el respaldo (S-20).
    chosen = _BY_KEY.get((field or "").strip().replace("_", "-").lower())
    if chosen is not None:
        return chosen
    for tag, _quality in parse_accept_lang_header(accept_language or ""):
        base = _BY_BASE.get(tag.split("-")[0])
        if base is not None:
            return base
    return locales.DEFAULT
