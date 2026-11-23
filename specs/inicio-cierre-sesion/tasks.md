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

- [x] T-001 Valores configurables de inicio de sesión y sesiones
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
  Decisiones: `ACCOUNT_RATE_LIMITS["login_failed"]` conserva `10/m/ip` junto a
  `{LOGIN_MAX_FAILED_ATTEMPTS}/{LOGIN_LOCKOUT_MINUTES}m/key`, como el valor por defecto de allauth,
  para no bloquear por IP tras 5 intentos cuando `password_reset.complete` borra el contador por
  correo y conserva el de IP (`RF-009` de `cambio-contrasena`) — [Cierto] — revertir: cambiar la
  cadena en `settings.py`. Validación pendiente en la máquina virtual del usuario (alternativa sin
  dependencias locales de `AGENTS.md`).

- [x] T-002 Límite por IP del inicio de sesión
  RF: RF-005 (límite de frecuencia por IP en el inicio de sesión), RF-020 (M-03) | Depende de: T-001 (valores configurables de inicio de sesión y sesiones) | Archivos: 2
  Archivos: `throttling.py`, `tests/test_auth_throttling.py`.
  Hecho cuando: `check_login_ip` permite 30 solicitudes por minuto desde una misma IP y rechaza la
  31.ª devolviendo `allowed=False` y los segundos de espera (`retry_after`), con una clave propia en
  caché independiente de las del registro; suite verde.
  Decisiones: `_check` admite un parámetro `window` con valor por defecto `_HOUR` para reutilizar el
  mismo registro deslizante con ventana de 60 s (`_MINUTE`) sin cambiar las funciones del registro —
  [Cierto] — revertir: separar una función propia para la ventana de un minuto. Validación pendiente
  en la máquina virtual del usuario.

- [x] T-003 Bloqueo por intentos fallidos en cuenta inactiva
  RF: RF-002 (rechazo neutro de credenciales inválidas o cuenta inactiva), RF-004 (bloqueo temporal por intentos fallidos; M-03; D-03, cómputo de intentos fallidos en cuenta inactiva; C-02, bloqueo por intentos en cuenta inactiva) | Depende de: T-001 | Archivos: 2
  Archivos: `backend/apps/audit/adapters.py`, `tests/test_inactive_login.py`.
  Hecho cuando: en `AuditAccountAdapter.pre_login`, un intento sobre una cuenta inactiva con
  contraseña correcta registra `inactive_account` en `SecurityEvent` y consume un intento en el
  limitador `login_failed` de allauth, de modo que al sexto intento consecutivo se bloquea con
  `too_many_login_attempts` y genera el evento `LOCKOUT`, igual que con contraseña incorrecta, sin
  romper los tests existentes de `test_inactive_login.py`; suite verde.
  Decisiones: `pre_login` consume el intento directamente con `allauth_ratelimit.consume` (con
  `action="login_failed"` y la clave de `_get_login_attempts_cache_key`) porque
  `DefaultAccountAdapter.authentication_failed` no consume el límite por sí solo en allauth 65.x —
  [Cierto] — revertir: quitar `_consume_login_failed` de `pre_login`. Validación pendiente en la
  máquina virtual del usuario.

- [x] T-004 Modelo `UserSession`
  RF: RF-007 (registro de sesiones activas; M-01, modelo `UserSession` y servicio de sesiones; D-02, huella HMAC en `UserSession.session_key` e índice inverso en caché; C-08, trato de `user_agent` vacío o largo; S-09, huella HMAC de la clave de sesión) | Depende de: — | Archivos: 3
  Archivos: `models.py`, `migrations/0015_usersession.py`, `tests/test_user_session_model.py`.
  Hecho cuando: `UserSession` guarda `user`, `session_key` (único de 64 caracteres), `ip`,
  `user_agent` (`"unknown"` si falta o está en blanco, y longitud completa sin recortar cuando viene
  informada), `created_at` y `last_seen_at` (indexado); `python manage.py makemigrations --check` no
  propone nada; suite verde.
  Decisiones: `UserSession.user_agent` admite `blank=True` y normaliza valores vacíos o de solo
  espacios a `"unknown"` en `save()`, conservando el valor íntegro sin recortar cuando tiene
  contenido (`C-08`) — [Cierto] — revertir: mover la normalización solo al servicio. Validación
  pendiente en la máquina virtual del usuario.

