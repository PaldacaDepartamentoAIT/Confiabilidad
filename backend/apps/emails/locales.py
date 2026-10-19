SUPPORTED = ("es", "pt-BR", "en")
DEFAULT = "es"
LANGUAGE_CHOICES = [("es", "Español"), ("pt-BR", "Português (Brasil)"), ("en", "English")]
_BY_KEY = {code.lower(): code for code in SUPPORTED}


def normalize(value: str | None) -> str:
    # Cualquier idioma que no sea uno de los tres admitidos cae en el idioma por defecto (D-10).
    key = (value or "").strip().replace("_", "-").lower()
    return _BY_KEY.get(key, DEFAULT)
