# Tareas: correo-asincrono-plantillas
Estado: aprobado

Rutas relativas a `backend/apps/emails/` salvo que se indique. "Suite verde" =
`cd backend && pytest -q` + `mypy .` + `ruff check .` + `black --check .` sin errores. En cada
tarea que cambia código de producción, antes de marcarla, se prueba al menos un mutante de ese
código y debe hacer fallar sus tests, ejecutando el archivo de tests completo (nunca con `-k`).
Mientras la feature no esté terminada, `migrations/0001_initial.py` se regenera en cada tarea que
cambia el esquema, para que al final quede una sola migración de esquema. Las fechas se mueven en
los tests con `update()` (D-07 de `procesos-pendientes`), sin librerías de reloj.

- [x] T-001 App `emails` y modelo `EmailTemplate`
  RF: RF-001, RF-020, RF-022 (D-16) | Depende de: — | Archivos: 6
  Archivos: `__init__.py`, `apps.py`, `models.py`, `migrations/__init__.py`,
  `migrations/0001_initial.py`, `tests/test_models.py`, más `config/settings.py` (en `backend/`).
  Hecho cuando: la app está en `INSTALLED_APPS`; `EmailTemplate` solo admite los siete tipos y
  `es`, `pt-BR` y `en`; una segunda plantilla con el mismo tipo e idioma falla en la base de datos;
  cambiar una plantilla deja una entrada de historial con su autor; `delete()` de una plantilla y
  de un queryset lanzan error y no borran nada; `migrate` se aplica sobre la última de `main`;
  suite verde.
  Excepción: crear una app de Django exige su esqueleto (`__init__.py`, `apps.py`, paquete de
  migraciones) y darla de alta en `settings.py`; no se puede repartir sin dejar una app a medias.
  Decisiones: (1) También se crea `tests/__init__.py`, como en `consents`, para que los módulos de
  test no choquen por nombre con los de otras apps. [Cierto] Revertir: borrarlo. (2) Los tests
  reutilizan la plantilla existente con `get_or_create` en vez de borrar: no hay ninguna vía para
  borrar plantillas, ni siquiera para tests (RF-022). [Cierto] Revertir: no aplica.

- [ ] T-002 Sustitución de variables como texto
  RF: RF-023 (D-07) | Depende de: T-001 | Archivos: 2
  Archivos: `rendering.py`, `tests/test_rendering.py`.
  Hecho cuando: `{{ name }}` y `{{name}}` se sustituyen por su valor; un nombre con acentos,
  alfabeto no latino y emoji (`"Zoë 李 👋"`) sale idéntico en asunto y cuerpo; `{{ user.__class__ }}`,
  `{% if %}` y `{name}` no se evalúan; un valor que contiene `{{ code }}` no se vuelve a sustituir;
  suite verde.

- [ ] T-003 Enlaces con el identificador en el fragmento
  RF: RF-004, RF-005 (D-09) | Depende de: T-002 | Archivos: 3
  Archivos: `rendering.py`, `tests/test_rendering.py`, `config/settings.py` (en `backend/`).
  Hecho cuando: con `FRONTEND_BASE_URL=https://app.ejemplo.com`, el enlace de registro es
  `https://app.ejemplo.com/register/continue#<public_id>` y el de restablecimiento
  `https://app.ejemplo.com/password-reset/continue#<public_id>`; una barra final en la dirección
  base no duplica la barra; suite verde.

- [ ] T-004 Validación de plantillas al guardar
  RF: RF-021 (D-07) | Depende de: T-003 | Archivos: 3
  Archivos: `rendering.py`, `models.py`, `tests/test_rendering.py`.
  Hecho cuando: guardar una plantilla de código sin `{{ code }}`, `{{ link }}` o `{{ expires_in }}`,
  con una variable que su tipo no admite (`{{ code }}` en un aviso) o con una dirección web cuyo
  dominio no es el de `FRONTEND_BASE_URL` lanza `ValidationError` que enumera cada problema, y la
  fila guardada no cambia; una plantilla correcta se guarda; suite verde.

