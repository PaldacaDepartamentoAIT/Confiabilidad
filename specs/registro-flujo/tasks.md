# Tareas: registro-flujo
Estado: aprobado

Rutas del backend relativas a `backend/apps/accounts/` y del frontend a `frontend/src/`, salvo que
se indique otra. «Suite verde» = `cd backend && pytest -q` + `mypy .` + `ruff check .` +
`black --check .` en el backend, y `pnpm --filter frontend test` + `typecheck` + `lint` +
`prettier --check` en el frontend, sin errores. En cada tarea, antes de marcarla, se prueba al menos
un mutante del código que introduce, que debe hacer fallar sus tests (archivo de tests completo,
nunca con `-k`).

Las pantallas se construyen sin ruta (E-12…E-14) y se enlazan todas a la vez en E-15, para no
exponer en la interfaz nada que aún no funcione (`AGENTS.md`).

## Backend

- [ ] T-001 Verificar de nuevo un código validado
  RF: RF-007, RF-008 (RF-009 de `procesos-pendientes`; M-01, D-02) | Depende de: — | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_flow.py`.
  Hecho cuando: `verify_code` valida un código correcto; con el código ya validado, el correcto se
  acepta sin cambiar `failed_attempts` ni `code_validated_at`, también con el código caducado y el
  proceso en la gracia; uno incorrecto suma un intento con el código vigente y da `CODE_EXPIRED` sin
  sumar con el código caducado; bloqueado o caducado se rechaza; una plaza da los mismos resultados
  que un registro sin validar cuyo código no se acierta; suite verde.

- [ ] T-002 La consola usa la regla nueva
  RF: RF-008 (RF-009 de `procesos-pendientes`; D-01) | Depende de: T-001 | Archivos: 3
  Archivos: `registration.py`, `tests/test_registration_service.py`,
  `backend/apps/audit/tests/test_registration_events.py`.
  Hecho cuando: `verify` delega en `verify_code`;
  `test_already_validated_code_rejects_any_code_without_counting` se sustituye por los casos de
  T-001 a través de `verify`; el test de auditoría espera `[True, True]`; suite verde.

- [ ] T-003 Resumen de `procesos-pendientes`: código validado
  RF: RF-008 | Depende de: T-002 | Archivos: 1
  Archivos: `specs/procesos-pendientes/resumen.md`.
  Hecho cuando: el resumen explica que repetir `registration verify` con el código correcto ya
  validado lo acepta de nuevo y que uno incorrecto suma un intento.

- [ ] T-004 Valores configurables del flujo
  RF: RF-023 (M-04) | Depende de: — | Archivos: 4
  Archivos: `backend/config/settings.py`, `backend/.env.example`, `conf.py`,
  `tests/test_registration_conf.py`.
  Hecho cuando: `conf` expone la espera entre reenvíos (60 s), el máximo de reenvíos (5), el límite
  por IP del flujo (60/h) y el plazo de borrado (24 h), leídos de variables de entorno, y rechaza un
  valor menor que 1 como los límites existentes; suite verde.
  Excepción: la configuración está repartida por diseño entre `settings.py`, `.env.example` y
  `conf.py`; separarla dejaría un ajuste sin lector o un lector sin ajuste.

- [ ] T-005 Límite por IP del flujo
  RF: RF-019 (M-04) | Depende de: T-004 | Archivos: 2
  Archivos: `throttling.py`, `tests/test_registration_throttling.py`.
  Hecho cuando: `check_flow_ip` permite 60 peticiones por hora y rechaza la siguiente con los
  segundos de espera, con una clave distinta de las del formulario (no se suman); suite verde.

- [ ] T-006 Textos del flujo en tres idiomas
  RF: RF-022 (M-03) | Depende de: — | Archivos: 2
  Archivos: `api/messages.py`, `tests/test_registration_api_messages.py`.
  Hecho cuando: `wrong_code`, `locked`, `code_expired`, `expired`, `resend_unavailable` y
  `not_found` tienen texto en `es`, `pt-BR` y `en`, y el test de completitud los incluye; suite
  verde.

- [ ] T-007 Ruta de verificación
  RF: RF-007, RF-016, RF-019, RF-021, RF-022 (M-03, D-03) | Depende de: T-001, T-005, T-006 |
  Archivos: 4
  Archivos: `api/flow_serializers.py`, `api/flow_views.py`, `api/urls.py`,
  `tests/test_registration_flow_api.py`.
  Hecho cuando: `POST /api/{browser,app}/v1/registration/verify` con `{public_id, code}` da `200`
  con el código correcto, `400` con `{"code": …}` y su texto en el idioma pedido para cada rechazo,
  `404` con un identificador desconocido de cualquier formato, `403` sin CSRF en la ruta web, y
  `429` con `Retry-After` al superar el límite por IP; un cuerpo ilegible da `400`, nunca `500`;
  suite verde.
  Excepción: una ruta nueva solo es observable con su serializador, su vista y su entrada en
  `urls.py` a la vez.

- [ ] T-008 Contadores de reenvío en el modelo
  RF: RF-010 (M-02, D-04) | Depende de: — | Archivos: 3
  Archivos: `models.py`, `migrations/0013_codeprocess_resend.py`,
  `tests/test_pending_registration_model.py`.
  Hecho cuando: `CodeProcess` tiene `resend_count` (0) y `last_sent_at` (nulo) en las tres tablas;
  la migración se aplica sobre datos existentes; `python manage.py makemigrations --check` no
  propone nada; suite verde.

- [ ] T-009 Contadores al emitir el código
  RF: RF-010, RF-017 (M-02) | Depende de: T-008 | Archivos: 3
  Archivos: `processes.py`, `registration.py`, `tests/test_registration_flow.py`.
  Hecho cuando: la plaza nace con `last_sent_at`; un registro nuevo, uno repetido y una plaza con
  cuenta al resolverse quedan con `resend_count` 0 y `last_sent_at` del momento de la resolución,
  igual en los tres casos; suite verde.

- [ ] T-010 Reenvío con espera y tope
  RF: RF-010 (M-01) | Depende de: T-004, T-009 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_flow.py`.
  Hecho cuando: `resend_code` reenvía pasados 60 s y suma uno a `resend_count`; antes de 60 s, tras
  el quinto reenvío o con el código validado devuelve `UNAVAILABLE` sin cambiar nada; una plaza se
  comporta igual que un registro real sin validar; suite verde.