- [x] T-005 Servicio de sesiones: alta, actividad, consulta y cierre actual
  RF: RF-006 (cierre de la sesión actual), RF-007, RF-008 (consulta de sesiones activas; M-01, D-02; C-01, detección y limpieza de sesiones caducadas; C-08) | Depende de: T-001, T-004 (modelo `UserSession`) | Archivos: 2
  Archivos: `sessions.py`, `tests/test_sessions_service.py`.
  Hecho cuando: `register_session` guarda la fila en `UserSession` con la huella HMAC
  (`audit_session_fingerprint`), nunca la clave en claro, y el índice inverso en la caché
  `sessions`; `touch_session` actualiza `last_seen_at`, `ip` y `user_agent` solo cuando han pasado
  al menos 60 s; `list_active_sessions` borra las vencidas o ausentes en la caché y devuelve las
  vigentes ordenadas de más reciente a más antigua con `is_current`; `close_current_session` borra
  la sesión de la caché y su fila de `UserSession`; suite verde.
  Decisiones: `sessions.py` mantiene un índice inverso efímero (`user-session-key:<huella>`) en
  `caches[settings.SESSION_CACHE_ALIAS]` con el TTL de `conf.session_lifetime()` para comprobar la
  existencia y borrar la sesión de Redis sin almacenar la clave en claro en PostgreSQL (`D-02`) —
  [Cierto] — revertir: cambiar el almacén de índice en `sessions.py`. Validación pendiente en la
  máquina virtual del usuario.

- [x] T-006 Servicio de sesiones: cierre de otras sesiones, invalidación masiva y purga
  RF: RF-003 (invalidación inmediata al desactivar o borrar una cuenta), RF-009 (cierre de otra sesión o de todas las demás), RF-010 (invalidación de sesiones al cambiar o restablecer la contraseña), RF-021 (limpieza de sesiones caducadas; M-01, D-02; C-01; C-05, cierre sin sesión válida y cierre masivo sin otras sesiones) | Depende de: T-005 (servicio de sesiones: alta, actividad, consulta y cierre actual) | Archivos: 2
  Archivos: `sessions.py`, `tests/test_sessions_service.py`.
  Hecho cuando: `revoke_other_session` rechaza cerrar la sesión actual y una inexistente o ajena, y
  al cerrar otra sesión válida la borra de la caché `sessions`, borra su fila y registra `LOGOUT` en
  `SecurityEvent`; `revoke_all_other_sessions` cierra todas las demás y registra un `LOGOUT` por
  cada una vigente (0 eventos si solo está la actual); `revoke_all_user_sessions` borra todas las de
  la cuenta; `purge_expired` borra todas las caducadas o sin entrada en caché y devuelve el total;
  suite verde.
  Decisiones: al revocar otra sesión o todas las demás, `sessions.py` emite la señal estándar
  `django.contrib.auth.signals.user_logged_out` con un `HttpRequest` construido con `_session_store(raw_key)`
  y los metadatos de la petición o de la fila revocada, manteniendo `apps/accounts` desacoplada de
  `apps/audit` y sin señales adicionales — [Cierto] — revertir: añadir una señal propia en
  `apps/accounts/signals.py`. Validación pendiente en la máquina virtual del usuario.

- [x] T-007 Sincronización automática de sesiones al entrar, salir, desactivar, borrar o cambiar contraseña
  RF: RF-003, RF-006, RF-007, RF-010 (M-02, invalidación automática por cuenta inactiva, borrado o cambio de contraseña; D-05, invalidación de sesiones en dos capas; C-03, alcance de invalidación por cambio de contraseña) | Depende de: T-006 (servicio de sesiones: cierre de otras sesiones, invalidación masiva y purga) | Archivos: 3
  Archivos: `models.py`, `sessions.py`, `tests/test_sessions_lifecycle.py`.
  Hecho cuando: iniciar o cerrar sesión mediante las señales de autenticación crea o borra la fila
  de `UserSession`; desactivar (`is_active=False`) o borrar físicamente un usuario, cambiar su
  contraseña en `User.save()` o completar `password_reset.complete` invalida sus sesiones en la
  caché `sessions` y vacía sus filas de `UserSession`; suite verde.
  Decisiones: los receptores de ciclo de vida (`user_logged_in`, `user_logged_out`, `pre_delete` y
  `password_reset_completed`) se registran en `models.py` (donde ya vive `_leave_password_reset_tombstone`
  y que se carga al arrancar Django) importando `sessions` dentro de cada gancho para evitar
  importaciones circulares sin tocar `apps.py` — [Cierto] — revertir: mover los receptores a
  `sessions.py` e importarlo en `apps.py`. Al cambiar la contraseña con la cuenta activa,
  `revoke_all_user_sessions(..., clear_only=True)` vacía el contenido de la sesión en Redis y borra
  su fila de `UserSession` en vez de borrar la clave de Redis, de modo que deja de autenticar pero
  `/_allauth/app/v1/auth/session` sigue respondiendo `401` y no `410` (preservando S-03 y CF-3 de
  `cambio-contrasena` sin `sdd-cambio`) — [Cierto] — revertir: pasar `clear_only=False`. Validación
  pendiente en la máquina virtual del usuario.

