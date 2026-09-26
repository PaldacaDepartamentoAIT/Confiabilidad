# Plan: auth-headless
Estado: aprobado

## Módulos

### M-01 App de cuentas y User custom
Responsabilidad: nueva app `backend/apps/accounts/` con un `User` custom mínimo (email como
identificador, único y normalizado a minúsculas), su manager (`create_user`/`create_superuser`),
migración `0001_initial`, y un management command `seed_test_user` para crear el usuario de
prueba (verificación CLI). `AUTH_USER_MODEL = "accounts.User"`.
RF: RF-001

### M-02 Integración de allauth headless
Responsabilidad: en `settings.py`, registrar `django.contrib.sites`, `allauth`,
`allauth.account`, `allauth.headless`, `apps.accounts` (+ `SITE_ID`), el backend de
autenticación de allauth, `AccountMiddleware`, login por email (`ACCOUNT_LOGIN_METHODS={"email"}`,
sin username), `ACCOUNT_EMAIL_VERIFICATION="none"`, `HEADLESS_ONLY=True`, y rate limiting
desactivado. En `config/urls.py`, `path("_allauth/", include("allauth.headless.urls"))`. Expone
los dos clientes: navegador (`/_allauth/browser/v1/...`, cookie) y app
(`/_allauth/app/v1/...`, `X-Session-Token`).
RF: RF-002, RF-003, RF-004, RF-005

### M-03 CSRF y CORS
Responsabilidad: CSRF exigido al cliente navegador (cookie) y **no** al de token (lo maneja
headless). `django-cors-headers`: `CorsMiddleware`, `CORS_ALLOWED_ORIGINS` con los orígenes de
Tauri (configurables por env), `CORS_ALLOW_CREDENTIALS=True`. `CSRF_TRUSTED_ORIGINS` por env.
RF: RF-006, RF-007

### M-04 Endurecimiento de cookies y HTTPS (solo producción)
Responsabilidad: en `settings.py`, activar en producción (`DEBUG=False`)
`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`,
`SESSION_COOKIE_SAMESITE`, `SECURE_SSL_REDIRECT`, y `SECURE_PROXY_SSL_HEADER=
("HTTP_X_FORWARDED_PROTO","https")`; relajado en desarrollo.
RF: RF-008, RF-009

### M-05 Middleware de IP real tras proxy
Responsabilidad: `apps/core/middleware.py` con `RealClientIPMiddleware` que fija
`request.META["REMOTE_ADDR"]` a la **última entrada** de `X-Forwarded-For` (un proxy de
confianza). Registrado en `MIDDLEWARE`.
RF: RF-010

## Modelo de datos
`User` (app `accounts`, `AbstractBaseUser` + `PermissionsMixin`; **placeholder** que la feature
de modelos completos extenderá):
- `email`: EmailField único; se normaliza a minúsculas en el manager. `USERNAME_FIELD = "email"`,
  `REQUIRED_FIELDS = []`.
- `is_active`, `is_staff` (para el admin), `date_joined`. Contraseña vía `AbstractBaseUser`.
- Manager `UserManager`: `create_user(email, password, **extra)` y `create_superuser(...)`.

Modelos de terceros: `allauth.account` (p. ej. `EmailAddress`) y `django.contrib.sites` (`Site`),
creados por sus migraciones.

## Decisiones

### D-01 Mecanismo de autenticación
Elegida: **django-allauth en modo headless**.
Descartada: construir tokens/JWT propios sobre DRF.
Motivo: el usuario pidió allauth headless; ya ofrece los dos clientes (navegador con cookie y app
con `X-Session-Token`) y los endpoints de login/sesión sin implementarlos a mano.

### D-02 Modelo de usuario
Elegida: **User custom** (`accounts.User`, email) desde ahora.
Descartada: `django.contrib.auth.User` por defecto.
Motivo: evitar el swap doloroso de `AUTH_USER_MODEL` al definir el dominio completo después; el
email es el identificador. Implica **resetear la BD de dev** (datos desechables).