- [ ] T-011 Ruta de reenvío
  RF: RF-010, RF-016, RF-019, RF-021 (M-03) | Depende de: T-007, T-010 | Archivos: 3
  Archivos: `api/flow_views.py`, `api/urls.py`, `tests/test_registration_flow_api.py`.
  Hecho cuando: `POST …/registration/resend` da `202`, `400` `{"code": "resend_unavailable"}`,
  `404`, `403` sin CSRF y `429`, y cuenta para el límite por IP; suite verde.

- [ ] T-012 Estado del proceso
  RF: RF-006, RF-009, RF-010 (M-01, D-05) | Depende de: T-010 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_flow.py`.
  Hecho cuando: `status` devuelve los segundos del código, los segundos hasta poder reenviar, los
  reenvíos restantes, bloqueado y caducado; no incluye ningún dato de la validación; un registro
  validado y uno sin validar dan el mismo estado; `None` si no existe; suite verde.

- [ ] T-013 Ruta de estado
  RF: RF-006, RF-016, RF-021 (M-03, D-03) | Depende de: T-011, T-012 | Archivos: 3
  Archivos: `api/flow_views.py`, `api/urls.py`, `tests/test_registration_flow_api.py`.
  Hecho cuando: `POST …/registration/status` da `200` con el estado o `404`, exige CSRF en la ruta
  web y no cuenta para el límite por IP (61 consultas seguidas dan `200`); suite verde.

- [ ] T-014 Lista pública de países
  RF: RF-001 (M-06) | Depende de: — | Archivos: 2
  Archivos: `validators.py`, `tests/test_validators.py`.
  Hecho cuando: `COUNTRY_CODES` es pública, ordenada y es la misma que usa `validate_country`, sin
  cambiar ninguna validación; suite verde.

- [ ] T-015 Ruta de opciones del formulario
  RF: RF-001, RF-021 (M-06, D-09) | Depende de: T-013, T-014 | Archivos: 3
  Archivos: `api/flow_views.py`, `api/urls.py`, `tests/test_registration_flow_api.py`.
  Hecho cuando: `GET …/registration/options?language=pt-BR` da los países y los documentos vigentes
  de términos y de marketing en ese idioma, o `null` si no hay; la ruta web pone la cookie
  `csrftoken`; suite verde.

- [ ] T-016 Completar con código y contraseña
  RF: RF-012, RF-013, RF-014 (M-01, D-02; C-03) | Depende de: T-001 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_flow.py`.
  Hecho cuando: `complete_with_code` crea la cuenta solo con el código correcto y validado; un código
  incorrecto o no validado suma un intento y no evalúa la contraseña; una contraseña que incumple la
  política devuelve cada regla sin sumar intento y conserva el código; bloqueado, caducado o
  inexistente se rechaza; una plaza nunca crea cuenta; suite verde.