- [x] T-008 Limpieza de sesiones caducadas por consola y tarea periódica
  RF: RF-021 (M-05, comando de consola y tarea programada de limpieza; P-03, backend verificable desde CLI) | Depende de: T-006 | Archivos: 4
  Archivos: `management/commands/purge_expired_sessions.py`, `tasks.py`,
  `backend/config/settings.py`, `tests/test_purge_expired_sessions.py`.
  Hecho cuando: `python manage.py purge_expired_sessions` y la tarea Celery
  `apps.accounts.tasks.purge_expired_sessions` (programada cada 3600 s en `CELERY_BEAT_SCHEDULE`)
  borran las filas caducadas o sin sesión viva e informan del número borrado; suite verde.
  Excepción: el comando, la tarea, su programación en `settings.py` y su test deben ir juntos para
  verificar tanto la orden de consola como la tarea periódica de RF-021.
  Decisiones: el comando imprime `<N> expired user sessions deleted.` sin `--dry-run`, ya que RF-021
  solo pide borrar e informar cuántos borró — [Cierto] — revertir: añadir `--dry-run` como en
  `purge_security_events`. Validación pendiente en la máquina virtual del usuario.

- [x] T-009 Textos de la API de inicio y cierre de sesión en tres idiomas
  RF: RF-019 (idioma de pantallas y mensajes; M-04, API de inicio y cierre de sesión, términos y sesiones activas) | Depende de: — | Archivos: 2
  Archivos: `api/messages.py`, `tests/test_registration_api_messages.py`.
  Hecho cuando: `invalid_credentials`, `too_many_login_attempts`, `already_authenticated`,
  `unauthenticated`, `terms_required` y `cannot_revoke_current_session` tienen texto en `es`,
  `pt-BR` y `en`, y el test de completitud de mensajes pasa; suite verde.
  Decisiones: validación pendiente en la máquina virtual del usuario (alternativa sin dependencias
  locales de `AGENTS.md`).

- [x] T-010 Rutas de inicio de sesión, consulta de sesión actual y cierre de sesión
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
  Decisiones: `AppSessionView` en `browser` (`BrowserSessionView`) se decora con
  `ensure_csrf_cookie` para que la consulta inicial de sesión entregue la cookie `csrftoken` al
  navegador antes del login; en `app`, `AppLogoutView` asigna `user` y `session` al `HttpRequest`
  subyacente antes de `django.contrib.auth.logout` para reutilizar el mismo receptor de auditoría —
  [Cierto] — revertir: emitir `user_logged_out` manualmente para `app`. Validación pendiente en la
  máquina virtual del usuario.

- [x] T-011 Test de neutralidad y bloqueo en el inicio de sesión
  RF: RF-002, RF-004 (CF-2, CF-6) | Depende de: T-010 (rutas de inicio de sesión, consulta de sesión actual y cierre de sesión) | Archivos: 3
  Archivos: `api/auth_views.py`, `apps/audit/adapters.py`, `tests/test_auth_neutrality.py`.
  Hecho cuando: un test demuestra que correo inexistente, contraseña incorrecta y cuenta inactiva
  (con contraseña correcta o incorrecta) reciben en `/api/{browser,app}/v1/auth/login` el mismo
  código (`400`), cuerpo, cabeceras y cookies en los intentos 1 a 5 y el mismo bloqueo
  (`too_many_login_attempts`) en el 6.º, mientras que `SecurityEvent` registra `inactive_account`
  antes del bloqueo cuando la contraseña de la cuenta inactiva es correcta; suite verde.
  Decisiones: cada caso usa su propia IP aleatoria para no disparar el límite por IP (`RF-005`)
  antes del 6.º intento por cuenta y un correo con sufijo aleatorio para aislar contadores de
  Redis entre ejecuciones — [Cierto] — revertir: fijar correos/IPs estáticos si la suite limpia
  la caché de sesiones entre parametrizaciones. Validación pendiente en la máquina virtual del
  usuario (alternativa sin dependencias locales de `AGENTS.md`).

- [x] T-012 Ruta de aceptación de términos vigentes y guarda del área privada
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
  Decisiones: `TermsAcceptSerializer` reutiliza `RegistrationSerializer().validate_terms` desde
  `run_validation` para conservar exactamente las mismas reglas y códigos de RF-004 de
  `registro-api` sin duplicar código — [Cierto] — revertir: extraer una función compartida en
  `serializers.py`. Validación pendiente en la máquina virtual del usuario (alternativa sin
  dependencias locales de `AGENTS.md`).

