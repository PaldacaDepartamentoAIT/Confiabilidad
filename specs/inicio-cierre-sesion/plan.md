# Plan: inicio-cierre-sesion
Estado: aprobado

## Dependencias previas a implementar
Ninguna. No requiere `sdd-cambio` en otras features: reutiliza las funciones públicas existentes de
`apps/consents/services.py` (`consent_status`, `accept_terms`), `apps/consents/versions.py`
(`current_document`), `apps/core/fingerprints.py` (`audit_session_fingerprint`),
`apps/audit/recorder.py` (`record_event`) y los componentes de `componentes-base-accesibles` y
`sistema-de-diseno`, manteniendo intactas las rutas `/_allauth/` que prueban las suites de
`auth-headless`, `usuario-personalizado`, `cambio-contrasena` y `auditoria-eventos-seguridad`.

## Módulos

### Backend

### M-01 Modelo `UserSession` y servicio de sesiones (`apps/accounts/models.py`, `apps/accounts/sessions.py`, migración nueva)
Responsabilidad:
- Modelo `UserSession` asociado a `User` (`on_delete=models.CASCADE`, `related_name="sessions"`) con
  `session_key` (`CharField(64, unique=True)`, huella HMAC calculada con `audit_session_fingerprint`,
  nunca la clave en claro; D-02, huella HMAC en `UserSession.session_key` e índice inverso en caché),
  `ip` (`GenericIPAddressField`), `user_agent` (`TextField`, con `"unknown"` si la cabecera falta o
  está en blanco, sin recortar longitud; C-08, trato de `user_agent` vacío o largo), `created_at` y
  `last_seen_at` (`DateTimeField`, indexado).
- Índice inverso en la caché `sessions` (`user-session-key:<huella> -> <clave_en_claro>`, con el
  mismo TTL de la sesión; D-02) para comprobar si la sesión sigue viva en Redis y para borrarla del
  almacén de sesiones al revocarla sin guardar el secreto en PostgreSQL.
- Operaciones del servicio (`apps/accounts/sessions.py`):
  - `register_session(request, user)`: crea o actualiza la fila de `UserSession` al iniciar sesión y
    guarda la correspondencia en la caché `sessions`.
  - `touch_session(request, user)`: si la sesión es válida y han pasado al menos
    `SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS` (60 s por defecto), actualiza `last_seen_at`, `ip` y
    `user_agent` y renueva el TTL en la caché `sessions`.
  - `list_active_sessions(user, current_session_key)`: borra antes las filas de `user` caducadas por
    plazo (`last_seen_at <= ahora - SESSION_LIFETIME_DAYS`) o ausentes en el almacén de sesiones
    (C-01, detección y limpieza de sesiones caducadas), y devuelve las vigentes ordenadas por
    `-last_seen_at, -id` indicando `is_current`.
  - `close_current_session(request, user, session_key)`: borra la sesión del almacén, su fila de
    `UserSession` y emite/registra el cierre en auditoría.
  - `revoke_other_session(user, current_session_key, session_id)` y
    `revoke_all_other_sessions(user, current_session_key)`: invalida en el almacén de sesiones las
    afectadas, borra sus filas de `UserSession` y registra en auditoría un evento `LOGOUT` por cada
    sesión vigente efectivamente cerrada (0 eventos si no había otras sesiones activas; C-05, cierre
    sin sesión válida y cierre masivo sin otras sesiones).
  - `revoke_all_user_sessions(user)`: invalida en el almacén y borra de `UserSession` todas las
    sesiones de la cuenta cuando pasa a inactiva, se borra o cambia su contraseña (RF-003,
    invalidación inmediata al desactivar o borrar una cuenta; RF-010, invalidación de sesiones al
    cambiar o restablecer la contraseña).
  - `purge_expired()`: borra todas las filas de `UserSession` caducadas o inexistentes en el almacén
    de sesiones y devuelve cuántas borró (RF-021, limpieza de sesiones caducadas).
RF: RF-003, RF-006 (cierre de la sesión actual), RF-007 (registro de sesiones activas), RF-008
(consulta de sesiones activas), RF-009 (cierre de otra sesión o de todas las demás), RF-010, RF-021

### M-02 Invalidación automática por cuenta inactiva, borrado o cambio de contraseña (`apps/accounts/models.py`, `apps/accounts/signals.py`, `apps/audit/receivers.py`)
Responsabilidad:
- En `User.save()` y `pre_delete`: si la cuenta existía y `is_active` pasa a `False`, o si cambia el
  hash de `password`, o antes de borrarse físicamente el usuario, llama a
  `sessions.revoke_all_user_sessions(user)` (D-05, invalidación de sesiones en dos capas).