- [ ] T-005 Plazo relativo por idioma
  RF: RF-014 (D-08) | Depende de: T-002 | Archivos: 2
  Archivos: `rendering.py`, `tests/test_rendering.py`.
  Hecho cuando: con 9 min 40 s restantes da "9 minutos", "9 minutos" y "9 minutes"; con 1 min 30 s,
  "1 minuto", "1 minuto" y "1 minute"; con 59 s, "menos de un minuto", "menos de um minuto" y "less
  than a minute"; ninguna salida contiene una hora ni una fecha; suite verde.

- [ ] T-006 Bloque fijo de reporte en los avisos de seguridad
  RF: RF-010 (D-08) | Depende de: T-002 | Archivos: 3
  Archivos: `rendering.py`, `tests/test_rendering.py`, `config/settings.py` (en `backend/`).
  Hecho cuando: los cinco avisos terminan, después del texto editable, con el bloque de su idioma,
  que nombra `EMAIL_SUPPORT_ADDRESS` y recomienda restablecer la contraseña; los dos correos de
  código no lo llevan; el bloque no forma parte del texto guardado en la plantilla; suite verde.

- [ ] T-007 Plantillas iniciales
  RF: RF-001, RF-022 (CF-3, S-17) | Depende de: T-004, T-005, T-006 | Archivos: 2
  Archivos: `migrations/0002_initial_templates.py`, `tests/test_migrations.py`.
  Hecho cuando: tras `migrate` existen las 21 plantillas (7 tipos × 3 idiomas), todas pasan la
  validación de T-004; deshacer la migración las borra; suite verde. Los textos se revisan en el PR.

- [ ] T-008 Idiomas admitidos y normalización
  RF: RF-013 (D-10) | Depende de: — | Archivos: 2
  Archivos: `locales.py`, `tests/test_locales.py`.
  Hecho cuando: `"es"`, `"pt-BR"`, `"pt-br"`, `"pt_BR"`, `"EN"` y `" en "` se normalizan a `es`,
  `pt-BR`, `pt-BR`, `pt-BR`, `en` y `en`; `None`, `""`, `"fr"` y `"pt"` dan `es`; suite verde.

- [ ] T-009 Idioma en la cuenta y en el registro pendiente
  RF: RF-012 (D-10) | Depende de: T-008 | Archivos: 3
  Archivos: `apps/accounts/models.py`, `apps/accounts/migrations/0007_language.py`,
  `apps/accounts/tests/test_language.py` (en `backend/`).
  Hecho cuando: `User` y `PendingRegistration` tienen `language` con los tres idiomas y `es` por
  defecto; una cuenta creada antes de la migración queda en `es`; un idioma no admitido falla la
  validación; el cambio de idioma de una cuenta queda en su historial; suite verde.

- [ ] T-010 La cuenta hereda el idioma al completar el registro
  RF: RF-012 | Depende de: T-009 | Archivos: 2
  Archivos: `apps/accounts/registration.py`, `apps/accounts/tests/test_registration_service.py`
  (en `backend/`).
  Hecho cuando: completar un registro pendiente en `pt-BR` crea la cuenta en `pt-BR`; el resto de
  la suite del registro sigue en verde; suite verde.

- [ ] T-011 Bandeja y encolado al confirmar
  RF: RF-002, RF-003 (D-01) | Depende de: T-001 | Archivos: 4
  Archivos: `models.py`, `outbox.py`, `migrations/0001_initial.py`, `tests/test_outbox.py`.
  Hecho cuando: pedir un correo dentro de una transacción crea su fila `pending` y, al confirmar,
  encola `deliver` con su id (una sola vez); si la transacción se deshace, no queda fila ni se
  encola nada; si encolar lanza un error de conexión, la operación termina bien y la fila queda
  `pending`; suite verde.
  Excepción: `0001_initial.py` se regenera con `makemigrations` y no se edita a mano.