- [x] T-013 Rutas de listado y cierre de otras sesiones activas
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
  Decisiones: en `sessions/revoke` se reutiliza la clave `not_found` ya presente en `messages.py`
  para sesiones inexistentes o ajenas, y en `sessions/revoke-others` con 0 otras sesiones se
  responde igualmente `200 {"result": "revoked", "revoked_count": 0}` sin tocar eventos —
  [Cierto] — revertir: añadir una clave de mensaje específica `session_not_found`. Validación
  pendiente en la máquina virtual del usuario (alternativa sin dependencias locales de `AGENTS.md`).

## Frontend

- [x] T-014 Almacenamiento de token para escritorio y soporte de autenticación en el cliente API
  RF: RF-006, RF-011, RF-018 (M-06, cliente de autenticación y almacenamiento de token para escritorio; S-07, limpieza local garantizada al cerrar sesión) | Depende de: — | Archivos: 3
  Archivos: `auth/tokenStorage.ts`, `api/client.ts`, `api/client.test.ts`.
  Hecho cuando: en modo `app`, el cliente adjunta `X-Session-Token` cuando hay token guardado en
  `TokenStorage`; `client.ts` interpreta `401` como `{ kind: "unauthenticated" }` y `403` con
  `code: "terms_required"` como `{ kind: "termsRequired", termsStatus }`, conservando el resto de
  respuestas existentes; suite verde.
  Decisiones: `createTokenStorage` usa `localStorage` como fuente de verdad cuando está disponible
  y cae a memoria solo si el acceso lanza error o no existe — [Cierto] — revertir: priorizar el
  valor en memoria sobre `localStorage`.

- [x] T-015 Llamadas de la API de autenticación y sesiones
  RF: RF-001, RF-006, RF-008, RF-009, RF-012, RF-018 (M-06, S-07) | Depende de: T-014 (almacenamiento de token para escritorio y soporte en el cliente API) | Archivos: 2
  Archivos: `api/auth.ts`, `api/auth.test.ts`.
  Hecho cuando: existen funciones tipadas `getSession`, `login` (que en modo `app` guarda el
  `session_token` recibido), `logout` (que borra siempre el token local en `finally`, aunque el
  servidor devuelva `401` o falle la red), `acceptTerms`, `listSessions`, `revokeSession` y
  `revokeOtherSessions`; suite verde.

- [x] T-016 Textos de inicio de sesión, términos pendientes y sesiones activas en tres idiomas
  RF: RF-013 (pantalla de inicio de sesión y enlaces con el registro), RF-014 (validación en el cliente y mensajes de error al iniciar sesión), RF-015 (pantalla de aceptación de términos pendientes), RF-016 (área privada y gestión de sesiones en pantalla), RF-019 (M-07, enrutamiento, guardia de sesión y enlaces con registro) | Depende de: — | Archivos: 4
  Archivos: `i18n/locales/es.ts`, `i18n/locales/pt-BR.ts`, `i18n/locales/en.ts`,
  `i18n/locales/locales.test.ts`.
  Hecho cuando: existen en los tres idiomas los textos de inicio de sesión, enlaces entre login y
  registro, pantalla de términos pendientes, área privada y gestión de sesiones, y códigos de error
  nuevos; `locales.test.ts` pasa; suite verde.
  Excepción: los tres archivos de idioma y el test que verifica la paridad de claves y grupos deben
  actualizarse juntos para no romper la comprobación de RF-008 de `componentes-base-accesibles`
  (traducciones completas).

- [x] T-017 Traducción de errores de inicio de sesión y términos en el cliente
  RF: RF-012, RF-014, RF-019 (M-08, pantalla de inicio de sesión; M-09, pantalla de términos pendientes) | Depende de: T-016 (textos en tres idiomas) | Archivos: 2
  Archivos: `registration/serverErrors.ts`, `registration/serverErrors.test.ts`.
  Hecho cuando: `serverErrors` traduce `invalid_credentials`, `too_many_login_attempts`,
  `already_authenticated` y `cannot_revoke_current_session` a sus claves de traducción, manteniendo
  todos los códigos existentes; suite verde.