- Receptor de `password_reset_completed` y de `user_logged_in` / `user_logged_out`: sincroniza el
  alta y baja en `UserSession` también cuando el inicio o cierre ocurre por las vistas de allauth.
- Verificación de sesión activa en las vistas autenticadas y en un middleware ligero tras la
  autenticación: si `not user.is_active` (incluso si se desactivó con `QuerySet.update(is_active=False)`
  sin pasar por `User.save()`) o la sesión fue revocada, invalida la sesión en Redis, borra su fila
  de `UserSession` y rechaza la petición como no autenticada (`401`).
RF: RF-003, RF-006, RF-007, RF-010

### M-03 Adaptador de allauth y límites de inicio de sesión (`apps/audit/adapters.py`, `apps/accounts/throttling.py`, `apps/accounts/conf.py`, `config/settings.py`, `backend/.env.example`)
Responsabilidad:
- En `AuditAccountAdapter.pre_login` (`apps/audit/adapters.py`): cuando `not user.is_active`, además
  de registrar el evento `LOGIN` fallido con `reason="inactive_account"`, consume un intento en el
  limitador `login_failed` de allauth (D-03, cómputo de intentos fallidos en cuenta inactiva; C-02,
  bloqueo por intentos en cuenta inactiva). Así allauth sigue siendo la única fuente del bloqueo
  (RF-006 de `auditoria-eventos-seguridad`, fuente única de intentos fallidos) y una cuenta inactiva
  con contraseña correcta se bloquea en el mismo intento (el 6.º por defecto) que una contraseña
  incorrecta, registrando `too_many_login_attempts` y `LOCKOUT` una vez bloqueada.
- En `apps/accounts/throttling.py` y `apps/accounts/conf.py`: `check_login_ip(ip)` con ventana
  deslizante de 60 segundos y tope `LOGIN_RATE_IP_PER_MINUTE` (30 por defecto; RF-005, límite de
  frecuencia por IP en el inicio de sesión).
- Configuración en `config/settings.py` y `backend/.env.example` (RF-020, valores configurables):
  `LOGIN_MAX_FAILED_ATTEMPTS` (5), `LOGIN_LOCKOUT_MINUTES` (5, conectado a
  `ACCOUNT_RATE_LIMITS["login_failed"]`), `LOGIN_RATE_IP_PER_MINUTE` (30),
  `SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS` (60) y `SESSION_LIFETIME_DAYS` (14, conectado a
  `SESSION_COOKIE_AGE`).
RF: RF-002 (rechazo neutro de credenciales inválidas o cuenta inactiva), RF-004 (bloqueo temporal
por intentos fallidos), RF-005, RF-020

### M-04 API de inicio y cierre de sesión, términos y sesiones activas (`apps/accounts/api/auth_views.py`, `apps/accounts/api/auth_serializers.py`, `apps/accounts/api/urls.py`, `apps/accounts/api/messages.py`)
Responsabilidad: seis rutas por cliente bajo `/api/{browser,app}/v1/auth/...`, con CSRF obligatorio
en la variante `browser` (reutilizando `_enforce_csrf` de `apps/accounts/api/views.py`) y token en
cabecera `X-Session-Token` en la variante `app` (D-01, vistas propias bajo `/api/.../auth/`; D-04,
autenticación común para ambos clientes; RF-018, clientes web y de escritorio; RF-019, idioma de
pantallas y mensajes):
- `POST /api/{browser,app}/v1/auth/login`:
  1. Resuelve el idioma (`request_language`).
  2. Comprueba `throttling.check_login_ip(ip)` → `429` con `retry_after` y cabecera `Retry-After`,
     sin evento de auditoría (RF-005).
  3. Comprueba si la petición ya trae una sesión activa válida → `400`
     `{"code": "already_authenticated", "message": ...}` sin alterar la sesión ni `UserSession`
     (RF-001, acceso con correo y contraseña; C-04, rechazo de login con sesión activa).
  4. Valida el JSON (`email`, `password`) → `400` con `{"errors": ...}` si falta algún campo o el
     correo no tiene formato válido.
  5. Ejecuta la autenticación con el adaptador de allauth:
     - Si salta el bloqueo de allauth (`too_many_login_attempts`) → `400`
       `{"code": "too_many_login_attempts", "message": ...}` (RF-004).
     - Si las credenciales no coinciden, el correo no existe o la cuenta está inactiva → `400`
       `{"code": "invalid_credentials", "message": ...}`, con idéntico código, cuerpo, cabeceras y
       cookies en los tres casos (RF-002; S-03, rechazo neutro de cuenta inactiva).
     - Si la cuenta está activa y las credenciales son válidas → inicia la sesión, crea la fila en
       `UserSession`, registra el evento `LOGIN` exitoso y responde `200` con `user` (`email`,
       `name`), `terms_status` (`accepted`, `not_accepted`, `no_current_version`), `terms` (el
       documento vigente en el idioma de la solicitud cuando `terms_status == "not_accepted"`, o
       `null`) y, en la variante `app`, `session_token` (RF-001, RF-007).