- [ ] T-012 Proveedor simulado y clasificación de errores
  RF: RF-026 (D-03, D-15) | Depende de: — | Archivos: 3
  Archivos: `errors.py`, `tests/backends.py`, `tests/test_errors.py`.
  Hecho cuando: `SMTPRecipientsRefused`, `SMTPSenderRefused` y `SMTPDataError` con código 5xx son
  definitivos; con código 4xx, temporales; `SMTPServerDisconnected`, `SMTPConnectError`,
  `SMTPAuthenticationError`, `TimeoutError`, `OSError` y cualquier otra excepción son temporales;
  el backend simulado lanza en orden los errores que se le indican y guarda los mensajes que
  entrega; suite verde.

- [ ] T-013 Entrega desde la cola y barrido periódico
  RF: RF-002, RF-011 (D-01) | Depende de: T-011, T-012 | Archivos: 3
  Archivos: `tasks.py`, `delivery.py`, `tests/test_delivery.py`.
  Hecho cuando: `deliver(id)` entrega un aviso pendiente por el backend simulado, con el asunto y
  el cuerpo de la plantilla de su tipo e idioma, y borra la fila; el mensaje no lleva cabecera
  `List-Unsubscribe` ni enlace de baja; `dispatch_due()` encola las filas `pending` con el intento
  vencido y no las futuras; una fila que quedó `pending` porque la cola estaba caída sale en el
  siguiente barrido; suite verde.

- [ ] T-014 Reintentos con espera creciente y reserva del intento
  RF: RF-016, RF-026 (D-04) | Depende de: T-013 | Archivos: 3
  Archivos: `delivery.py`, `tests/test_delivery.py`, `config/settings.py` (en `backend/`).
  Hecho cuando: tras un error temporal, la fila sigue `pending` con `attempts` + 1 y el siguiente
  intento a 30 s, 60 s, 120 s… hasta un tope de 15 min; con dos errores temporales y luego éxito, se
  entrega y se borra; un aviso con más de `EMAIL_NOTICE_RETRY_HOURS` (24 por defecto) desde su
  encolado deja de reintentarse y pasa a `failed`; una fila reservada por otro intento no se envía
  dos veces; suite verde.

- [ ] T-015 Fallo definitivo y registro de fallos
  RF: RF-017, RF-026 (D-12) | Depende de: T-014 | Archivos: 2
  Archivos: `delivery.py`, `tests/test_delivery.py`.
  Hecho cuando: un error definitivo pasa la fila a `failed` al primer intento, sin reintentar; una
  fila `failed` conserva tipo, idioma, destinatario, fecha de encolado, intentos y último error, y
  no vuelve a encolarse en el barrido; suite verde.

- [ ] T-016 Idioma de cada correo al encolar
  RF: RF-013 | Depende de: T-008, T-011 | Archivos: 2
  Archivos: `outbox.py`, `tests/test_outbox.py`.
  Hecho cuando: un correo de código se encola en el idioma indicado por quien lo pide (normalizado
  con T-008); un aviso de seguridad, en el `language` de la cuenta aunque se indique otro; sin
  idioma válido, en `es`; suite verde.

- [ ] T-017 Tope del aviso "ya tienes cuenta"
  RF: RF-007 (D-11) | Depende de: T-011 | Archivos: 5
  Archivos: `models.py`, `outbox.py`, `migrations/0001_initial.py`, `tests/test_outbox.py`,
  `config/settings.py` (en `backend/`).
  Hecho cuando: el primer aviso "ya tienes cuenta" de una cuenta se encola; un segundo dentro de
  `EMAIL_ACCOUNT_EXISTS_WINDOW_MINUTES` (60 por defecto) no se encola y la llamada no lanza error;
  pasada la ventana, se encola otro; el tope no afecta a otro tipo de correo ni a otra cuenta;
  borrar la cuenta borra su marca; suite verde.
  Excepción: `0001_initial.py` se regenera con `makemigrations` y la ventana necesita su ajuste en
  `settings.py`; los tres archivos restantes son el comportamiento y su test.

- [ ] T-018 El código se guarda oculto en la bandeja
  RF: RF-018 (D-06) | Depende de: T-011 y T-028 de `huellas-hmac-unificadas` | Archivos: 2
  Archivos: `outbox.py`, `tests/test_outbox.py`.
  Hecho cuando: un correo de código guarda `masked_code` y `code_nonce` (de `mask_code`) y ninguna
  columna, ni `context`, contiene el código en claro; los avisos no guardan máscara; suite verde.