- [x] T-018 Pantalla de inicio de sesión (sin ruta)
  RF: RF-013, RF-014, RF-019 (M-08; CF-7, tests de pantallas y redirecciones en frontend) | Depende de: T-015 (llamadas de la API de autenticación y sesiones), T-017 (traducción de errores en el cliente) | Archivos: 2
  Archivos: `auth/LoginPage.tsx`, `auth/LoginPage.test.tsx`.
  Hecho cuando: `LoginPage` valida al salir y al enviar que el correo y la contraseña no estén
  vacíos y que el correo tenga forma de dirección, enfocando el primer campo con error sin llamar al
  servidor; ante `invalid_credentials` muestra el error general, conserva el correo y vacía la
  contraseña; ante `too_many_login_attempts` o fallo de red muestra el error general conservando el
  correo; ante `429` muestra la cuenta atrás y desactiva el botón hasta cero; incluye el enlace a
  `/register` y notifica al autenticar con éxito; suite verde.
  Decisiones: al recibir `invalid_credentials` se vacía el `<input>` de contraseña mediante `ref`
  para mantener el formulario no controlado compatible con `useFormValidation` — [Cierto] —
  revertir: controlar el valor del campo en estado React. Validación pendiente en la máquina
  virtual del usuario (alternativa sin dependencias locales de `AGENTS.md`).

- [x] T-019 Pantalla de términos pendientes y conexión de rutas `/login` y `/terms`
  RF: RF-011, RF-012, RF-013, RF-015, RF-019 (M-09, CF-5, CF-7) | Depende de: T-015, T-017 | Archivos: 4
  Archivos: `auth/TermsPage.tsx`, `auth/TermsPage.test.tsx`, `App.tsx`, `App.test.tsx`.
  Hecho cuando: con `terms_status === "not_accepted"`, `TermsPage` muestra el documento vigente en
  Markdown, exige marcar la casilla antes de enviar, llama a `acceptTerms` y notifica el paso al
  área privada, o permite cerrar la sesión actual (`logout`, incluso si falla la red); con
  `no_current_version`, oculta el formulario de aceptación, informa de que no se puede continuar y
  ofrece cerrar la sesión; y `App.tsx` expone `/login` y `/terms` para ver ambas pantallas en el
  navegador; suite verde.
  Excepción: 4 archivos para conectar `/login` y `/terms` en `App.tsx` y `App.test.tsx` dentro de
  la misma entrega visual según la regla de visibilidad en `AGENTS.md`.
  Decisiones: reutiliza `DocumentCheckbox` (de `casilla-con-documento`) para mostrar el documento en
  Markdown dentro del modal del sistema de diseño y sincronizar el estado de la casilla — [Cierto] —
  revertir: pintar un `<Markdown>` en línea más un `<Checkbox>` simple. Validación pendiente en la
  máquina virtual del usuario (alternativa sin dependencias locales de `AGENTS.md`).

- [x] T-020 Pantalla del área privada, gestión de sesiones y rutas `/` y `/showcase`
  RF: RF-006, RF-008, RF-009, RF-011, RF-016, RF-017 (redirecciones según el estado de la sesión), RF-019 (M-10, pantalla del área privada y gestión de sesiones; C-05, C-06, CF-4, CF-7) | Depende de: T-015, T-016 | Archivos: 12
  Archivos: `auth/HomePage.tsx`, `auth/HomePage.test.tsx`, `layouts/AppLayout.css`, `App.tsx`,
  `App.test.tsx`, `showcase/ShowcasePage.test.tsx`, `showcase/a11y.test.tsx`, `visual/app.ts`,
  `visual/compare.visual.test.ts`, `visual/contrast.visual.test.ts`,
  `visual/document-modal.visual.test.ts`, `visual/smoke.visual.test.ts`.
  Hecho cuando: `HomePage` muestra con `AppLayout` el nombre y correo del usuario, el botón de
  cerrar la sesión actual (que limpia el cliente y lleva a `/login` incluso si el servidor da `401`
  o falla la red) y la tabla de sesiones activas señalando la actual; permite cerrar otra sesión
  individual o todas las demás; desactiva el botón «Cerrar todas las demás sesiones» cuando solo
  existe la sesión actual; si recibe `termsRequired` (`403`) o `unauthenticated` (`401`) al
  consultar o revocar sesiones, redirige a `/terms` o `/login`; y `App.tsx` expone `/` (`HomePage`) y
  `/showcase` (`ShowcasePage`) para verlas en el navegador; suite verde.
  Excepción: exponer `HomePage` en `/` y mover `ShowcasePage` a `/showcase` dentro de esta misma
  entrega exige actualizar los tests de `App`, `showcase` y `visual` que asumían el catálogo en `/`.
  Decisiones: `HomePage` reutiliza `Block` (con `count`), `Table` seleccionable (`kind: "code"` en IP
  y fechas, columnas redimensionables y barra superpuesta sobre la cabecera al seleccionar), `Chip`
  e `IconButton` (con `IconLogOut` de `28 × 28 px` y tooltip hacia arriba en la barra de selección)
  del sistema de diseño; conecta «Cerrar sesión» al menú de usuario en `Sidebar` (sin bloque
  separado de «Sesión iniciada»); y añade `.content > h1` (24 px, peso 600) en `AppLayout.css` según
  `docs/identidad-visual.md` — [Cierto] — revertir: crear un CSS propio `HomePage.css`. Validación
  pendiente en la máquina virtual del usuario (alternativa sin dependencias locales de `AGENTS.md`).

