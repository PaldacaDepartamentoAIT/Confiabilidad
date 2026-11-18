# Tareas: inicio-cierre-sesion
Estado: aprobado

Rutas del backend relativas a `backend/apps/accounts/` y del frontend a `frontend/src/`, salvo que
se indique otra. «Suite verde» = `cd backend && pytest -q` + `mypy .` + `ruff check .` +
`black --check .` en el backend, y `pnpm --filter frontend test` + `typecheck` + `lint` +
`prettier --check` en el frontend, sin errores. En cada tarea, antes de marcarla, se prueba al menos
un mutante del código que introduce, que debe hacer fallar sus tests (archivo de tests completo,
nunca con `-k`).

Las pantallas nuevas se construyen primero sin exponerlas en el enrutador (`E-07` y `E-08`) y se
conectan todas a la vez en `E-09`, para no exponer en la interfaz nada que aún no funcione
(`AGENTS.md`).

## Backend

- [ ] T-001 Valores configurables de inicio de sesión y sesiones
  RF: RF-020 (valores configurables; M-03, adaptador de allauth y límites de inicio de sesión) | Depende de: — | Archivos: 4
  Archivos: `backend/config/settings.py`, `backend/.env.example`, `conf.py`,
  `tests/test_auth_conf.py`.
  Hecho cuando: `conf` expone el máximo de intentos fallidos (5), la ventana de bloqueo (5 min), el
  límite de peticiones de login por IP (30/min), el intervalo de actualización de actividad de
  sesión (60 s) y la vida de una sesión (14 días), leídos del entorno, conecta
  `ACCOUNT_RATE_LIMITS["login_failed"]` y `SESSION_COOKIE_AGE` en `settings.py`, y rechaza valores
  menores que 1; suite verde.
  Excepción: la configuración está repartida por diseño entre `settings.py`, `.env.example` y
  `conf.py`; separarla dejaría un ajuste sin lector o sin su prueba.

- [ ] T-002 Límite por IP del inicio de sesión
  RF: RF-005 (límite de frecuencia por IP en el inicio de sesión), RF-020 (M-03) | Depende de: T-001 (valores configurables de inicio de sesión y sesiones) | Archivos: 2
  Archivos: `throttling.py`, `tests/test_auth_throttling.py`.
  Hecho cuando: `check_login_ip` permite 30 solicitudes por minuto desde una misma IP y rechaza la
  31.ª devolviendo `allowed=False` y los segundos de espera (`retry_after`), con una clave propia en
  caché independiente de las del registro; suite verde.

- [ ] T-003 Bloqueo por intentos fallidos en cuenta inactiva
  RF: RF-002 (rechazo neutro de credenciales inválidas o cuenta inactiva), RF-004 (bloqueo temporal por intentos fallidos; M-03; D-03, cómputo de intentos fallidos en cuenta inactiva; C-02, bloqueo por intentos en cuenta inactiva) | Depende de: T-001 | Archivos: 2
  Archivos: `backend/apps/audit/adapters.py`, `tests/test_inactive_login.py`.
  Hecho cuando: en `AuditAccountAdapter.pre_login`, un intento sobre una cuenta inactiva con
  contraseña correcta registra `inactive_account` en `SecurityEvent` y consume un intento en el
  limitador `login_failed` de allauth, de modo que al sexto intento consecutivo se bloquea con
  `too_many_login_attempts` y genera el evento `LOCKOUT`, igual que con contraseña incorrecta, sin
  romper los tests existentes de `test_inactive_login.py`; suite verde.

