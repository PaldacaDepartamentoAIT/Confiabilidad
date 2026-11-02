from collections.abc import Mapping

# Textos por idioma indexados por el código del error, sin catálogos gettext (D-05).
ERRORS: dict[str, dict[str, str]] = {
    "required": {
        "es": "Este campo es obligatorio.",
        "pt-BR": "Este campo é obrigatório.",
        "en": "This field is required.",
    },
    "null": {
        "es": "Este campo es obligatorio.",
        "pt-BR": "Este campo é obrigatório.",
        "en": "This field is required.",
    },
    "blank": {
        "es": "Este campo no puede estar vacío.",
        "pt-BR": "Este campo não pode ficar em branco.",
        "en": "This field cannot be blank.",
    },
    "invalid": {
        "es": "El valor no es válido.",
        "pt-BR": "O valor não é válido.",
        "en": "This value is not valid.",
    },
    "null_characters_not_allowed": {
        "es": "El texto no puede contener caracteres nulos.",
        "pt-BR": "O texto não pode conter caracteres nulos.",
        "en": "The text cannot contain null characters.",
    },
    "surrogate_characters_not_allowed": {
        "es": "El texto contiene caracteres no válidos.",
        "pt-BR": "O texto contém caracteres inválidos.",
        "en": "The text contains invalid characters.",
    },
    "max_length": {
        "es": "El valor es demasiado largo.",
        "pt-BR": "O valor é longo demais.",
        "en": "The value is too long.",
    },
    "email_domain_without_dot": {
        "es": "El dominio del correo debe tener un punto, como dominio.com.",
        "pt-BR": "O domínio do e-mail deve ter um ponto, como dominio.com.",
        "en": "The email domain must contain a dot, as in domain.com.",
    },
    "email_ip_domain": {
        "es": "El dominio del correo no puede ser una dirección IP.",
        "pt-BR": "O domínio do e-mail não pode ser um endereço IP.",
        "en": "The email domain cannot be an IP address.",
    },
    "name_empty": {
        "es": "El nombre no puede estar vacío.",
        "pt-BR": "O nome não pode ficar vazio.",
        "en": "The name cannot be empty.",
    },
    "name_too_long": {
        "es": "El nombre no puede tener más de %(max)d caracteres.",
        "pt-BR": "O nome não pode ter mais de %(max)d caracteres.",
        "en": "The name cannot be longer than %(max)d characters.",
    },
    "name_control_char": {
        "es": "El nombre no puede tener tabuladores, saltos de línea ni caracteres de control.",
        "pt-BR": "O nome não pode ter tabulações, quebras de linha nem caracteres de controle.",
        "en": "The name cannot contain tabs, line breaks or control characters.",
    },
    "name_consecutive_spaces": {
        "es": "El nombre no puede tener espacios seguidos.",
        "pt-BR": "O nome não pode ter espaços seguidos.",
        "en": "The name cannot contain consecutive spaces.",
    },
    "birthdate_in_future": {
        "es": "La fecha de nacimiento no puede ser posterior a hoy.",
        "pt-BR": "A data de nascimento não pode ser posterior a hoje.",
        "en": "The birthdate cannot be later than today.",
    },
    "birthdate_under_minimum_age": {
        "es": "Debes tener al menos %(years)d años y %(days)d días para registrarte.",
        "pt-BR": "Você precisa ter pelo menos %(years)d anos e %(days)d dias para se cadastrar.",
        "en": "You must be at least %(years)d years and %(days)d days old to register.",
    },
    "country_invalid": {
        "es": "Elige un país válido (código ISO de dos letras, como ES).",
        "pt-BR": "Escolha um país válido (código ISO de duas letras, como BR).",
        "en": "Choose a valid country (two-letter ISO code, such as GB).",
    },
    "terms_not_accepted": {
        "es": "Debes aceptar los términos y condiciones.",
        "pt-BR": "Você precisa aceitar os termos e condições.",
        "en": "You must accept the terms and conditions.",
    },
    "document_not_found": {
        "es": "Los términos indicados no existen. Recarga la página y revísalos.",
        "pt-BR": "Os termos indicados não existem. Recarregue a página e revise-os.",
        "en": "The given terms do not exist. Reload the page and review them.",
    },
    "wrong_kind": {
        "es": "El documento indicado no son los términos y condiciones.",
        "pt-BR": "O documento indicado não são os termos e condições.",
        "en": "The given document is not the terms and conditions.",
    },
    "no_current_version": {
        "es": "Ahora mismo no es posible registrarse: no hay términos vigentes.",
        "pt-BR": "No momento não é possível se cadastrar: não há termos vigentes.",
        "en": "Registration is not possible right now: there are no terms in force.",
    },
    "not_current_document": {
        "es": "Los términos han cambiado. Revísalos y acéptalos de nuevo.",
        "pt-BR": "Os termos mudaram. Revise-os e aceite-os novamente.",
        "en": "The terms have changed. Review them and accept them again.",
    },
    # Verificar, reenviar y completar (registro-flujo).
    "wrong_code": {
        "es": "El código no es correcto. Revísalo e inténtalo de nuevo.",
        "pt-BR": "O código não está correto. Verifique-o e tente novamente.",
        "en": "The code is not correct. Check it and try again.",
    },
    "locked": {
        "es": "Has agotado los intentos con este código. Pide uno nuevo.",
        "pt-BR": "Você esgotou as tentativas com este código. Peça um novo.",
        "en": "You have used up the attempts for this code. Request a new one.",
    },
    "code_expired": {
        "es": "El código ha caducado. Pide uno nuevo.",
        "pt-BR": "O código expirou. Peça um novo.",
        "en": "The code has expired. Request a new one.",
    },
    "expired": {
        "es": "El registro ha caducado. Vuelve a empezarlo.",
        "pt-BR": "O cadastro expirou. Comece-o novamente.",
        "en": "The registration has expired. Start it again.",
    },
    "resend_unavailable": {
        "es": "Ahora no se puede enviar otro código.",
        "pt-BR": "No momento não é possível enviar outro código.",
        "en": "Another code cannot be sent right now.",
    },
    "not_found": {
        "es": "El enlace no es válido o ha caducado.",
        "pt-BR": "O link não é válido ou expirou.",
        "en": "The link is not valid or has expired.",
    },
    # Política de contraseñas (RF-022 de procesos-pendientes), con los códigos de sus validadores.
    "password_too_short": {
        "es": "La contraseña debe tener al menos %(min_length)d caracteres.",
        "pt-BR": "A senha deve ter pelo menos %(min_length)d caracteres.",
        "en": "The password must be at least %(min_length)d characters long.",
    },
    "password_too_similar": {
        "es": "La contraseña se parece demasiado a tu nombre o a tu correo.",
        "pt-BR": "A senha é parecida demais com seu nome ou seu e-mail.",
        "en": "The password is too similar to your name or email address.",
    },
    "password_too_common": {
        "es": "Esta contraseña es demasiado común.",
        "pt-BR": "Esta senha é comum demais.",
        "en": "This password is too common.",
    },
    "password_entirely_numeric": {
        "es": "La contraseña no puede tener solo números.",
        "pt-BR": "A senha não pode ter apenas números.",
        "en": "The password cannot be entirely numeric.",
    },
    "password_pwned": {
        "es": "Esta contraseña ha aparecido en filtraciones de datos. Elige otra.",
        "pt-BR": "Esta senha apareceu em vazamentos de dados. Escolha outra.",
        "en": "This password has appeared in data breaches. Choose another one.",
    },
}