- [x] T-021 Enlaces a `/login` desde el formulario de registro y desde cuenta creada
  RF: RF-013 (M-07; S-08, enlace desde cuenta creada; CF-7) | Depende de: T-016 | Archivos: 3
  Archivos: `registration/RegisterPage.tsx`, `registration/DonePage.tsx`,
  `registration/RegisterPage.test.tsx`.
  Hecho cuando: tanto la pantalla de registro (`/register`) como la de cuenta creada
  (`/register/done`) muestran un enlace a `/login` que navega sin recargar la página; suite verde.
  Decisiones: en `RegisterPage` el enlace «Iniciar sesión» comparte la fila `.public-actions-row`
  como botón secundario junto al botón principal de envío (en simetría con `LoginPage`), y en
  `DonePage` se muestra como botón principal — [Cierto] — revertir: mostrar enlaces de texto bajo
  el botón. Validación pendiente en la máquina virtual del usuario (alternativa sin dependencias
  locales de `AGENTS.md`).

- [x] T-022 Rutas y redirecciones según el estado de la sesión y de los términos
  RF: RF-013, RF-015, RF-016, RF-017 (M-07; C-07, rutas de navegación del cliente; S-10, identidad visual y traslado de la página de muestra; CF-5, CF-7) | Depende de: T-018 (pantalla de inicio de sesión), T-019 (pantalla de términos pendientes), T-020 (pantalla del área privada), T-021 (enlaces a `/login`) | Archivos: 3
  Archivos: `App.tsx`, `App.test.tsx`, `registration/VerifyPage.test.tsx`.
  Hecho cuando: `/` muestra el área privada, `/login` el inicio de sesión, `/terms` los términos
  pendientes y `/showcase` la página de muestra; abrir `/` o `/terms` sin sesión redirige a
  `/login`; abrir `/login` o `/register` con sesión activa redirige a `/` (si los términos están
  aceptados) o a `/terms` (si faltan); abrir `/` con términos pendientes redirige a `/terms` y abrir
  `/terms` con ellos aceptados redirige a `/`; suite verde.
  Decisiones: `App.tsx` mantiene un caché en memoria de `session` (`undefined` antes de consultar,
  `null` sin sesión, `SessionInfo` con sesión) y verifica `getSession` en `/login`, `/register` y
  `/terms` después del montaje inicial para conservar el orden de llamada inicial de `RegisterPage`
  — [Cierto] — revertir: consultar sesión antes de montar las pantallas públicas. Validación
  pendiente en la máquina virtual del usuario (alternativa sin dependencias locales de `AGENTS.md`).

- [x] T-023 Accesibilidad de las pantallas de inicio de sesión, términos pendientes y área privada
  RF: RF-013, RF-015, RF-016 (CF-1, tests para cada RF y análisis estático limpio; CF-7) | Depende de: T-022 (rutas y redirecciones) | Archivos: 1
  Archivos: `auth/a11y.test.tsx`.
  Hecho cuando: `axe-core` no encuentra fallos en `LoginPage` (normal y con errores), `TermsPage`
  (con términos pendientes y sin versión vigente) y `HomePage` (con una y varias sesiones); suite
  verde.
  Decisiones: desactiva la regla `color-contrast` en jsdom como en el resto de pruebas unitarias
  del repositorio (el contraste real se valida en Chromium en `visual/contrast.visual.test.ts`), y
  fija límite de `15_000 ms` por test para evitar expiraciones bajo carga paralela — [Cierto] —
  revertir: usar el tiempo límite por defecto. Validación pendiente en la máquina virtual del usuario.

- [x] T-024 Resumen de la feature y guía de prueba
  RF: RF-001…RF-021 (M-10; CF-8, guía de prueba en aplicación y consola) | Depende de: T-013 (rutas de listado y cierre de otras sesiones), T-023 (accesibilidad de las pantallas) | Archivos: 1
  Archivos: `specs/inicio-cierre-sesion/resumen.md`.
  Hecho cuando: `resumen.md` explica qué se hizo, su marco teórico y los pasos ejecutables para
  probar en la aplicación y con `curl` / `manage.py` el inicio y cierre de sesión en ambos clientes,
  la cuenta inactiva, los límites, los términos pendientes, el listado y cierre de otras sesiones y
  la purga de sesiones caducadas.
  Decisiones: documenta el estado real tras las entregas `E-01`..`E-09` (incluida la selección con
  casillas en sesiones, barra superpuesta, menús de `Sidebar` hacia arriba e `IconButton`) — [Cierto]
  — revertir: resumir solo la versión previa de la pantalla de sesiones.