- [ ] T-004 Modelo `UserSession`
  RF: RF-007 (registro de sesiones activas; M-01, modelo `UserSession` y servicio de sesiones; D-02, huella HMAC en `UserSession.session_key` e índice inverso en caché; C-08, trato de `user_agent` vacío o largo; S-09, huella HMAC de la clave de sesión) | Depende de: — | Archivos: 3
  Archivos: `models.py`, `migrations/0015_usersession.py`, `tests/test_user_session_model.py`.
  Hecho cuando: `UserSession` guarda `user`, `session_key` (único de 64 caracteres), `ip`,
  `user_agent` (`"unknown"` si falta o está en blanco, y longitud completa sin recortar cuando viene
  informada), `created_at` y `last_seen_at` (indexado); `python manage.py makemigrations --check` no
  propone nada; suite verde.

- [ ] T-005 Servicio de sesiones: alta, actividad, consulta y cierre actual
  RF: RF-006 (cierre de la sesión actual), RF-007, RF-008 (consulta de sesiones activas; M-01, D-02; C-01, detección y limpieza de sesiones caducadas; C-08) | Depende de: T-001, T-004 (modelo `UserSession`) | Archivos: 2
  Archivos: `sessions.py`, `tests/test_sessions_service.py`.
  Hecho cuando: `register_session` guarda la fila en `UserSession` con la huella HMAC
  (`audit_session_fingerprint`), nunca la clave en claro, y el índice inverso en la caché
  `sessions`; `touch_session` actualiza `last_seen_at`, `ip` y `user_agent` solo cuando han pasado
  al menos 60 s; `list_active_sessions` borra las vencidas o ausentes en la caché y devuelve las
  vigentes ordenadas de más reciente a más antigua con `is_current`; `close_current_session` borra
  la sesión de la caché y su fila de `UserSession`; suite verde.

- [ ] T-006 Servicio de sesiones: cierre de otras sesiones, invalidación masiva y purga
  RF: RF-003 (invalidación inmediata al desactivar o borrar una cuenta), RF-009 (cierre de otra sesión o de todas las demás), RF-010 (invalidación de sesiones al cambiar o restablecer la contraseña), RF-021 (limpieza de sesiones caducadas; M-01, D-02; C-01; C-05, cierre sin sesión válida y cierre masivo sin otras sesiones) | Depende de: T-005 (servicio de sesiones: alta, actividad, consulta y cierre actual) | Archivos: 2
  Archivos: `sessions.py`, `tests/test_sessions_service.py`.
  Hecho cuando: `revoke_other_session` rechaza cerrar la sesión actual y una inexistente o ajena, y
  al cerrar otra sesión válida la borra de la caché `sessions`, borra su fila y registra `LOGOUT` en
  `SecurityEvent`; `revoke_all_other_sessions` cierra todas las demás y registra un `LOGOUT` por
  cada una vigente (0 eventos si solo está la actual); `revoke_all_user_sessions` borra todas las de
  la cuenta; `purge_expired` borra todas las caducadas o sin entrada en caché y devuelve el total;
  suite verde.

- [ ] T-007 Sincronización automática de sesiones al entrar, salir, desactivar, borrar o cambiar contraseña
  RF: RF-003, RF-006, RF-007, RF-010 (M-02, invalidación automática por cuenta inactiva, borrado o cambio de contraseña; D-05, invalidación de sesiones en dos capas; C-03, alcance de invalidación por cambio de contraseña) | Depende de: T-006 (servicio de sesiones: cierre de otras sesiones, invalidación masiva y purga) | Archivos: 3
  Archivos: `models.py`, `sessions.py`, `tests/test_sessions_lifecycle.py`.
  Hecho cuando: iniciar o cerrar sesión mediante las señales de autenticación crea o borra la fila
  de `UserSession`; desactivar (`is_active=False`) o borrar físicamente un usuario, cambiar su
  contraseña en `User.save()` o completar `password_reset.complete` invalida sus sesiones en la
  caché `sessions` y vacía sus filas de `UserSession`; suite verde.

