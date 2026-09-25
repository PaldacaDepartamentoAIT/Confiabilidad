# Tareas: auth-headless
Estado: aprobado

- [x] T-001 Modelo `User` custom y `AUTH_USER_MODEL`
  RF: RF-001 | Depende de: — | Archivos: 8
  Hecho cuando: `cd backend && pytest apps/accounts/tests/test_user_model.py -q` pasa
  (`create_user`/`create_superuser`, email normalizado a minúsculas y único).
  Excepción: andamiaje del modelo de usuario indivisible — `AUTH_USER_MODEL` exige el modelo, la
  app (`apps/accounts/` + `apps.py`), la migración y el registro en `settings.INSTALLED_APPS` a la
  vez; incluye los `__init__.py` de `accounts/`, `migrations/` y `tests/`.

- [x] T-002 Integración de allauth headless y CORS (dependencias + registro + urls)
  RF: RF-002 | Depende de: T-001 | Archivos: 4
  Hecho cuando: `cd backend && python manage.py check` no da errores con `allauth`,
  `allauth.account`, `allauth.headless`, `corsheaders` y `django.contrib.sites` instalados y
  `_allauth/` enrutado en `config/urls.py`.
  Excepción: dependencias (`requirements.txt`, `pyproject.toml`) + registro repartido en
  `settings.py` (apps, `SITE_ID`, backends, middleware) + urls; indivisible para dejar la
  integración funcional.

- [ ] T-003 Login del cliente navegador (cookie), CSRF y credenciales inválidas
  RF: RF-002, RF-004, RF-005, RF-006 | Depende de: T-002 | Archivos: 3
  Hecho cuando: `cd backend && pytest apps/accounts/tests/test_login_browser.py -q` pasa: el login
  por email con CSRF establece la cookie de sesión y `GET .../auth/session` devuelve el usuario;
  el login sin CSRF y con credenciales inválidas se rechazan.

- [ ] T-004 Login del cliente de aplicación (token)
  RF: RF-003, RF-004 | Depende de: T-003 | Archivos: 1
  Hecho cuando: `cd backend && pytest apps/accounts/tests/test_login_app.py -q` pasa: el login del
  cliente app devuelve un token de sesión y, con `X-Session-Token`, `GET .../auth/session` devuelve
  el usuario.

- [ ] T-005 CORS para los orígenes de Tauri
  RF: RF-007 | Depende de: T-002 | Archivos: 3
  Hecho cuando: `cd backend && pytest apps/accounts/tests/test_cors.py -q` pasa: una petición con un
  `Origin` de Tauri permitido recibe las cabeceras CORS con credenciales; un origen no permitido no
  las recibe.

- [ ] T-006 Endurecimiento de cookies y HTTPS en producción
  RF: RF-008, RF-009 | Depende de: T-002 | Archivos: 2
  Hecho cuando: `cd backend && pytest apps/accounts/tests/test_security_settings.py -q` pasa: bajo
  settings de producción, las cookies de sesión/CSRF son `Secure` (sesión además `HttpOnly`), y
  están activos `SECURE_SSL_REDIRECT` y `SECURE_PROXY_SSL_HEADER`.

- [ ] T-007 Middleware de IP real tras proxy
  RF: RF-010 | Depende de: — | Archivos: 3
  Hecho cuando: `cd backend && pytest apps/core/tests/test_real_ip.py -q` pasa: el middleware fija
  `REMOTE_ADDR` a la última entrada de `X-Forwarded-For` (un proxy de confianza).

- [ ] T-008 Comando `seed_test_user` (verificación por CLI)
  RF: RF-001 | Depende de: T-001 | Archivos: 4
  Hecho cuando: `cd backend && pytest apps/accounts/tests/test_seed_command.py -q` pasa: el comando
  crea (idempotente) el usuario de prueba por email.
  Excepción: incluye los `__init__.py` de `management/` y `management/commands/` (andamiaje, una
  sola vez) además del comando y su test.

## RF sin tarea
Ninguno.