- `GET /api/{browser,app}/v1/auth/session` (con `ensure_csrf_cookie` en `browser`):
  - Si no hay sesión válida o la cuenta está inactiva → `401`
    `{"code": "unauthenticated", "message": ...}`.
  - Si es válida → actualiza la actividad si corresponde (`touch_session`) y responde `200` con
    `user`, `terms_status` y `terms`.
- `POST /api/{browser,app}/v1/auth/logout`:
  - Si no hay sesión válida → `401` sin registrar evento de auditoría (RF-006, C-05).
  - Si hay sesión válida → invalida la sesión en el servidor, borra su fila de `UserSession`,
    registra `LOGOUT` exitoso y responde `200` `{"result": "logged_out"}` (permitido aunque falten
    los términos vigentes; RF-006; RF-011, bloqueo del área privada mientras falten los términos
    vigentes).
- `POST /api/{browser,app}/v1/auth/terms/accept`:
  - Exige sesión válida (`401` si no la hay). Valida `version`, `locale` y `accepted` con las mismas
    reglas y códigos de RF-004 de `registro-api` (términos obligatorios: `terms_not_accepted`,
    `document_not_found`, `wrong_kind`, `no_current_version`, `not_current_document`), llama a
    `consents.services.accept_terms` y responde `200` `{"terms_status": "accepted"}` (RF-012,
    aceptación de los términos vigentes con sesión iniciada).
- `GET /api/{browser,app}/v1/auth/sessions`:
  - Exige sesión válida (`401`) y comprueba en cada petición `consent_status(user).terms` (RF-011;
    C-06, comprobación de términos en cada petición privada): si no es `ACCEPTED`, responde `403`
    `{"code": "terms_required", "terms_status": ..., "message": ...}`.
  - Limpia las sesiones caducadas de la cuenta y devuelve `200` `{"sessions": [...]}` con `id`, `ip`,
    `user_agent`, `created_at`, `last_seen_at` e `is_current` (RF-008).
- `POST /api/{browser,app}/v1/auth/sessions/revoke` y `.../sessions/revoke-others`:
  - Exigen sesión válida (`401`), CSRF en `browser` y términos vigentes aceptados (`403`
    `terms_required`; RF-011, C-06).
  - `revoke` recibe `{"session_id": int}`: si es la sesión actual → `400`
    `{"code": "cannot_revoke_current_session", "message": ...}`; si no existe o es de otra cuenta →
    `404` `{"code": "not_found", "message": ...}`; si es otra sesión activa de la cuenta → la
    invalida, borra su fila, registra `LOGOUT` y responde `200` `{"result": "revoked"}` (RF-009).
  - `revoke-others` cierra todas las demás sesiones activas de la cuenta y responde `200`
    `{"result": "revoked", "revoked_count": <n>}` (con `revoked_count: 0` y sin eventos si solo
    estaba abierta la actual; RF-009, C-05).
RF: RF-001, RF-002, RF-003, RF-004, RF-005, RF-006, RF-007, RF-008, RF-009, RF-011, RF-012, RF-018, RF-019

### M-05 Comando de consola y tarea programada de limpieza (`apps/accounts/management/commands/purge_expired_sessions.py`, `apps/accounts/tasks.py`, `config/settings.py`)
Responsabilidad:
- Comando `python manage.py purge_expired_sessions` que ejecuta `sessions.purge_expired()` e imprime
  `<N> expired user sessions deleted.` (RF-021; P-03, backend verificable desde CLI).
- Tarea Celery `apps.accounts.tasks.purge_expired_sessions` registrada cada hora (`3600.0` s) en
  `CELERY_BEAT_SCHEDULE` (RF-021).