- [ ] T-008 Limpieza de sesiones caducadas por consola y tarea periódica
  RF: RF-021 (M-05, comando de consola y tarea programada de limpieza; P-03, backend verificable desde CLI) | Depende de: T-006 | Archivos: 4
  Archivos: `management/commands/purge_expired_sessions.py`, `tasks.py`,
  `backend/config/settings.py`, `tests/test_purge_expired_sessions.py`.
  Hecho cuando: `python manage.py purge_expired_sessions` y la tarea Celery
  `apps.accounts.tasks.purge_expired_sessions` (programada cada 3600 s en `CELERY_BEAT_SCHEDULE`)
  borran las filas caducadas o sin sesión viva e informan del número borrado; suite verde.
  Excepción: el comando, la tarea, su programación en `settings.py` y su test deben ir juntos para
  verificar tanto la orden de consola como la tarea periódica de RF-021.

- [ ] T-009 Textos de la API de inicio y cierre de sesión en tres idiomas
  RF: RF-019 (idioma de pantallas y mensajes; M-04, API de inicio y cierre de sesión, términos y sesiones activas) | Depende de: — | Archivos: 2
  Archivos: `api/messages.py`, `tests/test_registration_api_messages.py`.
  Hecho cuando: `invalid_credentials`, `too_many_login_attempts`, `already_authenticated`,
  `unauthenticated`, `terms_required` y `cannot_revoke_current_session` tienen texto en `es`,
  `pt-BR` y `en`, y el test de completitud de mensajes pasa; suite verde.

- [ ] T-010 Rutas de inicio de sesión, consulta de sesión actual y cierre de sesión
  RF: RF-001 (acceso con correo y contraseña), RF-002, RF-003, RF-004, RF-005, RF-006, RF-018 (clientes web y de escritorio), RF-019 (M-04; D-01, vistas propias bajo `/api/.../auth/`; D-04, autenticación común para ambos clientes; C-04, rechazo de login con sesión activa; C-05; CF-2, test de respuesta neutra y bloqueo en cuenta inactiva; CF-3, test de invalidación al cerrar sesión o desactivar cuenta; CF-6, test de límites de intentos y por IP) | Depende de: T-002 (límite por IP del inicio de sesión), T-003 (bloqueo por intentos fallidos en cuenta inactiva), T-007 (sincronización automática de sesiones), T-009 (textos de la API en tres idiomas) | Archivos: 4
  Archivos: `api/auth_serializers.py`, `api/auth_views.py`, `api/urls.py`, `tests/test_auth_api.py`.
  Hecho cuando: `POST /api/{browser,app}/v1/auth/login`, `GET .../auth/session` y
  `POST .../auth/logout` autentican y cierran sesión en web (cookie + CSRF) y escritorio
  (`X-Session-Token`), rechazan con `400 already_authenticated` si ya hay sesión activa, devuelven
  `429` al superar el límite por IP sin evento de auditoría, responden `401` sin evento al cerrar
  sin sesión válida y rechazan de inmediato sesiones de cuentas desactivadas incluso con
  `QuerySet.update(is_active=False)`; suite verde.
  Excepción: las rutas nuevas requieren su serializador, su vista, el registro en `urls.py` y su
  test de integración para ser ejercitables.

- [ ] T-011 Test de neutralidad y bloqueo en el inicio de sesión
  RF: RF-002, RF-004 (CF-2, CF-6) | Depende de: T-010 (rutas de inicio de sesión, consulta de sesión actual y cierre de sesión) | Archivos: 1
  Archivos: `tests/test_auth_neutrality.py`.
  Hecho cuando: un test demuestra que correo inexistente, contraseña incorrecta y cuenta inactiva
  (con contraseña correcta o incorrecta) reciben en `/api/{browser,app}/v1/auth/login` el mismo
  código (`400`), cuerpo, cabeceras y cookies en los intentos 1 a 5 y el mismo bloqueo
  (`too_many_login_attempts`) en el 6.º, mientras que `SecurityEvent` registra `inactive_account`
  antes del bloqueo cuando la contraseña de la cuenta inactiva es correcta; suite verde.