- [ ] T-017 Textos de la política de contraseña
  RF: RF-013, RF-022 | Depende de: T-006 | Archivos: 2
  Archivos: `api/messages.py`, `tests/test_registration_api_messages.py`.
  Hecho cuando: `password_too_short`, `password_too_similar`, `password_too_common`,
  `password_entirely_numeric` y el código de contraseña filtrada tienen texto en los tres idiomas;
  suite verde.

- [ ] T-018 Ruta de compleción
  RF: RF-012, RF-013, RF-014, RF-016, RF-019, RF-021 (M-03) | Depende de: T-011, T-016, T-017 |
  Archivos: 4
  Archivos: `api/flow_serializers.py`, `api/flow_views.py`, `api/urls.py`,
  `tests/test_registration_flow_api.py`.
  Hecho cuando: `POST …/registration/complete` con `{public_id, code, password}` da `201` y crea la
  cuenta con el correo verificado; `400` con el código de rechazo, o con
  `{"errors": {"password": […]}}`; `404`; `403` sin CSRF; `429`; completar sin código, con uno
  incorrecto o con uno no validado nunca crea la cuenta (CF-3); suite verde.
  Excepción: igual que T-007, la ruta no es observable sin serializador, vista y `urls.py`.

- [ ] T-019 Casos compartidos de contraseña en el servidor
  RF: RF-013 (CF-8, S-17) | Depende de: — | Archivos: 1
  Archivos: `tests/test_password_shared_cases.py`.
  Hecho cuando: un test recorre la tabla de la spec con los validadores de longitud y de solo
  números del servidor y obtiene el resultado de cada fila; suite verde.

- [ ] T-020 Marketing en el modelo
  RF: RF-018 (M-05) | Depende de: T-008 | Archivos: 3
  Archivos: `models.py`, `migrations/0014_pendingregistration_marketing.py`,
  `tests/test_pending_registration_model.py`.
  Hecho cuando: `PendingRegistration` guarda `marketing_version` y `marketing_locale`, vacíos por
  defecto; `makemigrations --check` no propone nada; suite verde.

- [ ] T-021 Marketing al empezar y al repetir
  RF: RF-018 (RF-005 y RF-024 de `procesos-pendientes`) | Depende de: T-020 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: `start` guarda en la plaza un documento de marketing vigente y descarta sin error uno
  inexistente o no vigente; un registro nuevo lo copia; uno repetido conserva el del primero, también
  su ausencia; un correo con cuenta no guarda nada; suite verde.

- [ ] T-022 Concesión de marketing al completar
  RF: RF-014, RF-018 (RF-020 de `procesos-pendientes`; C-01) | Depende de: T-021 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: completar registra la concesión con la fecha de compleción en la misma operación;
  un documento que ya no es vigente, borrado o de otro tipo crea la cuenta sin concesión y sin
  error; suite verde.

- [ ] T-023 Marketing en la API del formulario
  RF: RF-018 (RF-015 de `registro-api`; D-06) | Depende de: T-021 | Archivos: 3
  Archivos: `api/serializers.py`, `api/views.py`, `tests/test_registration_api.py`.
  Hecho cuando: `marketing` vigente llega a la plaza; ausente, no vigente, inexistente, sin documento
  vigente o mal formado (no objeto, tipos erróneos, longitudes, nulos, sustitutos, anidamiento) da la
  misma respuesta `202` sin error de campo ni `500`; `pt-br` concede `pt-BR` (CF-8 de
  `registro-api`); suite verde.

