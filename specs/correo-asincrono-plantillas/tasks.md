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

- [x] T-002 Sustitución de variables como texto
  RF: RF-023 (D-07) | Depende de: T-001 | Archivos: 2
  Archivos: `rendering.py`, `tests/test_rendering.py`.
  Hecho cuando: `{{ name }}` y `{{name}}` se sustituyen por su valor; un nombre con acentos,
  alfabeto no latino y emoji (`"Zoë 李 👋"`) sale idéntico en asunto y cuerpo; `{{ user.__class__ }}`,
  `{% if %}` y `{name}` no se evalúan; un valor que contiene `{{ code }}` no se vuelve a sustituir;
  suite verde.
  Decisiones: (1) `rendering.placeholders(text)` lista las variables de un texto; lo usará la
  validación de T-004. [Cierto] Revertir: inlinear la expresión. (2) Una variable sin valor se deja
  tal cual en el texto en vez de vaciarla: la validación de T-004 impide guardarla, y así un fallo
  se ve en vez de producir un hueco silencioso. [Probable] Revertir: devolver `""` en `_replace`.
  (3) Un mutante que admitía puntos en el nombre sobrevivía, porque esa clave nunca está en los
  valores; lo mata `test_attribute_access_is_not_a_placeholder`. [Cierto]

- [x] T-003 Enlaces con el identificador en el fragmento
  RF: RF-004, RF-005 (D-09) | Depende de: T-002 | Archivos: 3
  Archivos: `rendering.py`, `tests/test_rendering.py`, `config/settings.py` (en `backend/`).
  Hecho cuando: con `FRONTEND_BASE_URL=https://app.ejemplo.com`, el enlace de registro es
  `https://app.ejemplo.com/register/continue#<public_id>` y el de restablecimiento
  `https://app.ejemplo.com/password-reset/continue#<public_id>`; una barra final en la dirección
  base no duplica la barra; suite verde.
  Decisiones: (1) `FRONTEND_BASE_URL` vale por defecto `http://localhost:5173`, el puerto del
  frontend en `docker-compose.yml`. [Cierto] Revertir: cambiar el valor por defecto. (2) Un propósito
  desconocido lanza `ValueError`, porque solo puede venir de un error de programación. [Probable]
  Revertir: devolver la dirección base.

- [x] T-004 Validación de plantillas al guardar
  RF: RF-021 (D-07) | Depende de: T-003 | Archivos: 3
  Archivos: `rendering.py`, `models.py`, `tests/test_rendering.py`.
  Hecho cuando: guardar una plantilla de código sin `{{ code }}`, `{{ link }}` o `{{ expires_in }}`,
  con una variable que su tipo no admite (`{{ code }}` en un aviso) o con una dirección web cuyo
  dominio no es el de `FRONTEND_BASE_URL` lanza `ValidationError` que enumera cada problema, y la
  fila guardada no cambia; una plantilla correcta se guarda; suite verde.
  Decisiones: (1) Los datos obligatorios valen en el asunto o en el cuerpo. [Probable] Revertir:
  validar solo `body`. (2) También se rechaza cualquier `{{ … }}` o `{% … %}` que no sea una
  variable simple, para que una errata no llegue tal cual al correo. [Probable] Revertir: quitar
  el primer bucle de `validate_template`. (3) Solo se detectan direcciones que empiezan por
  `http://`, `https://` o `www.`; un dominio suelto (`otro.com`) no se reconoce como enlace.
  [Cierto] Revertir: ampliar `_ADDRESS`. (4) El dominio debe ser exactamente el de
  `FRONTEND_BASE_URL`; un subdominio no vale. [Probable] Revertir: aceptar subdominios en
  `_is_application_address`. (5) `save()` valida con `full_clean` siempre, como `User`. [Cierto]
  (6) El test del guardado inválido está en `test_rendering.py` para respetar los tres archivos de
  la tarea. [Cierto]