RF: RF-021

### Frontend

### M-06 Cliente de autenticación y almacenamiento de token para escritorio (`frontend/src/api/client.ts`, `frontend/src/api/auth.ts`, `frontend/src/auth/tokenStorage.ts`)
Responsabilidad:
- `TokenStorage` para el cliente `app` (Tauri): guarda, lee y borra el `session_token` en
  `localStorage` (con respaldo en memoria si el almacenamiento no está disponible).
- En `frontend/src/api/client.ts`: en modo `app`, adjunta `X-Session-Token` cuando existe un token
  guardado; interpreta además `401` como `{ kind: "unauthenticated" }` y `403` con
  `code === "terms_required"` como `{ kind: "termsRequired", termsStatus }`.
- Funciones tipadas en `frontend/src/api/auth.ts`: `getSession`, `login`, `logout` (que en un bloque
  `finally` borra siempre el token local aunque el servidor responda `401` o falle la red; RF-006;
  S-07, limpieza local garantizada al cerrar sesión), `acceptTerms`, `listSessions`, `revokeSession`
  y `revokeOtherSessions`.
RF: RF-006, RF-008, RF-009, RF-011, RF-012, RF-018, RF-019

### M-07 Enrutamiento, guardia de sesión y enlaces con registro (`frontend/src/App.tsx`, `frontend/src/registration/RegisterPage.tsx`, `frontend/src/registration/DonePage.tsx`, `frontend/src/i18n/locales/`)
Responsabilidad:
- Rutas en `App.tsx` (C-07, rutas de navegación del cliente; RF-013, pantalla de inicio de sesión y
  enlaces con el registro; RF-017, redirecciones según el estado de la sesión):
  - `/`: área privada (`HomePage`), redirige a `/login` sin sesión o a `/terms` si `terms_status !== "accepted"`.
  - `/terms`: pantalla de aceptación de términos pendientes (`TermsPage`), redirige a `/login` sin
    sesión o a `/` si `terms_status === "accepted"`.
  - `/login`: pantalla de inicio de sesión (`LoginPage`), redirige a `/` o `/terms` si ya hay sesión
    activa.
  - `/register`: formulario de registro (redirige a `/` o `/terms` si ya hay sesión activa, e incluye
    enlace a `/login`).
  - `/register/continue` y `/register/done` (que añade el enlace a `/login`; RF-013; S-08, enlace
    desde cuenta creada).
  - `/showcase`: página de muestra de componentes (`ShowcasePage`; C-07; S-10, identidad visual y
    traslado de la página de muestra).
- Textos en `es.json`, `pt-BR.json` y `en.json` manteniendo la comprobación de completitud de RF-008
  de `componentes-base-accesibles` (traducciones completas).
RF: RF-013, RF-017, RF-019

### M-08 Pantalla de inicio de sesión (`frontend/src/auth/LoginPage.tsx`)
Responsabilidad:
- Usa `PublicLayout` y `PublicPage` (`docs/identidad-visual.md`), con `TextField` (`type="email"`,
  `autoComplete="email"`), `PasswordField` (`kind="current"`, `autoComplete="current-password"`),
  botón principal de envío y enlace a `/register` (RF-013).
- Validación al salir del campo y al enviar con `useFormValidation`: correo y contraseña no vacíos y
  correo con forma de dirección (`@` con texto a ambos lados y sin espacios; RF-014, validación en el
  cliente y mensajes de error al iniciar sesión).
- Ante rechazo del servidor:
  - Por credenciales (`invalid_credentials`): muestra `FormAlert` general con el mensaje neutro,
    conserva el correo escrito y vacía el campo de contraseña (RF-014).
  - Por bloqueo (`too_many_login_attempts`) o fallo de red/servidor: muestra `FormAlert` general
    conservando el correo.
  - Por límite por IP (`rateLimited`, `429`): muestra `FormAlert` con cuenta atrás (`useCountdown`)
    y desactiva el envío hasta llegar a cero (RF-014).
- Al autenticar con éxito: navega a `/` si `terms_status === "accepted"` o a `/terms` en caso
  contrario (RF-017).
RF: RF-013, RF-014, RF-017, RF-019

### M-09 Pantalla de términos pendientes (`frontend/src/auth/TermsPage.tsx`)
Responsabilidad:
- Usa `PublicLayout` y `PublicPage` en `/terms` (RF-015, pantalla de aceptación de términos
  pendientes).