- [ ] T-024 Resúmenes de `procesos-pendientes` y `registro-api`: marketing
  RF: RF-018 | Depende de: T-022, T-023 | Archivos: 2
  Archivos: `specs/procesos-pendientes/resumen.md`, `specs/registro-api/resumen.md`.
  Hecho cuando: los dos resúmenes describen el marketing aceptado, con un `curl` del formulario con
  `marketing`.

- [ ] T-025 Borrado de procesos antiguos
  RF: RF-020, RF-017 (M-01, D-07) | Depende de: T-004 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_flow.py`.
  Hecho cuando: `purge_stale` borra en una transacción los registros pendientes y las plazas de
  registro cuyo código caducó hace 24 h o más, conserva los de menos, no toca las plazas de cambio
  de contraseña y devuelve cuántos borró; suite verde.

- [ ] T-026 Tarea programada de borrado
  RF: RF-020 (M-07) | Depende de: T-025 | Archivos: 3
  Archivos: `tasks.py`, `backend/config/settings.py`, `tests/test_registration_background.py`.
  Hecho cuando: `purge_stale_registrations` llama a `purge_stale` y está en `CELERY_BEAT_SCHEDULE`
  cada 3600 s; `celery -A config call apps.accounts.tasks.purge_stale_registrations` la dispara;
  suite verde.

- [ ] T-027 Borrado desde consola
  RF: RF-020 (M-07, P-03) | Depende de: T-025 | Archivos: 2
  Archivos: `management/commands/registration.py`, `tests/test_registration_command.py`.
  Hecho cuando: `python manage.py registration purge-stale` borra y muestra cuántos; suite verde.

- [ ] T-028 Equivalencia de plaza y registro real en el flujo
  RF: RF-016, RF-017, RF-020 (CF-2) | Depende de: T-013, T-018, T-023, T-026 | Archivos: 1
  Archivos: `tests/test_registration_flow_equivalence.py`.
  Hecho cuando: un registro real cuyo código no se acierta y una plaza dan las mismas respuestas
  (estado, cuerpo, cabeceras y cookies) y las mismas consultas (`django_assert_num_queries`) al
  consultar, verificar, reenviar, completar y caducar, con bloqueo y tope de reenvíos; pasan a `404`
  a la vez al repetir el registro y con `purge_stale`; un identificador desconocido da `404` sin
  escribir nada; suite verde.

## Frontend

- [ ] T-029 Variables de la identidad visual
  RF: RF-001, RF-005 (M-13, D-13; S-14) | Depende de: — | Archivos: 3
  Archivos: `styles/tokens.css`, `styles/base.css`, `styles/tokens.test.ts`.
  Hecho cuando: `tokens.css` define los 13 colores de cada tema de `docs/identidad-visual.md`, el
  oscuro bajo `prefers-color-scheme: dark`; `base.css` aplica lienzo, tinta, formas y foco visible;
  el test lee el CSS y comprueba cada valor de las dos tablas; suite verde.

- [ ] T-030 Fuentes y estilos cargados
  RF: RF-001 (M-13) | Depende de: T-029 | Archivos: 3
  Archivos: `frontend/package.json`, `pnpm-lock.yaml` (raíz), `main.tsx`.
  Hecho cuando: `@fontsource-variable/manrope` y `@fontsource-variable/jetbrains-mono` están
  instaladas; `main.tsx` importa fuentes y estilos; `pnpm --filter frontend build` termina sin
  errores; la página de muestra se ve con Manrope y los colores de la paleta; suite verde.

- [ ] T-031 Proxy de la API en desarrollo
  RF: RF-021 (M-14) | Depende de: — | Archivos: 2
  Archivos: `frontend/vite.config.ts`, `docker/docker-compose.yml`.
  Hecho cuando: con Docker levantado, `curl http://localhost:5173/api/health/` responde lo mismo que
  el backend; el destino sale de `VITE_BACKEND_URL`; suite verde.

- [ ] T-032 Enrutador
  RF: RF-004 (M-09, D-08) | Depende de: — | Archivos: 2
  Archivos: `routing/router.ts`, `routing/router.test.ts`.
  Hecho cuando: `navigate` cambia la ruta sin recargar, `popstate` la actualiza, el fragmento se lee
  aparte y una ruta desconocida da la de reserva; suite verde.