FIELD_ERRORS: dict[str, dict[str, str]] = {
    "email:invalid": {
        "es": "Introduce un correo válido, como usuario@dominio.com.",
        "pt-BR": "Informe um e-mail válido, como usuario@dominio.com.",
        "en": "Enter a valid email address, such as user@domain.com.",
    },
    "email:max_length": {
        "es": "El correo no puede tener más de 254 caracteres.",
        "pt-BR": "O e-mail não pode ter mais de 254 caracteres.",
        "en": "The email address cannot be longer than 254 characters.",
    },
    "birthdate:invalid": {
        "es": "Introduce una fecha válida con el formato AAAA-MM-DD.",
        "pt-BR": "Informe uma data válida no formato AAAA-MM-DD.",
        "en": "Enter a valid date in the YYYY-MM-DD format.",
    },
}

_NEUTRAL = {
    "es": (
        "Si puedes registrarte con este correo, recibirás un código en unos minutos. "
        "Revisa también la carpeta de spam."
    ),
    "pt-BR": (
        "Se você puder se cadastrar com este e-mail, receberá um código em alguns minutos. "
        "Verifique também a pasta de spam."
    ),
    "en": (
        "If you can register with this email address, you will receive a code within a few "
        "minutes. Please also check your spam folder."
    ),
}

_RATE_LIMITED = {
    "es": "Has hecho demasiadas solicitudes. Espera %(seconds)d segundos y vuelve a intentarlo.",
    "pt-BR": "Você fez solicitações demais. Aguarde %(seconds)d segundos e tente novamente.",
    "en": "Too many requests. Wait %(seconds)d seconds and try again.",
}


def error_text(
    code: str, language: str, *, field: str = "", params: Mapping[str, object] | None = None
) -> str:
    texts = FIELD_ERRORS.get(f"{field}:{code}") or ERRORS[code]
    text = texts[language]
    return text % dict(params) if params and "%(" in text else text


def neutral_text(language: str) -> str:
    return _NEUTRAL[language]


def rate_limited_text(language: str, *, seconds: int) -> str:
    return _RATE_LIMITED[language] % {"seconds": seconds}
