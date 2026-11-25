import pytest

from apps.accounts.api import messages
from apps.accounts.api.profile_serializers import ProfileUpdateSerializer
from apps.accounts.api.views import _render
from apps.emails import locales


@pytest.mark.parametrize("language", locales.SUPPORTED)
@pytest.mark.parametrize("code", ["email_immutable", "unknown_field", "no_profile_fields"])
def test_profile_serializer_error_codes_exist_in_all_languages(code: str, language: str) -> None:
    assert messages.error_text(code, language).strip()


def test_profile_update_serializer_accepts_partial_and_preserves_zz() -> None:
    serializer = ProfileUpdateSerializer(
        data={"name": "  Ana  ", "language": "es"},
        context={"stored_country": "ZZ"},
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data == {"name": "Ana"}

    keep_zz = ProfileUpdateSerializer(data={"country": "zz"}, context={"stored_country": "ZZ"})
    assert keep_zz.is_valid(), keep_zz.errors
    assert keep_zz.validated_data == {"country": "ZZ"}

    restore_zz = ProfileUpdateSerializer(data={"country": "zz"}, context={"stored_country": "ES"})
    assert not restore_zz.is_valid()
    assert _render(restore_zz.errors, "es")["country"][0]["code"] == "country_invalid"


def test_profile_update_serializer_rejects_email_empty_and_unknown_fields() -> None:
    with_email = ProfileUpdateSerializer(data={"name": "Ana", "email": "other@example.com"})
    assert not with_email.is_valid()
    assert _render(with_email.errors, "en")["email"][0]["code"] == "email_immutable"

    empty = ProfileUpdateSerializer(data={"language": "pt-BR"})
    assert not empty.is_valid()
    assert _render(empty.errors, "pt-BR")["non_field_errors"][0]["code"] == "no_profile_fields"

    unknown = ProfileUpdateSerializer(data={"name": "Ana", "nickname": "anny"})
    assert not unknown.is_valid()
    assert _render(unknown.errors, "es")["nickname"][0]["code"] == "unknown_field"

    bad_fields = ProfileUpdateSerializer(data={"name": "Ana  Luis", "birthdate": "2099-01-01"})
    assert not bad_fields.is_valid()
    assert set(bad_fields.errors) == {"name", "birthdate"}