- [ ] T-033 Aplicación con rutas
  RF: RF-004 (M-09) | Depende de: T-032 | Archivos: 2
  Archivos: `App.tsx`, `App.test.tsx`.
  Hecho cuando: `/` y cualquier ruta desconocida muestran la página de muestra a través del
  enrutador, como hoy; suite verde.

- [ ] T-034 Cliente de la API
  RF: RF-021, RF-022, RF-024 (M-08, D-10) | Depende de: — | Archivos: 2
  Archivos: `api/client.ts`, `api/client.test.ts`.
  Hecho cuando: con `fetch` simulado, el cliente usa `/api/browser/v1` y `X-CSRFToken` de la cookie
  en el navegador y `VITE_API_BASE_URL` + `/api/app/v1` en Tauri; envía `Accept-Language` y
  `language`; distingue éxito, errores de campo, código de error, `404`, `429` con `retry_after` y
  fallo de red; suite verde.

- [ ] T-035 Llamadas del registro
  RF: RF-001, RF-004, RF-006…RF-012 (M-08) | Depende de: T-034 | Archivos: 2
  Archivos: `api/registration.ts`, `api/registration.test.ts`.
  Hecho cuando: hay funciones tipadas para opciones, formulario, estado, verificar, reenviar y
  completar, con el cuerpo de cada ruta y `public_id` siempre en el cuerpo; `marketing` solo se
  incluye si se pasa; suite verde.

- [ ] T-036 Casilla y selector accesibles
  RF: RF-001, RF-003 (M-12) | Depende de: — | Archivos: 3
  Archivos: `components/fields/Checkbox.tsx`, `components/fields/SelectField.tsx`,
  `components/fields/ChoiceFields.test.tsx`.
  Hecho cuando: los dos tienen etiqueta asociada, asterisco de obligatorio, `aria-invalid`, y error y
  ayuda en `aria-describedby`, como `TextField`; `axe-core` no encuentra fallos; suite verde.

- [ ] T-037 Campo de fecha
  RF: RF-001 (M-12) | Depende de: — | Archivos: 2
  Archivos: `components/fields/TextField.tsx`, `components/fields/TextField.test.tsx`.
  Hecho cuando: `TextField` acepta `type="date"` y los tests existentes siguen sin cambios; suite
  verde.

- [ ] T-038 Validación con selectores, casillas y varios errores
  RF: RF-002, RF-003 (M-12) | Depende de: T-036 | Archivos: 2
  Archivos: `forms/useFormValidation.ts`, `forms/useFormValidation.test.tsx`.
  Hecho cuando: el hook lee `<select>` y casillas (`"true"` o `""`), un campo puede tener varios
  errores de servidor a la vez y la opción `scrollToError` llama a `scrollIntoView` antes de llevar
  el foco; sin la opción, los tests existentes pasan sin cambios; suite verde.

- [ ] T-039 Dígitos como el servidor
  RF: RF-013 (M-12, D-12; CF-8) | Depende de: — | Archivos: 3
  Archivos: `forms/digits.ts`, `forms/passwordRules.ts`, `forms/passwordRules.test.ts`.
  Hecho cuando: «solo números» rechaza también los caracteres con `Numeric_Type=Digit`
  (`²²²²²²²²²²²²`), con la lista generada por `unicodedata` y su comando de generación en un
  comentario; un test recorre la tabla de casos compartidos de la spec; suite verde.

- [ ] T-040 Cuenta atrás
  RF: RF-006, RF-010, RF-024 (M-11) | Depende de: — | Archivos: 2
  Archivos: `registration/useCountdown.ts`, `registration/useCountdown.test.ts`.
  Hecho cuando: con temporizadores simulados, el hook cuenta hacia atrás desde los segundos dados,
  avisa al llegar a cero y se reinicia con un valor nuevo; suite verde.

- [ ] T-041 Textos del formulario y errores del servidor
  RF: RF-001, RF-003, RF-022 (D-11) | Depende de: — | Archivos: 3
  Archivos: `i18n/locales/es.ts`, `i18n/locales/en.ts`, `i18n/locales/pt-BR.ts`.
  Hecho cuando: existen en los tres idiomas las etiquetas del formulario, los textos de los
  términos y del marketing, una clave por cada código de error del servidor y el texto genérico;
  `locales.test.ts` pasa; suite verde.