- Si `terms_status === "not_accepted"` y existe documento vigente: muestra el texto Markdown de la
  versión vigente en un bloque desplegable/legible, la casilla obligatoria `Checkbox`, el botón
  principal para confirmar la aceptación (`acceptTerms` → navega a `/`) y el botón secundario para
  cerrar la sesión actual (`logout` → `/login`) (RF-012, RF-015).
- Si `terms_status === "no_current_version"` (o no hay documento vigente): oculta la casilla y el
  botón de aceptar, muestra un `FormAlert` informando de que no es posible continuar en este momento
  y ofrece el botón para cerrar la sesión actual (RF-011, RF-015; S-06, exigencia de términos
  vigentes y fallo cerrado).
RF: RF-011, RF-012, RF-015, RF-017, RF-019

### M-10 Pantalla del área privada y gestión de sesiones (`frontend/src/auth/HomePage.tsx`, `specs/inicio-cierre-sesion/resumen.md`)
Responsabilidad:
- Usa `AppLayout` (`docs/identidad-visual.md`) en `/`, mostrando el nombre y correo de la persona
  autenticada, el botón para cerrar la sesión actual (RF-006) y el bloque de sesiones activas
  (RF-008; RF-016, área privada y gestión de sesiones en pantalla).
- En la lista de sesiones activas: muestra para cada fila su IP y fechas en monoespaciada, el agente
  de usuario, una etiqueta (`Chip`) señalando cuál es la sesión actual y, en cada una de las demás,
  un botón secundario para cerrarla individualmente (`revokeSession`). En la cabecera del bloque, un
  botón secundario para «Cerrar todas las demás sesiones» (`revokeOtherSessions`), desactivado cuando
  no hay otras sesiones abiertas aparte de la actual (RF-009, RF-016, C-05).
- Si al listar o cerrar sesiones el servidor responde `403` `terms_required` (porque entró en vigor
  una nueva versión obligatoria con la sesión abierta; D-06, comprobación de términos vigentes en
  cada petición privada; C-06) o `401` (`unauthenticated`), redirige de inmediato a `/terms` o
  `/login` respectivamente (RF-011, RF-017).
- Documentación ejecutable en `specs/inicio-cierre-sesion/resumen.md` (CF-8, guía de prueba en
  aplicación y consola).
RF: RF-006, RF-008, RF-009, RF-011, RF-016, RF-017, RF-019

## Modelo de datos
- Tabla nueva `accounts_usersession` (modelo `apps.accounts.models.UserSession`):
  - `id`: `BigAutoField` (PK).
  - `user`: `ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="sessions")`.
  - `session_key`: `CharField(max_length=64, unique=True)` — huella HMAC-SHA256 de la clave de
    sesión calculada con `audit_session_fingerprint(session_key)` (nunca la clave ni el token en
    claro; RF-007; S-09, huella HMAC de la clave de sesión).
  - `ip`: `GenericIPAddressField()`.
  - `user_agent`: `TextField(default="unknown")` — guarda `"unknown"` si la cabecera falta o está en
    blanco, y conserva la longitud completa sin recortar cuando viene informada (C-08).
  - `created_at`: `DateTimeField(default=timezone.now)`.
  - `last_seen_at`: `DateTimeField(default=timezone.now, db_index=True)`.
- Caché `sessions` (Redis, BD lógica 2):
  - `user-session-key:<huella_hmac>` → `<session_key_en_claro>`, con TTL igual a la duración de vida
    de la sesión (`SESSION_LIFETIME_DAYS`, 14 días por defecto).
- Caché `default` (Redis, BD lógica 1):
  - `login-rate:ip:<IP>` → lista de marcas de tiempo del último minuto para el límite por IP de la
    vista de inicio de sesión (`RF-005`).
  - Claves de `allauth` para el contador de intentos fallidos (`login_failed`, `RF-004`).
- Frontend:
  - En navegador (`browser`): sin almacenamiento de sesión en JS (usa cookie `HttpOnly` + cookie
    `csrftoken`).
  - En escritorio (`app`): clave `confiabilidad.sessionToken` en `localStorage` (con respaldo en
    memoria), borrada siempre al cerrar sesión o recibir `401` (RF-006, S-07).

## Decisiones