- [x] T-005 Plazo relativo por idioma
  RF: RF-014 (D-08) | Depende de: T-002 | Archivos: 2
  Archivos: `rendering.py`, `tests/test_rendering.py`.
  Hecho cuando: con 9 min 40 s restantes da "9 minutos", "9 minutos" y "9 minutes"; con 1 min 30 s,
  "1 minuto", "1 minuto" y "1 minute"; con 59 s, "menos de un minuto", "menos de um minuto" y "less
  than a minute"; ninguna salida contiene una hora ni una fecha; suite verde.
  Decisiones: (1) Un plazo de cero o negativo también da "menos de un minuto"; la entrega descarta
  antes el código caducado (T-020). [Probable] Revertir: lanzar un error si `remaining <= 0`.

- [x] T-006 Bloque fijo de reporte en los avisos de seguridad
  RF: RF-010 (D-08) | Depende de: T-002 | Archivos: 3
  Archivos: `rendering.py`, `tests/test_rendering.py`, `config/settings.py` (en `backend/`).
  Hecho cuando: los cinco avisos terminan, después del texto editable, con el bloque de su idioma,
  que nombra `EMAIL_SUPPORT_ADDRESS` y recomienda restablecer la contraseña; los dos correos de
  código no lo llevan; el bloque no forma parte del texto guardado en la plantilla; suite verde.
  Decisiones: (1) Textos del bloque: «Si no fuiste tú, escríbenos a <soporte> y restablece tu
  contraseña cuanto antes» y sus equivalentes en pt-BR y en; se revisan en el PR (S-17). [Probable]
  Revertir: cambiar `_REPORT_BLOCKS`. (2) `EMAIL_SUPPORT_ADDRESS` vale por defecto
  `soporte@localhost`, que en producción debe definirse (T-030). [Cierto] (3) `compose()` reúne
  sustitución y bloque para que la entrega (T-013) tenga una sola llamada. [Cierto]

- [x] T-007 Plantillas iniciales
  RF: RF-001, RF-022 (CF-3, S-17) | Depende de: T-004, T-005, T-006 | Archivos: 2
  Archivos: `migrations/0002_initial_templates.py`, `tests/test_migrations.py`.
  Hecho cuando: tras `migrate` existen las 21 plantillas (7 tipos × 3 idiomas), todas pasan la
  validación de T-004; deshacer la migración las borra; suite verde. Los textos se revisan en el PR.
  Decisiones: (1) Textos del bloque: «Si no fuiste tú, escríbenos a <soporte> y restablece tu
  contraseña cuanto antes» y sus equivalentes en pt-BR y en; se revisan en el PR (S-17). [Probable]
  Revertir: cambiar `_REPORT_BLOCKS`. (2) `EMAIL_SUPPORT_ADDRESS` vale por defecto
  `soporte@localhost`, que en producción debe definirse (T-030). [Cierto] (3) `compose()` reúne
  sustitución y bloque para que la entrega (T-013) tenga una sola llamada. [Cierto]

- [x] T-008 Idiomas admitidos y normalización
  RF: RF-013 (D-10) | Depende de: — | Archivos: 2
  Archivos: `locales.py`, `tests/test_locales.py`.
  Hecho cuando: `"es"`, `"pt-BR"`, `"pt-br"`, `"pt_BR"`, `"EN"` y `" en "` se normalizan a `es`,
  `pt-BR`, `pt-BR`, `pt-BR`, `en` y `en`; `None`, `""`, `"fr"` y `"pt"` dan `es`; suite verde.
  Decisiones: (1) Una variante regional distinta de pt-BR (`es-MX`, `pt-PT`) cae en el idioma por
  defecto, no en su idioma base: la spec solo admite los tres. [Probable] Revertir: mapear la
  parte anterior al guion. (2) `LANGUAGE_CHOICES` vive aquí para que `accounts` lo use en T-009;
  `EmailTemplate.Locale` repite los mismos tres valores. [Cierto] Revertir: unificarlos.