- [ ] T-042 Traducción de los errores del servidor
  RF: RF-003, RF-022 (D-11) | Depende de: T-041 | Archivos: 2
  Archivos: `registration/serverErrors.ts`, `registration/serverErrors.test.ts`.
  Hecho cuando: cada código de M-04 de `registro-api`, de la contraseña y del flujo se traduce a su
  clave con sus parámetros, y uno desconocido al genérico; suite verde.

- [ ] T-043 Pantalla del formulario: campos y comprobaciones
  RF: RF-001, RF-002, RF-003 (M-10) | Depende de: T-035, T-036, T-037, T-038, T-041 | Archivos: 2
  Archivos: `registration/RegisterPage.tsx`, `registration/RegisterPage.test.tsx`.
  Hecho cuando: con `fetch` simulado, la pantalla carga las opciones, muestra los países por nombre en
  el idioma activo, el texto de los términos y la casilla de marketing solo si hay documento; al
  enviar vacío muestra cada error bajo su campo, desplaza y enfoca el primero y no llama al servidor;
  suite verde.

- [ ] T-044 Pantalla del formulario: envío
  RF: RF-003, RF-004, RF-018, RF-024 (M-10) | Depende de: T-040, T-042, T-043 | Archivos: 2
  Archivos: `registration/RegisterPage.tsx`, `registration/RegisterPage.test.tsx`.
  Hecho cuando: un `400` pinta cada error bajo su campo con desplazamiento y foco al primero; un
  `429` muestra la cuenta atrás y reactiva el envío al llegar a cero; un fallo de red da el mensaje
  general sin perder los datos; `marketing` solo se envía con la casilla marcada; un `202` navega a
  `/register/continue#<public_id>`; suite verde.

- [ ] T-045 Textos de verificación, contraseña y cuenta creada
  RF: RF-005, RF-009, RF-010, RF-015, RF-016, RF-022 | Depende de: T-041 | Archivos: 3
  Archivos: `i18n/locales/es.ts`, `i18n/locales/en.ts`, `i18n/locales/pt-BR.ts`.
  Hecho cuando: existen en los tres idiomas el texto fijo de la verificación (sin afirmar que llegó
  un código), el temporizador, el reenvío, el bloqueo, el enlace no válido, el paso de contraseña y
  la cuenta creada; `locales.test.ts` pasa; suite verde.

- [ ] T-046 Pantalla de verificación: estado y enlace no válido
  RF: RF-005, RF-006, RF-016 (M-11, D-09) | Depende de: T-035, T-040, T-045 | Archivos: 2
  Archivos: `registration/VerifyPage.tsx`, `registration/VerifyPage.test.tsx`.
  Hecho cuando: la pantalla lee el identificador del fragmento, pide la cookie CSRF si falta, consulta
  el estado y muestra el texto fijo y el tiempo restante contando; al recargar vuelve a pedirlo; con
  `404` muestra el enlace no válido con acceso al formulario; nunca muestra un correo; suite verde.

- [ ] T-047 Pantalla de verificación: código y bloqueo
  RF: RF-007, RF-009, RF-024 (M-11) | Depende de: T-046 | Archivos: 2
  Archivos: `registration/VerifyPage.tsx`, `registration/VerifyPage.test.tsx`.
  Hecho cuando: un código incorrecto muestra el mensaje bajo el campo; con `locked` se desactiva el
  envío y solo queda el reenvío; con `code_expired` se indica que se pida otro; un `429` muestra la
  cuenta atrás; suite verde.

- [ ] T-048 Pantalla de verificación: reenvío
  RF: RF-010, RF-024 (M-11) | Depende de: T-047 | Archivos: 2
  Archivos: `registration/VerifyPage.tsx`, `registration/VerifyPage.test.tsx`.
  Hecho cuando: el botón muestra la cuenta atrás y se activa al llegar a cero; tras reenviar consulta
  de nuevo el estado; sin reenvíos restantes se desactiva y ofrece volver al formulario;
  `resend_unavailable` da el mensaje genérico; suite verde.