- [ ] T-012 Ruta de aceptación de términos vigentes y guarda del área privada
  RF: RF-011 (bloqueo del área privada mientras falten los términos vigentes), RF-012 (aceptación de los términos vigentes con sesión iniciada), RF-018, RF-019 (M-04; D-06, comprobación de términos vigentes en cada petición privada; C-06, comprobación de términos en cada petición privada; CF-5, test de bloqueo y aceptación de términos vigentes) | Depende de: T-010 | Archivos: 4
  Archivos: `api/auth_serializers.py`, `api/auth_views.py`, `api/urls.py`,
  `tests/test_auth_terms_gate.py`.
  Hecho cuando: `POST /api/{browser,app}/v1/auth/terms/accept` exige sesión activa (y CSRF en
  `browser`), valida el documento con las reglas y códigos de RF-004 de `registro-api` (términos
  obligatorios), registra la aceptación y devuelve `{"terms_status": "accepted"}`; una cuenta sin
  términos vigentes aceptados o sin versión vigente publicada puede consultar su sesión y cerrarla,
  pero recibe `403 terms_required` en las rutas del área privada, también cuando se publica una
  versión obligatoria nueva con la sesión ya abierta; suite verde.
  Excepción: la ruta nueva requiere su serializador, su vista, su entrada en `urls.py` y su test.

- [ ] T-013 Rutas de listado y cierre de otras sesiones activas
  RF: RF-008, RF-009, RF-011, RF-018, RF-019 (M-04, D-06; C-01, C-05, C-06; CF-4, test de listado y cierre de otras sesiones) | Depende de: T-012 (ruta de aceptación de términos vigentes y guarda del área privada) | Archivos: 4
  Archivos: `api/auth_serializers.py`, `api/auth_views.py`, `api/urls.py`,
  `tests/test_sessions_api.py`.
  Hecho cuando: `GET /api/{browser,app}/v1/auth/sessions`, `POST .../auth/sessions/revoke` y
  `POST .../auth/sessions/revoke-others` exigen sesión activa y términos vigentes (`403
  terms_required` si faltan), listan las sesiones vigentes ordenadas con `is_current` sin exponer
  `session_key`, cierran otra sesión concreta (`400` si es la actual, `404` si es ajena o no existe)
  o todas las demás (`200` con `revoked_count: 0` y sin eventos si no hay otras), e invalidan al
  instante sus cookies y tokens; suite verde.
  Excepción: las rutas nuevas requieren su serializador, su vista, `urls.py` y su test.

## Frontend

- [ ] T-014 Almacenamiento de token para escritorio y soporte de autenticación en el cliente API
  RF: RF-006, RF-011, RF-018 (M-06, cliente de autenticación y almacenamiento de token para escritorio; S-07, limpieza local garantizada al cerrar sesión) | Depende de: — | Archivos: 3
  Archivos: `auth/tokenStorage.ts`, `api/client.ts`, `api/client.test.ts`.
  Hecho cuando: en modo `app`, el cliente adjunta `X-Session-Token` cuando hay token guardado en
  `TokenStorage`; `client.ts` interpreta `401` como `{ kind: "unauthenticated" }` y `403` con
  `code: "terms_required"` como `{ kind: "termsRequired", termsStatus }`, conservando el resto de
  respuestas existentes; suite verde.

- [ ] T-015 Llamadas de la API de autenticación y sesiones
  RF: RF-001, RF-006, RF-008, RF-009, RF-012, RF-018 (M-06, S-07) | Depende de: T-014 (almacenamiento de token para escritorio y soporte en el cliente API) | Archivos: 2
  Archivos: `api/auth.ts`, `api/auth.test.ts`.
  Hecho cuando: existen funciones tipadas `getSession`, `login` (que en modo `app` guarda el
  `session_token` recibido), `logout` (que borra siempre el token local en `finally`, aunque el
  servidor devuelva `401` o falle la red), `acceptTerms`, `listSessions`, `revokeSession` y
  `revokeOtherSessions`; suite verde.