- [x] T-009 Idioma en la cuenta y en el registro pendiente
  RF: RF-012 (D-10) | Depende de: T-008 | Archivos: 3
  Archivos: `apps/accounts/models.py`, `apps/accounts/migrations/0007_language.py`,
  `apps/accounts/tests/test_language.py` (en `backend/`).
  Hecho cuando: `User` y `PendingRegistration` tienen `language` con los tres idiomas y `es` por
  defecto; una cuenta creada antes de la migración queda en `es`; un idioma no admitido falla la
  validación; el cambio de idioma de una cuenta queda en su historial; suite verde.
  Decisiones: (1) Una variante regional distinta de pt-BR (`es-MX`, `pt-PT`) cae en el idioma por
  defecto, no en su idioma base: la spec solo admite los tres. [Probable] Revertir: mapear la
  parte anterior al guion. (2) `LANGUAGE_CHOICES` vive aquí para que `accounts` lo use en T-009;
  `EmailTemplate.Locale` repite los mismos tres valores. [Cierto] Revertir: unificarlos.

- [x] T-010 La cuenta hereda el idioma al completar el registro
  RF: RF-012 | Depende de: T-009 | Archivos: 2
  Archivos: `apps/accounts/registration.py`, `apps/accounts/tests/test_registration_service.py`
  (en `backend/`).
  Hecho cuando: completar un registro pendiente en `pt-BR` crea la cuenta en `pt-BR`; el resto de
  la suite del registro sigue en verde; suite verde.

- [x] T-011 Bandeja y encolado al confirmar
  RF: RF-002, RF-003 (D-01) | Depende de: T-001 | Archivos: 4
  Archivos: `models.py`, `outbox.py`, `migrations/0001_initial.py`, `tests/test_outbox.py`.
  Hecho cuando: pedir un correo dentro de una transacción crea su fila `pending` y, al confirmar,
  encola `deliver` con su id (una sola vez); si la transacción se deshace, no queda fila ni se
  encola nada; si encolar lanza un error de conexión, la operación termina bien y la fila queda
  `pending`; suite verde.
  Excepción: `0001_initial.py` se regenera con `makemigrations` y no se edita a mano.
  Decisiones: (1) Una variante regional distinta de pt-BR (`es-MX`, `pt-PT`) cae en el idioma por
  defecto, no en su idioma base: la spec solo admite los tres. [Probable] Revertir: mapear la
  parte anterior al guion. (2) `LANGUAGE_CHOICES` vive aquí para que `accounts` lo use en T-009;
  `EmailTemplate.Locale` repite los mismos tres valores. [Cierto] Revertir: unificarlos.

- [x] T-012 Proveedor simulado y clasificación de errores
  RF: RF-026 (D-03, D-15) | Depende de: — | Archivos: 3
  Archivos: `errors.py`, `tests/backends.py`, `tests/test_errors.py`.
  Hecho cuando: `SMTPRecipientsRefused`, `SMTPSenderRefused` y `SMTPDataError` con código 5xx son
  definitivos; con código 4xx, temporales; `SMTPServerDisconnected`, `SMTPConnectError`,
  `SMTPAuthenticationError`, `TimeoutError`, `OSError` y cualquier otra excepción son temporales;
  el backend simulado lanza en orden los errores que se le indican y guarda los mensajes que
  entrega; suite verde.
  Decisiones: (1) Un rechazo de destinatarios es definitivo solo si todos los códigos son 5xx; con
  uno solo 4xx, se reintenta. [Probable] Revertir: usar `any` en `classify`. (2) La autenticación
  fallida (535) es temporal, como dice D-03; el tercer mutante lo confirma. [Cierto]

- [x] T-013 Entrega desde la cola y barrido periódico
  RF: RF-002, RF-011 (D-01) | Depende de: T-011, T-012 | Archivos: 3
  Archivos: `tasks.py`, `delivery.py`, `tests/test_delivery.py`.
  Hecho cuando: `deliver(id)` entrega un aviso pendiente por el backend simulado, con el asunto y
  el cuerpo de la plantilla de su tipo e idioma, y borra la fila; el mensaje no lleva cabecera
  `List-Unsubscribe` ni enlace de baja; `dispatch_due()` encola las filas `pending` con el intento
  vencido y no las futuras; una fila que quedó `pending` porque la cola estaba caída sale en el
  siguiente barrido; suite verde.
  Decisiones: (1) Las tareas llevan su nombre explícito (`apps.emails.tasks.deliver`) para que no
  dependa del módulo desde el que Celery las descubre. [Cierto] (2) La reserva del intento (D-04)
  entra ya aquí: `deliver` solo toma una fila pendiente y vencida, y la aparta 5 minutos. [Cierto]
  (3) La plantilla se lee al entregar, no al encolar: un cambio de soporte vale para los correos
  pendientes. [Probable] Revertir: guardar asunto y cuerpo en la fila al encolar.