- [ ] T-019 La entrega recupera el código y borra la máscara
  RF: RF-018 (D-06) | Depende de: T-015, T-018 | Archivos: 2
  Archivos: `delivery.py`, `tests/test_delivery.py`.
  Hecho cuando: el correo entregado contiene el código original; tras entregar, descartar o fallar,
  no queda máscara ni nonce; una fila `failed` no contiene el código; el código no aparece en
  ningún mensaje de registro (`caplog`) de la entrega ni del fallo; suite verde.

- [ ] T-020 Descarte del código que ya no sirve
  RF: RF-015 (D-05) | Depende de: T-019 | Archivos: 2
  Archivos: `delivery.py`, `tests/test_delivery.py`.
  Hecho cuando: con un comprobador registrado para el propósito que devuelve la caducidad, el
  correo se entrega; si devuelve nada (caducado, validado o reemplazado), la fila se borra sin
  enviar; tras un error temporal, se reintenta solo mientras el comprobador siga devolviendo una
  caducidad; un propósito sin comprobador registrado lanza un error de configuración; suite verde.

- [ ] T-021 Plazo calculado al entregar
  RF: RF-014 | Depende de: T-005, T-020 | Archivos: 2
  Archivos: `delivery.py`, `tests/test_delivery.py`.
  Hecho cuando: un correo encolado con 15 min de vigencia y entregado cuando quedan 6 min 10 s dice
  "6 minutos", no "15"; suite verde.

- [ ] T-022 Comprobador de vigencia de `accounts`
  RF: RF-015 (D-05) | Depende de: T-020 | Archivos: 3
  Archivos: `apps/accounts/email_checks.py`, `apps/accounts/apps.py`,
  `apps/accounts/tests/test_email_checks.py` (en `backend/`).
  Hecho cuando: para un registro pendiente y para una solicitud de cambio de contraseña vigentes,
  con su código correcto, devuelve su caducidad; devuelve nada si el código es otro, si el proceso
  ya validó el código, si está caducado, si su `public_id` cambió (reemplazo) o si no existe; un
  `public_id` de registro no sirve como solicitud ni a la inversa; queda registrado al arrancar
  Django; suite verde.