### D-03 CSRF y cliente de token
Elegida: **el cliente de token queda exento de CSRF**; CSRF solo para el cliente navegador.
Descartada: exigir CSRF también al cliente de token.
Motivo: el token va en cabecera puesta explícitamente por el cliente; no hay autoridad ambiental
(cookie) que forjar, así que CSRF sería redundante y complicaría el escritorio. (S-07)

### D-04 Topología web/API
Elegida: **mismo origen** web/API (en dev vía proxy del dev server).
Descartada: cross-site.
Motivo: cookie `SameSite=Lax`, sin CORS ni complicaciones de CSRF para la web; CORS queda solo
para el escritorio. (S-06)

### D-05 IP real tras proxy
Elegida: **middleware propio** que toma la última entrada de `X-Forwarded-For` (un proxy de
confianza).
Descartada: `django-ipware` / tomar la primera entrada.
Motivo: sin dependencia extra; la primera entrada es suplantable por el cliente. Configurable si
se añaden más saltos. (S-08)

### D-06 CORS
Elegida: **django-cors-headers**.
Descartada: middleware CORS propio.
Motivo: librería estándar y mantenida; menos superficie de error en cabeceras/preflight.

### D-07 Endurecimiento por entorno
Elegida: cookies seguras + redirección HTTPS **solo en producción**.
Descartada: activarlas siempre.
Motivo: `Secure`/`SSL_REDIRECT` romperían el desarrollo local sobre HTTP. (S-03)

### D-08 Rate limiting
Elegida: **desactivado** en esta feature de prueba.
Descartada: dejar el rate limiting por defecto de allauth activo.
Motivo: es de prueba; evita bloqueos espurios en tests. Se reactivará en la auth definitiva. (S-09)

## Estrategia de tests
- **Unitario** (`apps/accounts/tests/`):
  - `test_user_model.py`: `create_user`/`create_superuser`, normalización a minúsculas y unicidad
    del email → RF-001.
  - `test_real_ip.py`: el middleware fija `REMOTE_ADDR` a la última entrada de `X-Forwarded-For`
    → RF-010.
- **Integración (API headless)**:
  - `test_login_browser.py`: obtener CSRF, `POST` login del cliente navegador → cookie + sesión
    autenticada (`GET .../auth/session`); y `POST` sin CSRF → rechazado → RF-002, RF-004, RF-006.
  - `test_login_app.py`: `POST` login del cliente app → `X-Session-Token`; `GET .../auth/session`
    con el token → sesión autenticada → RF-003, RF-004.
  - `test_invalid_credentials.py`: contraseña incorrecta → rechazo sin sesión ni token → RF-005.
  - `test_cors.py`: preflight/respuesta con `Origin` de Tauri permitido → cabeceras CORS; origen
    no permitido → sin ellas → RF-007.
  - `test_security_settings.py`: bajo settings de producción, flags `Secure`/`HttpOnly`/
    `SSL_REDIRECT`/`SECURE_PROXY_SSL_HEADER` correctos → RF-008, RF-009.
- **Cobertura** (P-05 ≥80%): modelo, manager, middleware, command y config verificables por test;
  `settings.py` excluido en `pyproject.toml`.
- Ejecución en el contenedor de la red de Podman (Postgres+Redis), como en la feature anterior.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01 | unitario (`test_user_model`) + CLI (`seed_test_user`) |
| RF-002 | M-02 | integración (`test_login_browser`) |
| RF-003 | M-02 | integración (`test_login_app`) |
| RF-004 | M-02 | integración (browser + app) |
| RF-005 | M-02 | integración (`test_invalid_credentials`) |
| RF-006 | M-03 | integración (`test_login_browser`, caso sin CSRF) |
| RF-007 | M-03 | integración (`test_cors`) |
| RF-008 | M-04 | unitario/settings (`test_security_settings`) |
| RF-009 | M-04 | unitario/settings (`test_security_settings`) |
| RF-010 | M-05 | unitario (`test_real_ip`) |

## RF sin cobertura
Ninguno.