- [x] T-014 Reintentos con espera creciente y reserva del intento
  RF: RF-016, RF-026 (D-04) | Depende de: T-013 | Archivos: 3
  Archivos: `delivery.py`, `tests/test_delivery.py`, `config/settings.py` (en `backend/`).
  Hecho cuando: tras un error temporal, la fila sigue `pending` con `attempts` + 1 y el siguiente
  intento a 30 s, 60 s, 120 s… hasta un tope de 15 min; con dos errores temporales y luego éxito, se
  entrega y se borra; un aviso con más de `EMAIL_NOTICE_RETRY_HOURS` (24 por defecto) desde su
  encolado deja de reintentarse y pasa a `failed`; una fila reservada por otro intento no se envía
  dos veces; suite verde.
  Decisiones: (1) Las tareas llevan su nombre explícito (`apps.emails.tasks.deliver`) para que no
  dependa del módulo desde el que Celery las descubre. [Cierto] (2) La reserva del intento (D-04)
  entra ya aquí: `deliver` solo toma una fila pendiente y vencida, y la aparta 5 minutos. [Cierto]
  (3) La plantilla se lee al entregar, no al encolar: un cambio de soporte vale para los correos
  pendientes. [Probable] Revertir: guardar asunto y cuerpo en la fila al encolar.

- [x] T-015 Fallo definitivo y registro de fallos
  RF: RF-017, RF-026 (D-12) | Depende de: T-014 | Archivos: 2
  Archivos: `delivery.py`, `tests/test_delivery.py`.
  Hecho cuando: un error definitivo pasa la fila a `failed` al primer intento, sin reintentar; una
  fila `failed` conserva tipo, idioma, destinatario, fecha de encolado, intentos y último error, y
  no vuelve a encolarse en el barrido; suite verde.

- [x] T-016 Idioma de cada correo al encolar
  RF: RF-013 | Depende de: T-008, T-011 | Archivos: 2
  Archivos: `outbox.py`, `tests/test_outbox.py`.
  Hecho cuando: un correo de código se encola en el idioma indicado por quien lo pide (normalizado
  con T-008); un aviso de seguridad, en el `language` de la cuenta aunque se indique otro; sin
  idioma válido, en `es`; suite verde.
  Decisiones: (1) `enqueue` recibe la cuenta (`account`) en vez de una función aparte para los
  avisos, para no cambiar la interfaz de T-011. Si se pasa con un aviso, manda su idioma; con un
  correo de código se ignora. [Probable] Revertir: separar `enqueue_notice`. (2) Sin cuenta, un
  aviso usa el idioma indicado; M-10 debe pasar siempre la cuenta en los avisos. [Probable]
  (3) `outbox` importa `User` solo para los tipos (`TYPE_CHECKING`), sin dependencia en tiempo de
  ejecución hacia `accounts` (D-05). [Cierto]

- [x] T-017 Tope del aviso "ya tienes cuenta"
  RF: RF-007 (D-11) | Depende de: T-011 | Archivos: 5
  Archivos: `models.py`, `outbox.py`, `migrations/0001_initial.py`, `tests/test_outbox.py`,
  `config/settings.py` (en `backend/`).
  Hecho cuando: el primer aviso "ya tienes cuenta" de una cuenta se encola; un segundo dentro de
  `EMAIL_ACCOUNT_EXISTS_WINDOW_MINUTES` (60 por defecto) no se encola y la llamada no lanza error;
  pasada la ventana, se encola otro; el tope no afecta a otro tipo de correo ni a otra cuenta;
  borrar la cuenta borra su marca; suite verde.
  Excepción: `0001_initial.py` se regenera con `makemigrations` y la ventana necesita su ajuste en
  `settings.py`; los tres archivos restantes son el comportamiento y su test.
  Decisiones: (1) `enqueue` recibe la cuenta (`account`) en vez de una función aparte para los
  avisos, para no cambiar la interfaz de T-011. Si se pasa con un aviso, manda su idioma; con un
  correo de código se ignora. [Probable] Revertir: separar `enqueue_notice`. (2) Sin cuenta, un
  aviso usa el idioma indicado; M-10 debe pasar siempre la cuenta en los avisos. [Probable]
  (3) `outbox` importa `User` solo para los tipos (`TYPE_CHECKING`), sin dependencia en tiempo de
  ejecución hacia `accounts` (D-05). [Cierto]

