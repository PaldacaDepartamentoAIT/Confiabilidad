import hashlib
import hmac
import re

from django.test import override_settings

from apps.consents.hashing import email_fingerprint


@override_settings(CONSENT_EMAIL_HASH_SECRET="secret")
def test_fingerprint_is_hmac_sha256_of_the_normalized_email() -> None:
    expected = hmac.new(b"secret", b"ana@x.com", hashlib.sha256).hexdigest()

    assert email_fingerprint(" Ana@X.com ") == expected


def test_fingerprint_is_64_hex_characters_without_the_email() -> None:
    fingerprint = email_fingerprint("ana@x.com")

    assert re.fullmatch(r"[0-9a-f]{64}", fingerprint)
    assert "ana" not in fingerprint


def test_same_email_gives_same_fingerprint_after_normalizing() -> None:
    assert email_fingerprint(" Ana@X.com ") == email_fingerprint("ana@x.com")


def test_different_emails_give_different_fingerprints() -> None:
    assert email_fingerprint("ana@x.com") != email_fingerprint("ana@y.com")


def test_another_secret_gives_another_fingerprint() -> None:
    with override_settings(CONSENT_EMAIL_HASH_SECRET="one"):
        first = email_fingerprint("ana@x.com")
    with override_settings(CONSENT_EMAIL_HASH_SECRET="two"):
        second = email_fingerprint("ana@x.com")

    assert first != second
