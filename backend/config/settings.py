from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "channels",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "django_celery_beat",
    "simple_history",
    "apps.core",
    "apps.accounts",
    "apps.consents",
    "apps.emails",
    "apps.audit",
    "apps.companies",
]

TRUSTED_PROXY_IPS: list[str] = env.list("TRUSTED_PROXY_IPS", default=[])

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.RealClientIPMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "apps.audit.middleware.CurrentRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://confiabilidad:confiabilidad@localhost:5432/confiabilidad",
    ),
}

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")


def _redis_url_with_db(url: str, db: int) -> str:
    # Aísla usos de Redis en índices lógicos distintos (S-03).
    return urlunsplit(urlsplit(url)._replace(path=f"/{db}"))


CACHE_URL = env("CACHE_URL", default=_redis_url_with_db(REDIS_URL, 1))
SESSION_CACHE_URL = env("SESSION_CACHE_URL", default=_redis_url_with_db(REDIS_URL, 2))

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": CACHE_URL,
    },
    "sessions": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": SESSION_CACHE_URL,
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)

# Política de contraseñas del proyecto (RF-022 de procesos-pendientes).
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ("email", "name")},
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "apps.accounts.password_validation.PwnedPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Inicio de sesión y sesiones activas: límites y tiempos configurables (RF-020 de
# inicio-cierre-sesion).
LOGIN_MAX_FAILED_ATTEMPTS = env.int("LOGIN_MAX_FAILED_ATTEMPTS", default=5)
LOGIN_LOCKOUT_MINUTES = env.int("LOGIN_LOCKOUT_MINUTES", default=5)
LOGIN_RATE_IP_PER_MINUTE = env.int("LOGIN_RATE_IP_PER_MINUTE", default=30)
PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS = env.int("PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS", default=5)
PASSWORD_CHANGE_ATTEMPT_WINDOW_MINUTES = env.int(
    "PASSWORD_CHANGE_ATTEMPT_WINDOW_MINUTES", default=5
)
PASSWORD_CHANGE_LOCKOUT_MINUTES = env.int("PASSWORD_CHANGE_LOCKOUT_MINUTES", default=5)
ACCOUNT_DISABLE_MAX_FAILED_ATTEMPTS = env.int("ACCOUNT_DISABLE_MAX_FAILED_ATTEMPTS", default=5)
ACCOUNT_DISABLE_ATTEMPT_WINDOW_MINUTES = env.int(
    "ACCOUNT_DISABLE_ATTEMPT_WINDOW_MINUTES", default=5
)
ACCOUNT_DISABLE_LOCKOUT_MINUTES = env.int("ACCOUNT_DISABLE_LOCKOUT_MINUTES", default=5)
ACCOUNT_DISABLE_RETENTION_MONTHS = env.int("ACCOUNT_DISABLE_RETENTION_MONTHS", default=12)
SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS = env.int(
    "SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS", default=60
)
SESSION_LIFETIME_DAYS = env.int("SESSION_LIFETIME_DAYS", default=14)
SESSION_COOKIE_AGE = SESSION_LIFETIME_DAYS * 86400

# django-allauth (headless): cuenta local por email, con bloqueo por intentos fallidos (RF-004).
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_RATE_LIMITS: dict[str, object] = {
    "login_failed": f"10/m/ip,{LOGIN_MAX_FAILED_ATTEMPTS}/{LOGIN_LOCKOUT_MINUTES}m/key",
}
ACCOUNT_ADAPTER = "apps.audit.adapters.AuditAccountAdapter"
HEADLESS_ONLY = True

# CORS: solo el cliente de escritorio Tauri (la web es mismo origen). Orígenes por entorno.
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "tauri://localhost",
        "https://tauri.localhost",
        "http://localhost:1420",
    ],
)
CORS_ALLOW_CREDENTIALS = True


def security_settings(*, production: bool) -> dict[str, object]:
    # Endurecimiento solo en producción (HTTPS tras proxy de confianza); en dev se relaja.
    settings_map: dict[str, object] = {
        "SECURE_PROXY_SSL_HEADER": ("HTTP_X_FORWARDED_PROTO", "https"),
    }
    if production:
        settings_map.update(
            {
                "SESSION_COOKIE_SECURE": True,
                "CSRF_COOKIE_SECURE": True,
                "SESSION_COOKIE_HTTPONLY": True,
                "SECURE_SSL_REDIRECT": True,
            }
        )
    return settings_map