- [x] T-018 El código se guarda oculto en la bandeja
  RF: RF-018 (D-06) | Depende de: T-011 y T-028 de `huellas-hmac-unificadas` | Archivos: 2
  Archivos: `outbox.py`, `tests/test_outbox.py`.
  Hecho cuando: un correo de código guarda `masked_code` y `code_nonce` (de `mask_code`) y ninguna
  columna, ni `context`, contiene el código en claro; los avisos no guardan máscara; suite verde.
  Decisiones: (1) `enqueue` recibe `purpose`, `public_id` y `code`; el propósito y el identificador
  sirven a T-020 para comprobar si el código sigue vigente. [Cierto] (2) El test de "ninguna
  columna en claro" admite una probabilidad de 1 entre un millón de que la máscara valga 0 y el
  valor coincida con el código; no se fija el nonce para probar el camino real. [Cierto]

- [x] T-019 La entrega recupera el código y borra la máscara
  RF: RF-018 (D-06) | Depende de: T-015, T-018 | Archivos: 2
  Archivos: `delivery.py`, `tests/test_delivery.py`.
  Hecho cuando: el correo entregado contiene el código original; tras entregar, descartar o fallar,
  no queda máscara ni nonce; una fila `failed` no contiene el código; el código no aparece en
  ningún mensaje de registro (`caplog`) de la entrega ni del fallo; suite verde.
  Decisiones: (1) El código y el enlace solo se añaden a los valores si la fila tiene máscara;
  `context` se convierte a texto valor a valor. [Cierto] (2) Tras un error temporal la máscara se
  conserva para el siguiente intento; solo se borra al entregar (la fila desaparece), al descartar
  (T-020) o al fallar. [Cierto]

- [x] T-020 Descarte del código que ya no sirve
  RF: RF-015 (D-05) | Depende de: T-019 | Archivos: 2
  Archivos: `delivery.py`, `tests/test_delivery.py`.
  Hecho cuando: con un comprobador registrado para el propósito que devuelve la caducidad, el
  correo se entrega; si devuelve nada (caducado, validado o reemplazado), la fila se borra sin
  enviar; tras un error temporal, se reintenta solo mientras el comprobador siga devolviendo una
  caducidad; un propósito sin comprobador registrado lanza un error de configuración; suite verde.
  Decisiones: (1) El registro de comprobadores vive en `delivery.py` (`register_code_check`); el
  comprobador recibe `public_id` y el código recuperado y devuelve la caducidad o `None`. [Cierto]
  (2) Un correo descartado se borra entero, código incluido, sin dejar rastro en el registro de
  fallos: no es un fallo del proveedor. [Probable] Revertir: marcarlo como `failed`.

- [x] T-021 Plazo calculado al entregar
  RF: RF-014 | Depende de: T-005, T-020 | Archivos: 2
  Archivos: `delivery.py`, `tests/test_delivery.py`.
  Hecho cuando: un correo encolado con 15 min de vigencia y entregado cuando quedan 6 min 10 s dice
  "6 minutos", no "15"; suite verde.