### D-01 Vistas propias bajo `/api/{browser,app}/v1/auth/...` apoyadas en allauth y `django.contrib.sessions`
Elegida: exponer las rutas de la feature bajo `/api/{browser,app}/v1/auth/...` (M-04) usando por
debajo el adaptador de allauth y el motor de sesiones de Django, sin modificar las rutas nativas
`/_allauth/...`.
Descartada: sobrescribir o envolver las vistas internas de `/_allauth/{browser,app}/v1/auth/...`.
Motivo: el cliente `frontend/src/api/client.ts` ya consume `/api/{browser,app}/v1` con su formato de
errores, idioma (`RF-019`) y límite `429` con `retry_after` (`RF-005`). Además, mantener intactas las
rutas `/_allauth/...` evita romper los tests existentes de `auth-headless`, `usuario-personalizado`
(`test_inactive_login.py`, que verifica el `401` nativo de allauth en `/_allauth/...`),
`cambio-contrasena` y `auditoria-eventos-seguridad`, cumpliendo la regla de `AGENTS.md` de no forzar
`sdd-cambio` en otras features.

### D-02 Huella HMAC en `UserSession.session_key` e índice inverso efímero en la caché `sessions`
Elegida: guardar en PostgreSQL únicamente `audit_session_fingerprint(session_key)` (HMAC-SHA256) y
mantener en la caché Redis `sessions` la correspondencia `user-session-key:<huella> -> <session_key>`
con el mismo TTL de la sesión.
Descartada: guardar la clave de sesión en claro en `UserSession.session_key`, o no borrar la sesión
de Redis al revocar otra sesión.
Motivo: guardar la clave en claro en PostgreSQL contradice RF-007 y S-09 (quien lea la tabla podría
suplantar cualquier sesión en web o escritorio, porque en allauth headless el `X-Session-Token` es la
clave de sesión). La caché Redis `sessions` ya almacena las sesiones vivas; guardar allí la
correspondencia permite tanto comprobar si una sesión sigue existiendo en Redis (RF-008, RF-021) como
borrarla de Redis al instante al cerrar otra sesión, desactivar la cuenta o cambiar la contraseña
(RF-003, RF-009, RF-010). Además, las vistas autenticadas comprueban que exista la fila vigente en
`UserSession`, por lo que aunque Redis perdiera el índice inverso, una fila borrada en `UserSession`
nunca vuelve a autenticar.

### D-03 Cómputo de intentos fallidos en cuenta inactiva mediante el limitador de allauth en `pre_login`
Elegida: en `AuditAccountAdapter.pre_login`, cuando `not user.is_active`, registrar el intento en el
limitador `login_failed` de allauth además de emitir el evento `LOGIN` con `reason="inactive_account"`,
y en la vista `/api/.../auth/login` devolver la misma respuesta `400` `invalid_credentials` que ante
contraseña errónea o correo inexistente.
Descartada: llevar un contador paralelo propio fuera de allauth, o no contar los intentos de cuentas
inactivas con contraseña correcta.
Motivo: RF-006 de `auditoria-eventos-seguridad` prohíbe contar intentos o bloquear fuera de la
librería de autenticación, y C-02 exige que una cuenta inactiva con contraseña correcta se bloquee en
el mismo intento que una contraseña incorrecta para no delatar su existencia en el sexto intento.

### D-04 Autenticación de las vistas de `/api/{browser,app}/v1/auth/...` para ambos clientes
Elegida: un autenticador común en `auth_views.py` que en las rutas `browser` lee `request.session`
(cookie) y exige CSRF en los métodos que cambian estado (`POST`), y en las rutas `app` lee la
cabecera `X-Session-Token` cargando la sesión desde `SessionStore`, verificando en ambos casos que
`user.is_active` sea `True` y que exista su fila vigente en `UserSession`.
Descartada: usar solo `SessionAuthentication` de DRF.
Motivo: `SessionAuthentication` de DRF no lee `X-Session-Token` para el cliente de escritorio Tauri
ni comprueba la vigencia de la fila en `UserSession`.

### D-05 Invalidación de sesiones por desactivación, borrado o cambio de contraseña en dos capas
Elegida: invalidar todas las sesiones de la cuenta y borrar sus filas de `UserSession` tanto al
guardar/borrar el usuario o completar un restablecimiento (`User.save()`, `pre_delete`,
`password_reset_completed`) como al detectar `not user.is_active` en cualquier petición autenticada.
Descartada: invalidar únicamente en `User.save()`.
Motivo: en Django es habitual desactivar cuentas con `User.objects.filter(...).update(is_active=False)`,
que no ejecuta `User.save()`. La doble capa garantiza que las filas y sesiones se limpien en el acto
cuando pasa por el modelo y que ninguna sesión de una cuenta inactiva pueda autenticar jamás aunque se
haya desactivado por `QuerySet.update` (RF-003, RF-010; C-03, alcance de invalidación por cambio de
contraseña).

