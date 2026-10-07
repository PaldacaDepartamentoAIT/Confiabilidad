import hashlib
import hmac

from apps.consents import conf


def email_fingerprint(email: str) -> str:
    message = email.strip().lower().encode()
    return hmac.new(conf.email_hash_secret().encode(), message, hashlib.sha256).hexdigest()