- [x] T-022 Comprobador de vigencia de `accounts`
  RF: RF-015 (D-05) | Depende de: T-020 | Archivos: 3
  Archivos: `apps/accounts/email_checks.py`, `apps/accounts/apps.py`,
  `apps/accounts/tests/test_email_checks.py` (en `backend/`).
  Hecho cuando: para un registro pendiente y para una solicitud de cambio de contraseña vigentes,
  con su código correcto, devuelve su caducidad; devuelve nada si el código es otro, si el proceso
  ya validó el código, si está caducado, si su `public_id` cambió (reemplazo) o si no existe; un
  `public_id` de registro no sirve como solicitud ni a la inversa; queda registrado al arrancar
  Django; suite verde.
  Decisiones: (1) El registro de comprobadores vive en `delivery.py` (`register_code_check`); el
  comprobador recibe `public_id` y el código recuperado y devuelve la caducidad o `None`. [Cierto]
  (2) Un correo descartado se borra entero, código incluido, sin dejar rastro en el registro de
  fallos: no es un fallo del proveedor. [Probable] Revertir: marcarlo como `failed`.

- [x] T-023 Proveedor por entorno y barrido en el planificador
  RF: RF-024 (D-02, D-14) | Depende de: T-013 | Archivos: 3
  Archivos: `config/settings.py`, `.env.example`, `apps/emails/tests/test_settings.py` (en
  `backend/`).
  Hecho cuando: con `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
  `EMAIL_USE_SSL`, `EMAIL_TIMEOUT` y `DEFAULT_FROM_EMAIL` en el entorno, la configuración usa el
  backend SMTP con esos valores; sin `EMAIL_BACKEND` definido, usa el de consola;
  `CELERY_BEAT_SCHEDULE` incluye `dispatch_due` cada 30 s; `.env.example` documenta todas las
  variables de la feature comentadas; suite verde.
  Decisiones: (1) El registro de comprobadores vive en `delivery.py` (`register_code_check`); el
  comprobador recibe `public_id` y el código recuperado y devuelve la caducidad o `None`. [Cierto]
  (2) Un correo descartado se borra entero, código incluido, sin dejar rastro en el registro de
  fallos: no es un fallo del proveedor. [Probable] Revertir: marcarlo como `failed`.

- [x] T-024 Panel de plantillas
  RF: RF-020, RF-021, RF-022 (D-16) | Depende de: T-004, T-007 | Archivos: 2
  Archivos: `admin.py`, `tests/test_admin.py`.
  Hecho cuando: un miembro de «Soporte técnico» y un superusuario ven y editan asunto y cuerpo; un
  staff sin el grupo recibe 403; no hay botón ni vista para añadir ni borrar; guardar una plantilla
  inválida muestra cada problema y no cambia la fila; el historial se ve y no se puede revertir;
  suite verde.
  Decisiones: (1) Tipo e idioma son de solo lectura en el formulario: solo se editan asunto y
  cuerpo. [Cierto] (2) `is_support` se copia del criterio de `consents` en vez de importarlo de su
  `admin.py`, para no acoplar las apps. [Probable] Revertir: moverlo a `apps/core`.

- [x] T-025 Panel de correos fallidos
  RF: RF-017 (D-12) | Depende de: T-015, T-024 | Archivos: 4
  Archivos: `admin.py`, `models.py`, `migrations/0001_initial.py`, `tests/test_admin.py`.
  Hecho cuando: el proxy `FailedEmail` lista solo las filas `failed` con tipo, idioma,
  destinatario, fecha, intentos y último error; soporte puede verlas y borrarlas, pero no
  editarlas ni crearlas; las filas `pending` no aparecen; suite verde.
  Excepción: el modelo proxy exige regenerar `0001_initial.py` con `makemigrations`.
  Decisiones: (1) Tipo e idioma son de solo lectura en el formulario: solo se editan asunto y
  cuerpo. [Cierto] (2) `is_support` se copia del criterio de `consents` en vez de importarlo de su
  `admin.py`, para no acoplar las apps. [Probable] Revertir: moverlo a `apps/core`.

- [x] T-026 Permisos de «Soporte técnico»
  RF: RF-017, RF-020 (D-13) | Depende de: T-024, T-025 | Archivos: 2
  Archivos: `migrations/0003_support_permissions.py`, `tests/test_migrations.py`.
  Hecho cuando: tras `migrate` sobre una base vacía, el grupo «Soporte técnico» tiene ver y cambiar
  plantillas y ver y borrar correos fallidos, además de sus permisos de `consents`; deshacer la
  migración quita solo esos permisos; suite verde.
  Decisiones: (1) Con la conformidad del usuario (opción a), el test de `consents` que exigía que
  el grupo tuviera solo permisos de `consents` compara ahora solo esos permisos: RF-019 de
  `consentimientos` no exige exclusividad. [Cierto] Revertir: usar un grupo propio para correos.
  (2) La migración crea el grupo si no existe (`get_or_create`) y depende de `consents.0002` para
  que, cuando exista, sea el mismo. Revertir quita solo estos cuatro permisos. [Cierto]

- [x] T-027 Comando `emails test`
  RF: RF-025 | Depende de: T-013, T-016 | Archivos: 4
  Archivos: `management/__init__.py`, `management/commands/__init__.py`,
  `management/commands/emails.py`, `tests/test_command.py`.
  Hecho cuando: `manage.py emails test --kind registration_code --locale pt-BR --to x@ejemplo.com`
  deja una fila `pending` con datos de ejemplo y la muestra; un tipo o idioma desconocido da un
  error del comando; suite verde.
  Excepción: los dos `__init__.py` son el esqueleto obligatorio de los comandos de Django.
  Decisiones: (1) Las pruebas crean su fila directamente y se encolan al confirmar: no son de
  ninguna cuenta, así que no llevan el tope de RF-007 ni el idioma de una cuenta. [Cierto] Revertir:
  pasar por `outbox.enqueue` con una cuenta de ejemplo. (2) Los correos de código de prueba llevan
  en `context` un código de ejemplo (`123456`, no secreto), su enlace y "15 minutos", sin máscara ni
  comprobación de vigencia. [Cierto] (3) Para encolar al confirmar se hizo pública
  `outbox.queue` (antes `_queue`), un cambio fuera de los archivos de la tarea. [Cierto]

- [x] T-028 Comandos `emails notify` y `emails dispatch`
  RF: RF-009 | Depende de: T-016, T-027 | Archivos: 2
  Archivos: `management/commands/emails.py`, `tests/test_command.py`.
  Hecho cuando: `manage.py emails notify --kind account_disabled --email ana@ejemplo.com` encola el
  aviso en el idioma de la cuenta; también `password_changed` y `sessions_closed`; otro tipo o un
  correo sin cuenta da un error del comando; `manage.py emails dispatch` encola los pendientes
  vencidos y dice cuántos; suite verde.
  Decisiones: (1) `notify` busca la cuenta sin distinguir mayúsculas ni espacios, como el resto
  del proyecto, y pasa la cuenta a `enqueue`, que elige su idioma. [Cierto] (2) Solo admite los
  tres avisos sin acción propia; los demás los provoca su operación (M-10). [Cierto]

- [x] T-029 Un correo sale por el worker real
  RF: RF-002 (CF-1) | Depende de: T-013 | Archivos: 1
  Archivos: `tests/test_worker.py`.
  Hecho cuando: con el worker de Celery real del fixture de `core` y el backend en memoria, un aviso
  encolado y confirmado acaba entregado y su fila borrada; suite verde.
  Decisiones: (1) El fixture del worker real se copia del de `core` en el propio archivo, porque los
  fixtures de `apps/core/tests/conftest.py` no llegan a `apps/emails`. [Cierto] (2) El test pasa sin
  código nuevo (la entrega es de T-013); un mutante que renombra la tarea lo hace fallar. [Cierto]

- [x] T-030 Documentación operativa
  RF: — (CF-4) | Depende de: T-023 | Archivos: 1
  Archivos: `HUMAN_TODO.md` (en la raíz).
  Hecho cuando: la guía de MXroute nombra las variables reales de T-023 en su paso de SOPS; hay una
  entrada para definir `EMAIL_CODE_SECRET` en producción; el comando de T-027 para enviar un correo
  real de prueba va en su propio bloque.

- [x] T-031 Resumen de la feature
  RF: — (CF-5) | Depende de: T-030 y las tareas de M-10 en `procesos-pendientes` y `cambio-contrasena` | Archivos: 1
  Archivos: `specs/correo-asincrono-plantillas/resumen.md` (en la raíz).
  Hecho cuando: explica qué se hizo; cómo provocar desde consola cada tipo de correo y ver un fallo
  reintentado con el proveedor simulado; la configuración completa del envío (subdominio y buzón de
  MXroute, registros de Cloudflare, variables de entorno y su lugar en SOPS) para rehacerla o
  cambiar de proveedor; y un «Marco teórico» con SPF, DKIM y DMARC, la bandeja de salida, la
  máscara del código y la entrega al menos una vez; todos sus comandos son copiables.

- [x] T-032 Corrección: el historial conserva el texto inicial de cada plantilla
  Tipo: corrección | Origen: validación de RF-020
  RF: RF-020 | Depende de: — | Archivos: 3
  Archivos: `migrations/0004_initial_template_history.py`, `tests/test_migrations.py`,
  `tests/test_admin.py`.
  Causa: `0002_initial_templates` crea las plantillas sin registro de historial; el primer cambio
  desde el panel perdía el texto anterior.
  Hecho cuando: tras migrar, cada una de las 21 plantillas tiene un registro de historial con su
  texto inicial; tras editar una desde el panel, su historial muestra el texto anterior, el nuevo, el
  autor y la fecha; aplicar la migración otra vez no duplica registros y deshacerla quita solo esos;
  suite verde.
  Decisiones: (1) Una plantilla que ya tiene historial (editada antes de esta migración) no recibe
  el registro inicial: su texto original ya no se puede recuperar. [Cierto] (2) El registro inicial
  lleva la fecha de la instalación (`updated_at`) y el motivo «Initial text», que es lo que borra
  deshacer la migración. [Cierto]

- [ ] T-033 Corrección: rechazar dominios sueltos y otros esquemas en las plantillas
  Tipo: corrección | Origen: validación de RF-021
  RF: RF-021 | Depende de: — | Archivos: 2
  Archivos: `rendering.py`, `tests/test_rendering.py`.
  Causa: solo se detectaban direcciones con `http(s)://` o `www.`; `evil.com/login`,
  `seguridad-app.com` o `ftp://evil.com/x` se guardaban y los clientes de correo los convierten en
  enlace.
  Hecho cuando: guardar una plantilla con `evil.com/login`, `seguridad-app.com`, `ftp://evil.com/x` o
  `https:/evil.com` lanza `ValidationError` que nombra cada dirección; una dirección del dominio de
  `FRONTEND_BASE_URL` se acepta; las 21 plantillas iniciales siguen siendo válidas; suite verde.

