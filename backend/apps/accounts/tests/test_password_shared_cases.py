import pytest
from django.contrib.auth.password_validation import (
    MinimumLengthValidator,
    NumericPasswordValidator,
    get_default_password_validators,
)
from django.core.exceptions import ValidationError

# Tabla «Casos compartidos de contraseña» de specs/registro-flujo/spec.md (CF-8): el test del
# frontend debe recorrer la misma; si cambia una, cambia la otra.
SHARED_CASES = [
    ("abcdefghijk", False, False),
    ("abcdefghijkl", True, False),
    ("😀" * 11, False, False),
    ("😀" * 12, True, False),
    ("123456789012", True, True),
    ("١٢٣٤٥٦٧٨٩٠١٢", True, True),
    ("²" * 12, True, True),
    ("12345678901a", True, False),
]


def _rejects(validator_type: type, password: str) -> bool:
    validators = [v for v in get_default_password_validators() if isinstance(v, validator_type)]
    assert len(validators) == 1, f"{validator_type.__name__} is not configured once"
    try:
        validators[0].validate(password)
    except ValidationError:
        return True
    return False


@pytest.mark.parametrize(("password", "long_enough", "only_digits"), SHARED_CASES)
def test_server_rules_match_the_shared_cases(
    password: str, long_enough: bool, only_digits: bool
) -> None:
    assert not _rejects(MinimumLengthValidator, password) == long_enough
    assert _rejects(NumericPasswordValidator, password) == only_digits