- [ ] T-016 Textos de inicio de sesión, términos pendientes y sesiones activas en tres idiomas
  RF: RF-013 (pantalla de inicio de sesión y enlaces con el registro), RF-014 (validación en el cliente y mensajes de error al iniciar sesión), RF-015 (pantalla de aceptación de términos pendientes), RF-016 (área privada y gestión de sesiones en pantalla), RF-019 (M-07, enrutamiento, guardia de sesión y enlaces con registro) | Depende de: — | Archivos: 4
  Archivos: `i18n/locales/es.ts`, `i18n/locales/pt-BR.ts`, `i18n/locales/en.ts`,
  `i18n/locales/locales.test.ts`.
  Hecho cuando: existen en los tres idiomas los textos de inicio de sesión, enlaces entre login y
  registro, pantalla de términos pendientes, área privada y gestión de sesiones, y códigos de error
  nuevos; `locales.test.ts` pasa; suite verde.
  Excepción: los tres archivos de idioma y el test que verifica la paridad de claves y grupos deben
  actualizarse juntos para no romper la comprobación de RF-008 de `componentes-base-accesibles`
  (traducciones completas).

- [ ] T-017 Traducción de errores de inicio de sesión y términos en el cliente
  RF: RF-012, RF-014, RF-019 (M-08, pantalla de inicio de sesión; M-09, pantalla de términos pendientes) | Depende de: T-016 (textos en tres idiomas) | Archivos: 2
  Archivos: `registration/serverErrors.ts`, `registration/serverErrors.test.ts`.
  Hecho cuando: `serverErrors` traduce `invalid_credentials`, `too_many_login_attempts`,
  `already_authenticated` y `cannot_revoke_current_session` a sus claves de traducción, manteniendo
  todos los códigos existentes; suite verde.

- [ ] T-018 Pantalla de inicio de sesión (sin ruta)
  RF: RF-013, RF-014, RF-019 (M-08; CF-7, tests de pantallas y redirecciones en frontend) | Depende de: T-015 (llamadas de la API de autenticación y sesiones), T-017 (traducción de errores en el cliente) | Archivos: 2
  Archivos: `auth/LoginPage.tsx`, `auth/LoginPage.test.tsx`.
  Hecho cuando: `LoginPage` valida al salir y al enviar que el correo y la contraseña no estén
  vacíos y que el correo tenga forma de dirección, enfocando el primer campo con error sin llamar al
  servidor; ante `invalid_credentials` muestra el error general, conserva el correo y vacía la
  contraseña; ante `too_many_login_attempts` o fallo de red muestra el error general conservando el
  correo; ante `429` muestra la cuenta atrás y desactiva el botón hasta cero; incluye el enlace a
  `/register` y notifica al autenticar con éxito; suite verde.

- [ ] T-019 Pantalla de términos pendientes (sin ruta)
  RF: RF-011, RF-012, RF-015, RF-019 (M-09, CF-5, CF-7) | Depende de: T-015, T-017 | Archivos: 2
  Archivos: `auth/TermsPage.tsx`, `auth/TermsPage.test.tsx`.
  Hecho cuando: con `terms_status === "not_accepted"`, `TermsPage` muestra el documento vigente en
  Markdown, exige marcar la casilla antes de enviar, llama a `acceptTerms` y notifica el paso al
  área privada, o permite cerrar la sesión actual (`logout`, incluso si falla la red); con
  `no_current_version`, oculta el formulario de aceptación, informa de que no se puede continuar y
  ofrece cerrar la sesión; suite verde.