- [ ] T-034 Documentación tras la validación
  RF: — (CF-5) | Depende de: T-032, T-033, T-034 de `cambio-contrasena` | Archivos: 3
  Archivos: `specs/correo-asincrono-plantillas/resumen.md`, `specs/correo-asincrono-plantillas/tasks.md`,
  `specs/correo-asincrono-plantillas/spec.md` (rutas desde la raíz).
  Hecho cuando: el resumen recoge el historial inicial, la validación de dominios sueltos y el idioma
  del reenvío; en `tasks.md`, las decisiones copiadas de otra tarea (T-007, T-009, T-011, T-014,
  T-017, T-022, T-023 y T-025) se sustituyen por las reales, reconstruidas del commit de cada tarea,
  o por «sin decisiones fuera del plan»; el historial de la spec registra su aprobación del
  2026-10-14.

## RF sin tarea
- RF-008 (aviso de contraseña restablecida) y RF-019 (mismo trabajo exista o no la cuenta): sin
  tarea en esta feature. Los implementan las tareas de M-10 en `procesos-pendientes` y
  `cambio-contrasena`, que se crearán con su `sdd-plan` y `sdd-tareas`.
- RF-004, RF-005 y RF-006: aquí solo se cubren el enlace (T-003), el tope (T-017) y la bandeja;
  el envío desde cada operación también es de M-10.
- La validación de esta feature espera a que esas tareas estén hechas (CF-6).