- [ ] T-023 Proveedor por entorno y barrido en el planificador
  RF: RF-024 (D-02, D-14) | Depende de: T-013 | Archivos: 3
  Archivos: `config/settings.py`, `.env.example`, `apps/emails/tests/test_settings.py` (en
  `backend/`).
  Hecho cuando: con `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
  `EMAIL_USE_SSL`, `EMAIL_TIMEOUT` y `DEFAULT_FROM_EMAIL` en el entorno, la configuración usa el
  backend SMTP con esos valores; sin `EMAIL_BACKEND` definido, usa el de consola;
  `CELERY_BEAT_SCHEDULE` incluye `dispatch_due` cada 30 s; `.env.example` documenta todas las
  variables de la feature comentadas; suite verde.

- [ ] T-024 Panel de plantillas
  RF: RF-020, RF-021, RF-022 (D-16) | Depende de: T-004, T-007 | Archivos: 2
  Archivos: `admin.py`, `tests/test_admin.py`.
  Hecho cuando: un miembro de «Soporte técnico» y un superusuario ven y editan asunto y cuerpo; un
  staff sin el grupo recibe 403; no hay botón ni vista para añadir ni borrar; guardar una plantilla
  inválida muestra cada problema y no cambia la fila; el historial se ve y no se puede revertir;
  suite verde.

- [ ] T-025 Panel de correos fallidos
  RF: RF-017 (D-12) | Depende de: T-015, T-024 | Archivos: 4
  Archivos: `admin.py`, `models.py`, `migrations/0001_initial.py`, `tests/test_admin.py`.
  Hecho cuando: el proxy `FailedEmail` lista solo las filas `failed` con tipo, idioma,
  destinatario, fecha, intentos y último error; soporte puede verlas y borrarlas, pero no
  editarlas ni crearlas; las filas `pending` no aparecen; suite verde.
  Excepción: el modelo proxy exige regenerar `0001_initial.py` con `makemigrations`.

- [ ] T-026 Permisos de «Soporte técnico»
  RF: RF-017, RF-020 (D-13) | Depende de: T-024, T-025 | Archivos: 2
  Archivos: `migrations/0003_support_permissions.py`, `tests/test_migrations.py`.
  Hecho cuando: tras `migrate` sobre una base vacía, el grupo «Soporte técnico» tiene ver y cambiar
  plantillas y ver y borrar correos fallidos, además de sus permisos de `consents`; deshacer la
  migración quita solo esos permisos; suite verde.

- [ ] T-027 Comando `emails test`
  RF: RF-025 | Depende de: T-013, T-016 | Archivos: 4
  Archivos: `management/__init__.py`, `management/commands/__init__.py`,
  `management/commands/emails.py`, `tests/test_command.py`.
  Hecho cuando: `manage.py emails test --kind registration_code --locale pt-BR --to x@ejemplo.com`
  deja una fila `pending` con datos de ejemplo y la muestra; un tipo o idioma desconocido da un
  error del comando; suite verde.
  Excepción: los dos `__init__.py` son el esqueleto obligatorio de los comandos de Django.

- [ ] T-028 Comandos `emails notify` y `emails dispatch`
  RF: RF-009 | Depende de: T-016, T-027 | Archivos: 2
  Archivos: `management/commands/emails.py`, `tests/test_command.py`.
  Hecho cuando: `manage.py emails notify --kind account_disabled --email ana@ejemplo.com` encola el
  aviso en el idioma de la cuenta; también `password_changed` y `sessions_closed`; otro tipo o un
  correo sin cuenta da un error del comando; `manage.py emails dispatch` encola los pendientes
  vencidos y dice cuántos; suite verde.

- [ ] T-029 Un correo sale por el worker real
  RF: RF-002 (CF-1) | Depende de: T-013 | Archivos: 1
  Archivos: `tests/test_worker.py`.
  Hecho cuando: con el worker de Celery real del fixture de `core` y el backend en memoria, un aviso
  encolado y confirmado acaba entregado y su fila borrada; suite verde.

- [ ] T-030 Documentación operativa
  RF: — (CF-4) | Depende de: T-023 | Archivos: 1
  Archivos: `HUMAN_TODO.md` (en la raíz).
  Hecho cuando: la guía de MXroute nombra las variables reales de T-023 en su paso de SOPS; hay una
  entrada para definir `EMAIL_CODE_SECRET` en producción; el comando de T-027 para enviar un correo
  real de prueba va en su propio bloque.

- [ ] T-031 Resumen de la feature
  RF: — (CF-5) | Depende de: T-030 y las tareas de M-10 en `procesos-pendientes` y `cambio-contrasena` | Archivos: 1
  Archivos: `specs/correo-asincrono-plantillas/resumen.md` (en la raíz).
  Hecho cuando: explica qué se hizo; cómo provocar desde consola cada tipo de correo y ver un fallo
  reintentado con el proveedor simulado; la configuración completa del envío (subdominio y buzón de
  MXroute, registros de Cloudflare, variables de entorno y su lugar en SOPS) para rehacerla o
  cambiar de proveedor; y un «Marco teórico» con SPF, DKIM y DMARC, la bandeja de salida, la
  máscara del código y la entrega al menos una vez; todos sus comandos son copiables.

## RF sin tarea
- RF-008 (aviso de contraseña restablecida) y RF-019 (mismo trabajo exista o no la cuenta): sin
  tarea en esta feature. Los implementan las tareas de M-10 en `procesos-pendientes` y
  `cambio-contrasena`, que se crearán con su `sdd-plan` y `sdd-tareas`.
- RF-004, RF-005 y RF-006: aquí solo se cubren el enlace (T-003), el tope (T-017) y la bandeja;
  el envío desde cada operación también es de M-10.
- La validación de esta feature espera a que esas tareas estén hechas (CF-6).