# El endurecimiento se desactiva en el entorno de test (el CI fija DJANGO_SECURE_HARDENING=0),
# porque el cliente de test hace HTTP y SECURE_SSL_REDIRECT devolvería 301. La lógica de
# producción se verifica en test_security_settings.py.
globals().update(
    security_settings(production=env.bool("DJANGO_SECURE_HARDENING", default=not DEBUG))
)

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Registro pendiente: límites configurables (RF-019) y secreto de los códigos (RF-008, RF-015).
REGISTRATION_MAX_FAILED_ATTEMPTS = env.int("REGISTRATION_MAX_FAILED_ATTEMPTS", default=5)
REGISTRATION_CODE_TTL_MINUTES = env.int("REGISTRATION_CODE_TTL_MINUTES", default=15)
REGISTRATION_GRACE_MINUTES = env.int("REGISTRATION_GRACE_MINUTES", default=15)
REGISTRATION_MAX_LIFETIME_MINUTES = env.int("REGISTRATION_MAX_LIFETIME_MINUTES", default=60)
REGISTRATION_CODE_SECRET = env("REGISTRATION_CODE_SECRET", default=SECRET_KEY)
REGISTRATION_CODE_SECRET_PREVIOUS = env("REGISTRATION_CODE_SECRET_PREVIOUS", default="")
REGISTRATION_CODE_SECRET_ROTATED_AT = env("REGISTRATION_CODE_SECRET_ROTATED_AT", default="")
REGISTRATION_SECRET_TRANSITION_MINUTES = env.int(
    "REGISTRATION_SECRET_TRANSITION_MINUTES", default=60
)
PWNED_PASSWORDS_TIMEOUT_SECONDS = env.float("PWNED_PASSWORDS_TIMEOUT_SECONDS", default=2.0)
# Minutos durante los que se reintenta el trabajo de fuera de la respuesta de empezar un proceso.
REGISTRATION_START_RETRY_MINUTES = env.int("REGISTRATION_START_RETRY_MINUTES", default=5)
# Límite de frecuencia del formulario de registro (RF-010 y RF-011 de registro-api).
REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS = env.int(
    "REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS", default=60
)
REGISTRATION_RATE_EMAIL_IP_PER_HOUR = env.int("REGISTRATION_RATE_EMAIL_IP_PER_HOUR", default=5)
REGISTRATION_RATE_IP_PER_HOUR = env.int("REGISTRATION_RATE_IP_PER_HOUR", default=20)
# Pantallas de verificación y contraseña del registro (RF-010, RF-019, RF-020 de registro-flujo).
REGISTRATION_RESEND_INTERVAL_SECONDS = env.int("REGISTRATION_RESEND_INTERVAL_SECONDS", default=60)
REGISTRATION_MAX_RESENDS = env.int("REGISTRATION_MAX_RESENDS", default=5)
REGISTRATION_RATE_FLOW_IP_PER_HOUR = env.int("REGISTRATION_RATE_FLOW_IP_PER_HOUR", default=60)
REGISTRATION_PURGE_AFTER_HOURS = env.int("REGISTRATION_PURGE_AFTER_HOURS", default=24)
PWNED_PASSWORDS_ENABLED = env.bool("PWNED_PASSWORDS_ENABLED", default=True)

# Correos: proveedor de envío por entorno (D-02). Sin EMAIL_BACKEND, el correo completo sale
# por la consola del worker. En producción: SMTP contra MXroute, con las credenciales en SOPS.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=465)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=True)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=10)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-responder@localhost")

# Tareas periódicas de mantenimiento y alertas (tareas-purga-y-alertas).
PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS = env.float(
    "PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS", default=3600.0
)
PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS = env.float(
    "PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS", default=3600.0
)
PURGE_SECURITY_EVENTS_INTERVAL_SECONDS = env.float(
    "PURGE_SECURITY_EVENTS_INTERVAL_SECONDS", default=86400.0
)
MAINTENANCE_ALERT_EMAILS: list[str] = env.list("MAINTENANCE_ALERT_EMAILS", default=[])
MAINTENANCE_LOCK_TIMEOUT_SECONDS = env.int("MAINTENANCE_LOCK_TIMEOUT_SECONDS", default=3600)

# Barrido de la bandeja de salida: encola los correos pendientes con el intento vencido (D-14).
CELERY_BEAT_SCHEDULE = {
    "emails-dispatch-due": {"task": "apps.emails.tasks.dispatch_due", "schedule": 30.0},
    "accounts-sweep-unresolved": {"task": "apps.accounts.tasks.sweep_unresolved", "schedule": 60.0},
    "accounts-purge-stale-registrations": {
        "task": "apps.accounts.tasks.purge_stale_registrations",
        "schedule": PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS,
    },
    "accounts-purge-expired-sessions": {
        "task": "apps.accounts.tasks.purge_expired_sessions",
        "schedule": PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS,
    },
    "audit-purge-security-events": {
        "task": "apps.audit.tasks.purge_security_events",
        "schedule": PURGE_SECURITY_EVENTS_INTERVAL_SECONDS,
    },
}

# Correos: dirección del frontend a la que llevan los enlaces de los correos (D-09).
FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:5173")
# Dirección a la que el titular reporta un aviso de seguridad que no reconoce (RF-010).
EMAIL_SUPPORT_ADDRESS = env("EMAIL_SUPPORT_ADDRESS", default="soporte@localhost")
# Horas durante las que se reintenta un aviso de seguridad que el proveedor no acepta (RF-016).
EMAIL_NOTICE_RETRY_HOURS = env.int("EMAIL_NOTICE_RETRY_HOURS", default=24)
# Minutos durante los que una cuenta no recibe otro aviso "ya tienes cuenta" (RF-007).
EMAIL_ACCOUNT_EXISTS_WINDOW_MINUTES = env.int("EMAIL_ACCOUNT_EXISTS_WINDOW_MINUTES", default=60)

# El historial se consulta en el panel, pero no se revierte desde él (RF-020 de consentimientos).
SIMPLE_HISTORY_REVERT_DISABLED = True

# Consentimientos: secreto de la huella del correo (RF-012). No debe rotar nunca (S-09).
CONSENT_EMAIL_HASH_SECRET = env("CONSENT_EMAIL_HASH_SECRET", default=SECRET_KEY)

# Correos: clave de la máscara del código de los correos pendientes, distinta de la de códigos
# (RF-011 de huellas-hmac-unificadas). No rota: al cambiarla se descartan los correos pendientes.
EMAIL_CODE_SECRET = env("EMAIL_CODE_SECRET", default=f"email-code:{SECRET_KEY}")

# En desarrollo hay un valor fijo para que Docker arranque sin .env; sin DEBUG, audit.E001 exige la
# clave (D-05, P-02).
AUDIT_HASH_SECRET = env("AUDIT_HASH_SECRET", default="") or (
    "dev-audit-secret-change-me" if DEBUG else ""
)