### D-06 Comprobación de términos vigentes como guarda en el servidor y redirección reactiva en el cliente
Elegida: comprobar `consents.services.consent_status(user).terms == TermsState.ACCEPTED` en cada
petición a las vistas del área privada (`/api/.../auth/sessions`, `revoke`, `revoke-others`),
respondiendo `403` `{"code": "terms_required", "terms_status": ...}` cuando falten, y hacer que el
cliente redirija a `/terms` tanto al cargar la sesión como al recibir `terms_required`.
Descartada: comprobar los términos únicamente en el momento de iniciar sesión.
Motivo: C-06 y RF-011 exigen bloquear las operaciones del área privada también cuando entra en vigor
una versión nueva obligatoria de términos mientras la sesión ya estaba abierta.

## Estrategia de tests
Se sigue TDD estricto (P-04, TDD estricto) con cobertura de líneas ≥ 80 % en backend y frontend
(P-05, cobertura de líneas ≥ 80 %).
- **Unitarios y de modelo en backend (`apps/accounts/tests/test_user_session_model.py`, `test_sessions_service.py`)**:
  - Creación de `UserSession` con huella HMAC (nunca clave en claro), valor por defecto `"unknown"` y
    conservación de `user_agent` largo sin recortar (RF-007, C-08).
  - Intervalo de actualización de `last_seen_at` (60 s por defecto) y caducidad por tiempo o por
    ausencia en la caché `sessions` (RF-007, RF-020).
  - Invalidación de todas las sesiones al desactivar o borrar la cuenta y al cambiar o restablecer la
    contraseña por consola, panel o guardado del modelo (RF-003, RF-010, C-03).
- **Integración de API en backend (`apps/accounts/tests/test_auth_api.py`, `test_auth_neutrality.py`, `test_auth_limits.py`, `test_auth_terms_gate.py`, `test_sessions_api.py`)**:
  - Inicio de sesión exitoso en `browser` (con CSRF y cookie) y en `app` (con `X-Session-Token`),
    normalización de correo, actualización de `last_login`, creación de `UserSession` y registro en
    `SecurityEvent` (RF-001, RF-007, RF-018).
  - Rechazo cuando ya existe sesión activa en la petición sin alterar la sesión en curso (RF-001,
    C-04).
  - Indistinguibilidad de la respuesta (`400`, estructura, mensaje, cabeceras y cookies) entre correo
    inexistente, contraseña incorrecta y cuenta inactiva (con contraseña correcta o incorrecta), y
    bloqueo en el mismo intento (el 6.º), verificando que `SecurityEvent` registra `inactive_account`
    antes del bloqueo y `too_many_login_attempts` + `LOCKOUT` al bloquearse (RF-002, RF-004; CF-2,
    test de respuesta neutra y bloqueo en cuenta inactiva; CF-6, test de límites de intentos y por
    IP).
  - Límite de 30 peticiones por minuto por IP en el inicio de sesión (`429` con `retry_after`, sin
    fila en `SecurityEvent`; RF-005, RF-020, CF-6).
  - Cierre de la sesión actual en ambos clientes (invalida cookie y token, borra `UserSession`,
    registra `LOGOUT`) y respuesta `401` sin evento de auditoría cuando la sesión ya no existe
    (RF-006, C-05; CF-3, test de invalidación al cerrar sesión o desactivar cuenta).
  - Listado de sesiones activas (limpia vencidas, ordena por actividad reciente, marca `is_current` y
    no expone `session_key`), cierre de otra sesión concreta (`400` si es la actual, `404` si es
    ajena o inexistente) y cierre de todas las demás (incluyendo el caso con 0 adicionales que
    responde `200` sin eventos de auditoría) (RF-008, RF-009, C-01, C-05; CF-4, test de listado y
    cierre de otras sesiones).
  - Bloqueo por términos pendientes (`403` `terms_required`) al iniciar sesión, al no existir versión
    vigente y cuando se publica una versión obligatoria nueva con la sesión ya abierta; y desbloqueo
    tras aceptar los términos vigentes en `/api/.../auth/terms/accept` (RF-011, RF-012, C-06; CF-5,
    test de bloqueo y aceptación de términos vigentes).
  - Idioma de los mensajes en `es`, `pt-BR` y `en` (RF-019).