## Entregas
Rama de integración: `feat/inicio-cierre-sesion` (los PR de las entregas van contra ella; ver `AGENTS.md`)

- E-01 Configuración, límite por IP y cómputo de intentos en cuenta inactiva
  Tareas: T-001, T-002, T-003 | Líneas estimadas: 240 | Rama: feat/inicio-cierre-sesion-limites
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_auth_conf.py apps/accounts/tests/test_auth_throttling.py apps/accounts/tests/test_inactive_login.py` y comprobar que 6 intentos con contraseña correcta sobre una cuenta inactiva disparan el bloqueo `too_many_login_attempts` y la fila `LOCKOUT` en `SecurityEvent`.

- E-02 Modelo `UserSession` y servicio básico de sesiones activas
  Tareas: T-004, T-005 | Líneas estimadas: 399 | Rama: feat/inicio-cierre-sesion-servicio-sesiones
  Cómo probarlo: aplicar la migración y ejecutar `pytest apps/accounts/tests/test_user_session_model.py apps/accounts/tests/test_sessions_service.py --no-cov -v`.
  Dividida: con T-006 superaba `sdd.max_lineas_pr` (400); el cierre de otras sesiones, invalidación masiva y purga pasan a E-02b.

- E-02b Cierre de otras sesiones, invalidación masiva y purga en el servicio
  Tareas: T-006 | Líneas estimadas: 220 | Rama: feat/inicio-cierre-sesion-revocar-sesiones
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_sessions_service.py --no-cov -v` para comprobar `revoke_other_session`, `revoke_all_other_sessions`, `revoke_all_user_sessions` y `purge_expired`.

- E-03 Ciclo de vida automático de sesiones y orden de purga en consola
  Tareas: T-007, T-008 | Líneas estimadas: 280 | Rama: feat/inicio-cierre-sesion-purga
  Cómo probarlo: iniciar sesión desde consola/test, envejecer la fila en `UserSession` y ejecutar `python manage.py purge_expired_sessions`; desactivar o cambiar la contraseña de un usuario y comprobar que sus filas de `UserSession` desaparecen.

- E-04 API de inicio de sesión, sesión actual y cierre de sesión
  Tareas: T-009, T-010 | Líneas estimadas: 427 | Rama: feat/inicio-cierre-sesion-api-auth
  Cómo probarlo: con `curl`, iniciar sesión en `/api/browser/v1/auth/login` y `/api/app/v1/auth/login`, consultar `/api/.../auth/session` y cerrar sesión en `/api/.../auth/logout`.
  Excepción: 427 líneas reales (dentro de `sdd.max_lineas_pr_excepcion`, 500): login, consulta de sesión y logout comparten autenticador y textos en `auth_views.py` y no deben exponerse por separado; T-011 pasa a E-04b para no superar 500 líneas.

- E-04b Neutralidad y bloqueo por intentos fallidos en el inicio de sesión
  Tareas: T-011 | Líneas estimadas: 70 | Rama: feat/inicio-cierre-sesion-neutralidad
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_auth_neutrality.py --no-cov -v` y comprobar con `curl` la respuesta idéntica y el bloqueo al 6.º intento entre correo inexistente, contraseña errónea y cuenta inactiva.

- E-05 API de aceptación de términos vigentes y guarda del área privada
  Tareas: T-012 | Líneas estimadas: 293 | Rama: feat/inicio-cierre-sesion-api-sesiones
  Cómo probarlo: con `curl`, iniciar sesión con una cuenta sin términos vigentes aceptados, aceptarlos en `/api/app/v1/auth/terms/accept` y comprobar en `/api/app/v1/auth/session` que `terms_status` pasa a `"accepted"`, además de ejecutar `pytest apps/accounts/tests/test_auth_terms_gate.py --no-cov -v`.

- E-05b API de listado y cierre de otras sesiones activas
  Tareas: T-013 | Líneas estimadas: 312 | Rama: feat/inicio-cierre-sesion-gestion-sesiones
  Cómo probarlo: con `curl`, comprobar `403 terms_required` en `/api/app/v1/auth/sessions` sin términos vigentes y, tras aceptarlos, listar sesiones activas y revocar otra sesión o todas las demás.

- E-06 Cliente de autenticación y almacenamiento de token para escritorio
  Tareas: T-014, T-015 | Líneas estimadas: 333 | Rama: feat/inicio-cierre-sesion-cliente-auth
  Cómo probarlo: ejecutar `pnpm --filter frontend test src/api/client.test.ts src/api/auth.test.ts`.

- E-06b Textos multilingües y traducción de errores de autenticación en el cliente
  Tareas: T-016, T-017 | Líneas estimadas: 110 | Rama: feat/inicio-cierre-sesion-textos-auth
  Cómo probarlo: ejecutar `pnpm --filter frontend test src/i18n/locales/locales.test.ts src/registration/serverErrors.test.ts`.

- E-07 Pantalla de inicio de sesión (sin ruta)
  Tareas: T-018 | Líneas estimadas: 301 | Rama: feat/inicio-cierre-sesion-pantallas-acceso
  Cómo probarlo: ejecutar `pnpm --filter frontend test src/auth/LoginPage.test.tsx`.

- E-07b Pantalla de términos pendientes y rutas `/login` y `/terms`
  Tareas: T-019 | Líneas estimadas: 355 | Rama: feat/inicio-cierre-sesion-pantalla-terminos
  Cómo probarlo: abrir `http://localhost:5173/login` y `http://localhost:5173/terms` en el navegador y ejecutar `pnpm --filter frontend test src/auth/TermsPage.test.tsx src/App.test.tsx`.