- [ ] T-020 Pantalla del área privada y gestión de sesiones (sin ruta)
  RF: RF-006, RF-008, RF-009, RF-011, RF-016, RF-017 (redirecciones según el estado de la sesión), RF-019 (M-10, pantalla del área privada y gestión de sesiones; C-05, C-06, CF-4, CF-7) | Depende de: T-015, T-016 | Archivos: 2
  Archivos: `auth/HomePage.tsx`, `auth/HomePage.test.tsx`.
  Hecho cuando: `HomePage` muestra con `AppLayout` el nombre y correo del usuario, el botón de
  cerrar la sesión actual (que limpia el cliente y lleva a `/login` incluso si el servidor da `401`
  o falla la red) y la tabla de sesiones activas señalando la actual; permite cerrar otra sesión
  individual o todas las demás; desactiva el botón «Cerrar todas las demás sesiones» cuando solo
  existe la sesión actual; y si recibe `termsRequired` (`403`) o `unauthenticated` (`401`) al
  consultar o revocar sesiones, redirige a `/terms` o `/login`; suite verde.

- [ ] T-021 Enlaces a `/login` desde el formulario de registro y desde cuenta creada
  RF: RF-013 (M-07; S-08, enlace desde cuenta creada; CF-7) | Depende de: T-016 | Archivos: 3
  Archivos: `registration/RegisterPage.tsx`, `registration/DonePage.tsx`,
  `registration/RegisterPage.test.tsx`.
  Hecho cuando: tanto la pantalla de registro (`/register`) como la de cuenta creada
  (`/register/done`) muestran un enlace a `/login` que navega sin recargar la página; suite verde.

- [ ] T-022 Rutas y redirecciones según el estado de la sesión y de los términos
  RF: RF-013, RF-015, RF-016, RF-017 (M-07; C-07, rutas de navegación del cliente; S-10, identidad visual y traslado de la página de muestra; CF-5, CF-7) | Depende de: T-018 (pantalla de inicio de sesión), T-019 (pantalla de términos pendientes), T-020 (pantalla del área privada), T-021 (enlaces a `/login`) | Archivos: 3
  Archivos: `App.tsx`, `App.test.tsx`, `registration/VerifyPage.test.tsx`.
  Hecho cuando: `/` muestra el área privada, `/login` el inicio de sesión, `/terms` los términos
  pendientes y `/showcase` la página de muestra; abrir `/` o `/terms` sin sesión redirige a
  `/login`; abrir `/login` o `/register` con sesión activa redirige a `/` (si los términos están
  aceptados) o a `/terms` (si faltan); abrir `/` con términos pendientes redirige a `/terms` y abrir
  `/terms` con ellos aceptados redirige a `/`; suite verde.

- [ ] T-023 Accesibilidad de las pantallas de inicio de sesión, términos pendientes y área privada
  RF: RF-013, RF-015, RF-016 (CF-1, tests para cada RF y análisis estático limpio; CF-7) | Depende de: T-022 (rutas y redirecciones) | Archivos: 1
  Archivos: `auth/a11y.test.tsx`.
  Hecho cuando: `axe-core` no encuentra fallos en `LoginPage` (normal y con errores), `TermsPage`
  (con términos pendientes y sin versión vigente) y `HomePage` (con una y varias sesiones); suite
  verde.

- [ ] T-024 Resumen de la feature y guía de prueba
  RF: RF-001…RF-021 (M-10; CF-8, guía de prueba en aplicación y consola) | Depende de: T-013 (rutas de listado y cierre de otras sesiones), T-023 (accesibilidad de las pantallas) | Archivos: 1
  Archivos: `specs/inicio-cierre-sesion/resumen.md`.
  Hecho cuando: `resumen.md` explica qué se hizo, su marco teórico y los pasos ejecutables para
  probar en la aplicación y con `curl` / `manage.py` el inicio y cierre de sesión en ambos clientes,
  la cuenta inactiva, los límites, los términos pendientes, el listado y cierre de otras sesiones y
  la purga de sesiones caducadas.

## Entregas
Rama de integración: `feat/inicio-cierre-sesion` (los PR de las entregas van contra ella; ver `AGENTS.md`)

