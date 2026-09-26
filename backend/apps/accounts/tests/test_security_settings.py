from config.settings import security_settings


def test_production_hardens_cookies_and_https() -> None:
    prod = security_settings(production=True)

    assert prod["SESSION_COOKIE_SECURE"] is True
    assert prod["CSRF_COOKIE_SECURE"] is True
    assert prod["SESSION_COOKIE_HTTPONLY"] is True
    assert prod["SECURE_SSL_REDIRECT"] is True
    assert prod["SECURE_PROXY_SSL_HEADER"] == ("HTTP_X_FORWARDED_PROTO", "https")


def test_development_relaxes_secure_flags() -> None:
    dev = security_settings(production=False)

    assert "SESSION_COOKIE_SECURE" not in dev
    assert "SECURE_SSL_REDIRECT" not in dev
    assert dev["SECURE_PROXY_SSL_HEADER"] == ("HTTP_X_FORWARDED_PROTO", "https")