- E-07c Botón de icono, menús hacia arriba y menú de usuario
  Tareas: mejora de componentes del sistema de diseño | Líneas estimadas: 424 | Rama: feat/inicio-cierre-sesion-componentes-menu
  Cómo probarlo: abrir el catálogo de componentes y comprobar el tooltip hacia arriba de `IconButton` y los menús de idioma y usuario desplegándose hacia arriba en `Sidebar`.
  Excepción: 424 líneas reales (dentro de `sdd.max_lineas_pr_excepcion`, 500) por actualizar las referencias HTML (`docs/referencia/crear-empresa.html` y `activos.html`) al invertir los colores del avatar en tema claro.

- E-07d Columnas redimensionables y elipsis en tablas
  Tareas: mejora de componente compartido `Table` | Líneas estimadas: 208 | Rama: feat/inicio-cierre-sesion-tabla-redimensionable
  Cómo probarlo: arrastrar los bordes derechos entre cabeceras en `Table` y comprobar el acorte dinámico con `...`.

- E-07e Selección de filas con casillas en tablas
  Tareas: mejora de componente compartido `Table` | Líneas estimadas: 420 | Rama: feat/inicio-cierre-sesion-tabla-seleccion
  Cómo probarlo: marcar casillas en la tabla del catálogo y comprobar la barra de selección superpuesta sobre la cabecera con «n seleccionadas» y `IconButton`.
  Excepción: 420 líneas reales (dentro de `sdd.max_lineas_pr_excepcion`, 500) por entregar `Table` seleccionable, `IconTrash`, sus tests y su muestra en un único corte vertical.

- E-08 Pantalla del área privada, gestión de sesiones y rutas `/` y `/showcase`
  Tareas: T-020 | Líneas estimadas: 478 | Rama: feat/inicio-cierre-sesion-pantalla-sesiones
  Cómo probarlo: abrir `http://localhost:5173/` y `http://localhost:5173/showcase` en el navegador y ejecutar `pnpm --filter frontend test src/auth/HomePage.test.tsx src/App.test.tsx`.
  Excepción: 478 líneas reales (dentro de `sdd.max_lineas_pr_excepcion`, 500): al exponer `HomePage` en `/` en la misma entrega visual para cumplir `AGENTS.md`, `ShowcasePage` pasa a `/showcase` y obliga a actualizar sus tests unitarios y visuales además de la pantalla y sus tests.

- E-09 Enrutamiento completo, redirecciones, accesibilidad y resumen
  Tareas: T-021, T-022, T-023, T-024 | Líneas estimadas: 327 | Rama: feat/inicio-cierre-sesion-rutas
  Cómo probarlo: abrir `http://localhost:5173/login`, iniciar sesión, aceptar términos si están pendientes, ver y cerrar sesiones en `/` y cerrar la sesión actual, siguiendo `specs/inicio-cierre-sesion/resumen.md`.

- E-09b Transiciones entre pantallas, altura animada en tarjetas y acciones en línea en verificación
  Tareas: mejora visual tras revisión de E-09 | Líneas estimadas: 245 | Rama: feat/inicio-cierre-sesion-transiciones
  Cómo probarlo: cambiar entre pantallas públicas comprobando el fade-out/fade-in del contenido sin mover la barra superior, recargar páginas con carga asíncrona viendo crecer la tarjeta sin saltos y abrir `/register/continue#...` para ver «Enviar otro código» junto a «Verificar».

## RF sin tarea
Ninguno.