- [ ] T-049 Paso de contraseña
  RF: RF-011, RF-012, RF-013, RF-024 (M-11) | Depende de: T-039, T-042, T-045 | Archivos: 2
  Archivos: `registration/PasswordStep.tsx`, `registration/PasswordStep.test.tsx`.
  Hecho cuando: el paso valida longitud y solo números en el navegador sin llamar al servidor si
  fallan; envía el código recibido y la contraseña; pinta bajo el campo cada regla que devuelve el
  servidor; con un rechazo del código avisa a quien lo contiene; con `201` avisa del éxito; un `429`
  muestra la cuenta atrás; suite verde.

- [ ] T-050 Verificación con paso de contraseña y cuenta creada
  RF: RF-008, RF-011, RF-015 (M-11, S-08) | Depende de: T-048, T-049 | Archivos: 3
  Archivos: `registration/VerifyPage.tsx`, `registration/DonePage.tsx`,
  `registration/VerifyPage.test.tsx`.
  Hecho cuando: un código aceptado muestra el paso de contraseña con el código solo en el estado de
  React; un rechazo del código vuelve a la verificación con su mensaje y sin el código; recargar
  vuelve a la verificación; `201` navega a `/register/done`, que muestra la cuenta creada sin
  iniciar sesión; suite verde.

- [ ] T-051 Rutas del registro
  RF: RF-004, RF-005, RF-015, RF-016 (M-09) | Depende de: T-033, T-044, T-050 | Archivos: 2
  Archivos: `App.tsx`, `App.test.tsx`.
  Hecho cuando: `/register`, `/register/continue` y `/register/done` muestran sus pantallas, y `/`
  sigue con la página de muestra; suite verde.

- [ ] T-052 Accesibilidad de las pantallas del registro
  RF: RF-003, RF-005 (CF-5) | Depende de: T-051 | Archivos: 1
  Archivos: `registration/a11y.test.tsx`.
  Hecho cuando: `axe-core` no encuentra fallos en el formulario (vacío y con errores), la
  verificación (normal, bloqueada y enlace no válido), el paso de contraseña y la cuenta creada;
  ninguna contiene un correo; suite verde.

- [ ] T-053 Resumen de la feature y límites pendientes
  RF: RF-021 (CF-7, M-14) | Depende de: T-028, T-052 | Archivos: 2
  Archivos: `specs/registro-flujo/resumen.md`, `specs/cambio-contrasena/HUMAN_TODO.md`.
  Hecho cuando: `resumen.md` explica qué se hizo, el recorrido en la web y con `curl` (con el código
  del correo del proveedor local), cómo disparar la limpieza y su marco teórico; el `HUMAN_TODO.md`
  de `cambio-contrasena` indica que los límites de reenvío y verificación del registro ya existen.

## Entregas
Rama de integración: feat/registro-flujo (los PR de las entregas van contra ella; ver `AGENTS.md`)

Para el «Cómo probarlo» de cada entrega, desde la raíz del repositorio, levanta los servicios:
```bash
docker compose -f docker/docker-compose.yml up -d
```
Los códigos de verificación se leen en la salida del worker:
```bash
docker compose -f docker/docker-compose.yml logs -f worker
```
Los tests del backend y del frontend se ejecutan con:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
```bash
pnpm --filter frontend test
```
Los pasos concretos de cada entrega, con sus comandos listos para copiar, van en su resumen de
entrega (`entregas/E-XX-<descripcion>/resumen.md`).

- E-01 Volver a presentar un código validado (consola)
  Tareas: T-001, T-002, T-003 | Líneas estimadas: 200 | Rama: feat/registro-flujo-codigo-validado
  Cómo probarlo: empezar un registro con el comando `registration start`, verificarlo dos veces con
  `registration verify` y el código del worker (la segunda también se acepta) y una tercera con un
  código incorrecto (suma un intento).

- E-02 Verificar el código por la API, con límite por IP
  Tareas: T-004, T-005, T-006, T-007 | Líneas estimadas: 380 | Rama:
  feat/registro-flujo-verificar-api
  Cómo probarlo: con `curl`, empezar un registro por la API de `registro-api`, y llamar a la ruta de
  verificación con el código bueno, uno malo, un identificador inventado (`404`) y 61 veces seguidas
  (`429`).