- **Consola y tarea periódica (`apps/accounts/tests/test_purge_expired_sessions.py`)**:
  - Comando `manage.py purge_expired_sessions` y tarea `purge_expired_sessions` borran solo las
    sesiones caducadas o ausentes en el almacén e informan del total borrado (RF-021, P-03).
- **Frontend (`frontend/src/auth/*.test.tsx`, `frontend/src/App.test.tsx`)**:
  - `LoginPage`: validación de campos al salir y al enviar, foco en el primer error, vaciado de
    contraseña tras rechazo de credenciales conservando el correo, cuenta atrás ante `429` y enlace a
    `/register` (RF-013, RF-014; CF-7, tests de pantallas y redirecciones en frontend).
  - Enlaces a `/login` en `RegisterPage` y `DonePage`, y página de muestra en `/showcase` (RF-013,
    C-07, CF-7).
  - `TermsPage`: visualización y aceptación de términos vigentes, fallo cerrado sin versión vigente y
    cierre de sesión desde `/terms` (RF-012, RF-015, CF-5, CF-7).
  - `HomePage`: visualización de usuario y sesiones activas, botón de cerrar todas las demás
    desactivado cuando solo hay una sesión, cierre de otra sesión individual, cierre de todas las
    demás, cierre de la sesión actual (incluso cuando el servidor devuelve `401` o falla la red,
    borrando el token local y llevando a `/login`) y redirección a `/terms` si una llamada devuelve
    `terms_required` (RF-006, RF-008, RF-009, RF-016, RF-017, C-05, C-06, CF-7).
  - Redirecciones entre `/`, `/login`, `/terms`, `/register` y `/showcase` según el estado de la
    sesión y de los términos (RF-017, CF-7).

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-04 (D-01, D-04) | Integración (`test_auth_api`) |
| RF-002 | M-03, M-04 (D-01, D-03) | Integración (`test_auth_neutrality`) |
| RF-003 | M-01, M-02, M-04 (D-02, D-05) | Unitario + integración (`test_sessions_service`, `test_auth_api`) |
| RF-004 | M-03, M-04 (D-03) | Integración (`test_auth_limits`, `test_auth_neutrality`) |
| RF-005 | M-03, M-04 | Integración (`test_auth_limits`) |
| RF-006 | M-01, M-02, M-04, M-06, M-10 | Integración backend (`test_auth_api`) + frontend (`HomePage.test.tsx`) |
| RF-007 | M-01, M-02 (D-02) | Unitario (`test_user_session_model`, `test_sessions_service`) + integración |
| RF-008 | M-01, M-04, M-06, M-10 | Integración backend (`test_sessions_api`) + frontend (`HomePage.test.tsx`) |
| RF-009 | M-01, M-04, M-06, M-10 | Integración backend (`test_sessions_api`) + frontend (`HomePage.test.tsx`) |
| RF-010 | M-01, M-02 (D-05) | Unitario + integración (`test_sessions_service`) |
| RF-011 | M-04, M-06, M-07, M-09, M-10 (D-06) | Integración backend (`test_auth_terms_gate`) + frontend (`TermsPage.test.tsx`, `HomePage.test.tsx`) |
| RF-012 | M-04, M-06, M-09 | Integración backend (`test_auth_terms_gate`) + frontend (`TermsPage.test.tsx`) |
| RF-013 | M-07, M-08 | Frontend (`LoginPage.test.tsx`, `RegisterPage.test.tsx`, `DonePage.test.tsx`, `App.test.tsx`) |
| RF-014 | M-08 | Frontend (`LoginPage.test.tsx`) |
| RF-015 | M-09 | Frontend (`TermsPage.test.tsx`) |
| RF-016 | M-10 | Frontend (`HomePage.test.tsx`) |
| RF-017 | M-07, M-08, M-09, M-10 | Frontend (`App.test.tsx`, `HomePage.test.tsx`, `TermsPage.test.tsx`) |
| RF-018 | M-04, M-06 (D-01, D-04) | Integración backend (`test_auth_api`, `test_sessions_api`) + frontend (`client.test.ts`, `auth.test.ts`) |
| RF-019 | M-04, M-07, M-08, M-09, M-10 | Integración backend (`test_auth_api`) + frontend (`i18n`, tests de pantallas) |
| RF-020 | M-01, M-03 | Unitario + integración (`test_auth_limits`, `test_sessions_service`) |
| RF-021 | M-01, M-05 | Comando + integración (`test_purge_expired_sessions`) |

## RF sin cobertura
Ninguno.
