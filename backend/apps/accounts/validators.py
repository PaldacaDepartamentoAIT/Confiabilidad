import unicodedata
from datetime import date, timedelta
from itertools import pairwise

import pycountry
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

NAME_MAX_LENGTH = 150
MINIMUM_AGE_YEARS = 18
MINIMUM_AGE_EXTRA_DAYS = 5
PLACEHOLDER_COUNTRY = "ZZ"
_ISO_ALPHA_2 = frozenset(country.alpha_2 for country in pycountry.countries)
# Separadores de línea y de párrafo de Unicode: también son "saltos de línea".
_LINE_BREAK_CATEGORIES = {"Cc", "Zl", "Zp"}


_email_format = EmailValidator()


def validate_registration_email(value: str) -> None:
    # Más estricto que la cuenta: un dominio sin punto o una IP nunca recibirá el código (S-08).
    user, _sep, domain = value.rpartition("@")
    if user and domain.startswith("["):
        raise ValidationError(_("Email domain cannot be an IP address."), code="email_ip_domain")
    if user and domain and "." not in domain:
        raise ValidationError(
            _("Email domain must contain a dot."), code="email_domain_without_dot"
        )
    _email_format(value)


def normalize_name(value: str) -> str:
    return value.strip()


def validate_name(value: str) -> None:
    if not value:
        raise ValidationError(_("Name cannot be empty."), code="name_empty")
    errors: list[ValidationError] = []
    if len(value) > NAME_MAX_LENGTH:
        errors.append(
            ValidationError(
                _("Name cannot exceed %(max)d characters."),
                code="name_too_long",
                params={"max": NAME_MAX_LENGTH},
            )
        )
    if any(unicodedata.category(char) in _LINE_BREAK_CATEGORIES for char in value):
        errors.append(
            ValidationError(
                _("Name cannot contain tabs, line breaks or control characters."),
                code="name_control_char",
            )
        )
    if any(a.isspace() and b.isspace() for a, b in pairwise(value)):
        errors.append(
            ValidationError(
                _("Name cannot contain consecutive spaces."),
                code="name_consecutive_spaces",
            )
        )
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise ValidationError(errors)


def minimum_age_date(birthdate: date) -> date:
    year = birthdate.year + MINIMUM_AGE_YEARS
    try:
        eighteenth_birthday = birthdate.replace(year=year)
    except ValueError:
        # Nacido un 29 de febrero y el año de los 18 no es bisiesto: los cumple el 28.
        eighteenth_birthday = date(year, 2, 28)
    return eighteenth_birthday + timedelta(days=MINIMUM_AGE_EXTRA_DAYS)


def validate_birthdate(value: date, today: date | None = None) -> None:
    today = today or timezone.localdate()
    if value > today:
        raise ValidationError(_("Birthdate cannot be in the future."), code="birthdate_in_future")
    if today < minimum_age_date(value):
        raise ValidationError(
            _("You must be at least %(years)d years and %(days)d days old."),
            code="birthdate_under_minimum_age",
            params={"years": MINIMUM_AGE_YEARS, "days": MINIMUM_AGE_EXTRA_DAYS},
        )


def normalize_country(value: str) -> str:
    return value.strip().upper()


def validate_country(value: str, stored_value: str | None = None) -> None:
    if value == PLACEHOLDER_COUNTRY and stored_value == PLACEHOLDER_COUNTRY:
        return
    if value not in _ISO_ALPHA_2:
        raise ValidationError(
            _("Country must be a current ISO 3166-1 alpha-2 code."),
            code="country_invalid",
        )