- E-03 Reenviar el código con espera y tope
  Tareas: T-008, T-009, T-010, T-011 | Líneas estimadas: 350 | Rama: feat/registro-flujo-reenvio
  Cómo probarlo: con `curl`, reenviar antes de 60 s (`resend_unavailable`), después (`202` y código
  nuevo en el worker) y por sexta vez (`resend_unavailable`).

- E-04 Estado del proceso y opciones del formulario
  Tareas: T-012, T-013, T-014, T-015 | Líneas estimadas: 340 | Rama: feat/registro-flujo-estado
  Cómo probarlo: con `curl`, pedir las opciones (países, términos y marketing vigentes y la cookie
  `csrftoken`) y el estado de un registro antes y después de reenviar y de bloquearlo.

- E-05 Completar el registro con código y contraseña
  Tareas: T-016, T-017, T-018, T-019 | Líneas estimadas: 390 | Rama: feat/registro-flujo-completar
  Cómo probarlo: con `curl`, completar sin validar, con un código malo, con una contraseña corta y,
  por último, bien: la cuenta existe con el correo verificado y el registro pendiente desaparece.

- E-06 Consentimiento de marketing en el registro
  Tareas: T-020, T-021, T-022, T-023, T-024 | Líneas estimadas: 390 | Rama:
  feat/registro-flujo-marketing
  Cómo probarlo: con `curl`, registrarse con `marketing` vigente y completar (la cuenta tiene el
  consentimiento en el panel); repetir con un documento inexistente (la respuesta no cambia y la
  cuenta queda sin consentimiento).

- E-07 Limpieza programada y equivalencia completa
  Tareas: T-025, T-026, T-027, T-028 | Líneas estimadas: 370 | Rama: feat/registro-flujo-limpieza
  Cómo probarlo: envejecer un registro desde el shell de Django, ejecutar el subcomando
  `registration purge-stale` y ver que desaparece; ejecutar el test de equivalencia del flujo.

- E-08 Identidad visual, proxy y enrutador
  Tareas: T-029, T-030, T-031, T-032, T-033 | Líneas estimadas: 320 | Rama:
  feat/registro-flujo-identidad-visual
  Cómo probarlo: abrir http://localhost:5173/ con el sistema en tema claro y en oscuro y ver la
  página de muestra con Manrope y la paleta; pedir la salud de la API a través del puerto 5173.

- E-09 Cliente de la API del registro
  Tareas: T-034, T-035 | Líneas estimadas: 320 | Rama: feat/registro-flujo-cliente-api
  Cómo probarlo: los tests del frontend de `src/api`.

- E-10 Casilla, selector, fecha y validación ampliada
  Tareas: T-036, T-037, T-038 | Líneas estimadas: 380 | Rama: feat/registro-flujo-campos
  Cómo probarlo: los tests del frontend de `src/components` y `src/forms`.

- E-11 Contraseña como el servidor y cuenta atrás
  Tareas: T-039, T-040 | Líneas estimadas: 200 | Rama: feat/registro-flujo-digitos-cuenta-atras
  Cómo probarlo: los tests del frontend de `src/forms` y de la cuenta atrás; en la página de
  muestra, `²²²²²²²²²²²²` como contraseña nueva da el error de solo números.

- E-12 Pantalla del formulario (sin ruta)
  Tareas: T-041, T-042, T-043, T-044 | Líneas estimadas: 400 | Rama: feat/registro-flujo-formulario
  Cómo probarlo: los tests del frontend del formulario y de los errores del servidor.

- E-13 Pantalla de verificación (sin ruta)
  Tareas: T-045, T-046, T-047, T-048 | Líneas estimadas: 390 | Rama:
  feat/registro-flujo-verificacion
  Cómo probarlo: los tests del frontend de la pantalla de verificación.

- E-14 Paso de contraseña y cuenta creada (sin ruta)
  Tareas: T-049, T-050 | Líneas estimadas: 300 | Rama: feat/registro-flujo-contrasena
  Cómo probarlo: los tests del frontend de `src/registration`.

- E-15 Registro completo en la web
  Tareas: T-051, T-052, T-053 | Líneas estimadas: 150 | Rama: feat/registro-flujo-rutas
  Cómo probarlo: registrarse en http://localhost:5173/register de principio a fin con el código del
  correo del proveedor local, siguiendo `resumen.md`.

## RF sin tarea
Ninguno.