- E-01 Configuración, límite por IP y cómputo de intentos en cuenta inactiva
  Tareas: T-001, T-002, T-003 | Líneas estimadas: 240 | Rama: feat/inicio-cierre-sesion-limites
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_auth_conf.py apps/accounts/tests/test_auth_throttling.py apps/accounts/tests/test_inactive_login.py` y comprobar que 6 intentos con contraseña correcta sobre una cuenta inactiva disparan el bloqueo `too_many_login_attempts` y la fila `LOCKOUT` en `SecurityEvent`.

- E-02 Modelo `UserSession` y servicio de sesiones activas
  Tareas: T-004, T-005, T-006 | Líneas estimadas: 350 | Rama: feat/inicio-cierre-sesion-servicio-sesiones
  Cómo probarlo: aplicar la migración y ejecutar `pytest apps/accounts/tests/test_user_session_model.py apps/accounts/tests/test_sessions_service.py`.

- E-03 Ciclo de vida automático de sesiones y orden de purga en consola
  Tareas: T-007, T-008 | Líneas estimadas: 280 | Rama: feat/inicio-cierre-sesion-purga
  Cómo probarlo: iniciar sesión desde consola/test, envejecer la fila en `UserSession` y ejecutar `python manage.py purge_expired_sessions`; desactivar o cambiar la contraseña de un usuario y comprobar que sus filas de `UserSession` desaparecen.

- E-04 API de inicio de sesión, sesión actual, cierre de sesión y neutralidad
  Tareas: T-009, T-010, T-011 | Líneas estimadas: 380 | Rama: feat/inicio-cierre-sesion-api-auth
  Cómo probarlo: con `curl`, iniciar sesión en `/api/browser/v1/auth/login` y `/api/app/v1/auth/login`, consultar `/api/.../auth/session`, cerrar sesión en `/api/.../auth/logout`, y verificar la misma respuesta `400` ante cuenta inactiva y contraseña errónea.

- E-05 API de aceptación de términos vigentes y gestión de otras sesiones
  Tareas: T-012, T-013 | Líneas estimadas: 340 | Rama: feat/inicio-cierre-sesion-api-sesiones
  Cómo probarlo: con `curl`, iniciar sesión con una cuenta sin términos vigentes (ve `403 terms_required` en `/api/app/v1/auth/sessions`), aceptarlos en `/api/app/v1/auth/terms/accept`, listar sus sesiones activas y cerrar otra sesión o todas las demás.

- E-06 Cliente de autenticación, token de escritorio y traducciones del frontend
  Tareas: T-014, T-015, T-016, T-017 | Líneas estimadas: 350 | Rama: feat/inicio-cierre-sesion-cliente-auth
  Cómo probarlo: ejecutar `pnpm --filter frontend test src/api/client.test.ts src/api/auth.test.ts src/i18n/locales/locales.test.ts src/registration/serverErrors.test.ts`.

- E-07 Pantallas de inicio de sesión y de términos pendientes (sin ruta)
  Tareas: T-018, T-019 | Líneas estimadas: 360 | Rama: feat/inicio-cierre-sesion-pantallas-acceso
  Cómo probarlo: ejecutar `pnpm --filter frontend test src/auth/LoginPage.test.tsx src/auth/TermsPage.test.tsx`.

- E-08 Pantalla del área privada y gestión de sesiones (sin ruta)
  Tareas: T-020 | Líneas estimadas: 320 | Rama: feat/inicio-cierre-sesion-pantalla-sesiones
  Cómo probarlo: ejecutar `pnpm --filter frontend test src/auth/HomePage.test.tsx`.

- E-09 Enrutamiento completo, redirecciones, accesibilidad y resumen
  Tareas: T-021, T-022, T-023, T-024 | Líneas estimadas: 340 | Rama: feat/inicio-cierre-sesion-rutas
  Cómo probarlo: abrir `http://localhost:5173/login`, iniciar sesión, aceptar términos si están pendientes, ver y cerrar sesiones en `/` y cerrar la sesión actual, siguiendo `specs/inicio-cierre-sesion/resumen.md`.

## RF sin tarea
Ninguno.
