# Tareas: registro-api
Estado: aprobado

Rutas relativas a `backend/apps/accounts/` salvo que se indique. "Suite verde" =
`cd backend && pytest -q` + `mypy .` + `ruff check .` + `black --check .` sin errores. En cada
tarea, antes de marcarla, se prueba al menos un mutante del código que introduce y debe hacer
fallar sus tests, ejecutando el archivo de tests completo (nunca con `-k`).

Ninguna tarea empieza antes de que `correo-asincrono-plantillas` esté fusionada en `main` (S-17,
CF-6). Las tareas T-009…T-011 esperan además a que esté aprobado el `sdd-cambio` de
`procesos-pendientes` que guarda los términos en el registro pendiente (S-03).

- [x] T-001 Validador del correo del registro
  RF: RF-003 (D-14) | Depende de: — | Archivos: 2
  Archivos: `validators.py`, `tests/test_validators.py`.
  Hecho cuando: `validate_registration_email` acepta `ana@example.com`, `ana+etiqueta@example.com`
  y `ana@españa.es`, y rechaza con su código `ana@localhost` y cualquier dominio sin punto
  (`email_domain_without_dot`), `ana@[192.0.2.1]` (`email_ip_domain`) y un formato inválido
  (`invalid`); el validador del modelo no cambia (un `PendingRegistration` con `ana@localhost`
  sigue pasando `full_clean`); suite verde.
  Decisiones: el dominio sin punto y la IP se comprueban antes del formato de Django, que ya
  rechaza `ana@intranet` como `invalid` y les quitaría su código propio — [Cierto] — revertir:
  llamar primero a `EmailValidator`. La comprobación del modelo se prueba con
  `validate_registration_data`, que ejecuta las mismas reglas de la cuenta sin base de datos —
  [Cierto] — revertir: un `full_clean` sobre un `PendingRegistration`.

- [x] T-002 Todos los errores del nombre a la vez
  RF: RF-002 (D-13) | Depende de: — | Archivos: 2
  Archivos: `validators.py`, `tests/test_validators.py`.
  Hecho cuando: un nombre de más de 150 caracteres con un tabulador y dos espacios seguidos produce
  en una sola `ValidationError` los códigos `name_too_long`, `name_control_char` y
  `name_consecutive_spaces`; un nombre válido sigue pasando; los tests existentes de
  `usuario-personalizado` sobre el nombre siguen en verde sin cambiar lo que afirman; suite verde.
  Decisiones: con un solo error se lanza esa `ValidationError` tal cual, y solo con varios se lanza
  una lista, para que `.code` siga existiendo donde ya se usaba — [Cierto] — revertir: lanzar
  siempre la lista. El nombre vacío sigue siendo un error único, porque excluye los demás —
  [Cierto] — revertir: acumularlo también.

- [x] T-003 Idioma de la solicitud
  RF: RF-013 (D-06) | Depende de: — | Archivos: 3
  Archivos: `api/__init__.py`, `api/language.py`, `tests/test_registration_api_language.py`.
  Hecho cuando: `request_language` devuelve `pt-BR` para el campo `pt_BR` o `pt-br`; con el campo
  ausente o inválido usa `Accept-Language` por idioma base y en su orden de preferencia
  (`pt-PT` → `pt-BR`, `es-MX` → `es`, `en-GB` → `en`, `fr, en;q=0.8` → `en`); sin campo válido ni
  cabecera reconocible devuelve `es`; suite verde.
  Decisiones: el campo admite las mismas variantes de escritura que `locales.normalize`, pero con su
  propia tabla, porque `normalize` convierte lo desconocido en `es` y no deja pasar a la cabecera —
  [Cierto] — revertir: añadir a `locales` una función que devuelva `None`. Una cabecera ilegible
  se trata como ausente (Django devuelve una lista vacía) — [Cierto] — revertir: no aplica.

- [x] T-004 Catálogo de textos por idioma
  RF: RF-013, RF-002, RF-005 (D-05; CF-7) | Depende de: T-001, T-003 | Archivos: 2
  Archivos: `api/messages.py`, `tests/test_registration_api_messages.py`.
  Hecho cuando: el catálogo tiene texto en `es`, `pt-BR` y `en` para el mensaje neutro (S-13), el
  límite superado y estos códigos: `required`, `null`, `blank`, `invalid`,
  `email_domain_without_dot`, `email_ip_domain`, `name_empty`, `name_too_long`,
  `name_control_char`, `name_consecutive_spaces`, `birthdate_in_future`,
  `birthdate_under_minimum_age`, `country_invalid`, `terms_not_accepted`, `document_not_found`,
  `wrong_kind`, `no_current_version` y `not_current_document`; un test falla si algún código no
  tiene texto en alguno de los tres idiomas; los parámetros (`%(max)d`, `%(years)d`, `%(days)d`) se
  sustituyen en los tres; suite verde.
  Decisiones: `invalid` tiene un texto genérico y textos propios para el correo y la fecha
  (`FIELD_ERRORS`), porque «el valor no es válido» no dice qué corregir en esos dos campos —
  [Probable] — revertir: quitar `FIELD_ERRORS`. `null` usa el mismo texto que `required` —
  [Probable] — revertir: darle uno propio. Los 21 textos y sus traducciones se revisan en el PR,
  como S-17 de `correo-asincrono-plantillas` — [Cierto] — revertir: no aplica.

- [x] T-005 Documento mostrado como función pública de `consents`
  RF: RF-004 (M-07, refactor) | Depende de: — | Archivos: 2
  Archivos: `backend/apps/consents/services.py`, `backend/apps/consents/tests/test_services.py`.
  Hecho cuando: `current_document_shown(kind, version=, locale=)` es pública, `accept_terms` y
  `grant_marketing` la usan, un test la llama directamente con cada código de error
  (`document_not_found`, `wrong_kind`, `no_current_version`, `not_current_document`), y los tests
  existentes de `consents` siguen en verde sin cambiar lo que afirman; suite verde.

- [x] T-006 Serializador del formulario
  RF: RF-002, RF-003, RF-004 (M-02, D-13) | Depende de: T-001, T-002, T-004, T-005 | Archivos: 2
  Archivos: `api/serializers.py`, `tests/test_registration_api_serializer.py`.
  Hecho cuando: con datos válidos devuelve los datos normalizados y el documento; cada campo
  ausente, nulo, vacío o mal formado da su código de DRF; nombre, fecha y país dan los códigos de
  sus validadores, el correo los de T-001; un formulario con varios campos inválidos devuelve los
  errores de todos (CF-4); términos: sin `accepted` o con `false` → `terms_not_accepted`, y cada
  motivo de `current_document_shown` con su código; un documento vigente en otro idioma que el de
  la solicitud se acepta (S-21); el serializador no consulta cuentas ni registros pendientes (test
  con `django_assert_num_queries` que solo admite las consultas de términos); todos los códigos que
  emite están en el catálogo de T-004; suite verde.
  Decisiones: `terms` es un `JSONField` validado a mano, y no un serializador anidado, para que sus
  errores salgan en una lista plana bajo `terms` («error en el campo de términos», RF-004) —
  [Cierto] — revertir: serializador anidado y aplanar en la vista. Un documento sin `version` o sin
  `locale` da `required` bajo `terms`, el código de «no indica el documento» — [Probable] —
  revertir: un código propio en el catálogo. La marca solo vale con el booleano `true` de JSON
  (`"true"` y `1` no cuentan) — [Probable] — revertir: aceptar los valores verdaderos de DRF. La
  prueba de que no se consultan cuentas ni registros comprueba que ninguna consulta toca tablas
  `accounts_`, en vez de contar consultas — [Cierto] — revertir: `django_assert_num_queries`.

- [x] T-007 Límites configurables
  RF: RF-012 (M-06) | Depende de: — | Archivos: 3
  Archivos: `conf.py`, `backend/config/settings.py`, `tests/test_registration_conf.py`.
  Hecho cuando: `REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS` (60),
  `REGISTRATION_RATE_EMAIL_IP_PER_HOUR` (5) y `REGISTRATION_RATE_IP_PER_HOUR` (20) se leen del
  entorno con esos valores por defecto y `conf.py` los expone; con `settings` cambiados, `conf.py`
  devuelve los nuevos; suite verde.

- [x] T-008 Límite de frecuencia por correo e IP y por IP
  RF: RF-010, RF-011, RF-012 (M-06, D-07, D-08, D-09) | Depende de: T-007 | Archivos: 2
  Archivos: `throttling.py`, `tests/test_registration_throttling.py`.
  Hecho cuando, con la hora inyectada: una segunda solicitud con el mismo correo e IP antes de 60 s
  se rechaza con la espera que falta; la sexta en una hora se rechaza hasta que la primera salga de
  la ventana; el mismo correo desde otra IP no se ve afectado (C-01); la IP se rechaza tras 20 en
  una hora; las rechazadas no se apuntan (la ventana se libera sola, S-06); `Ana@X.com ` y
  `ana@x.com` cuentan juntas; la clave de caché usa `consent_email_fingerprint` y no contiene el
  correo; con los límites cambiados por `settings` se aplican los nuevos; suite verde.
  Decisiones: una marca sale de la ventana cuando cumple exactamente una hora, y la espera se
  redondea hacia arriba a segundos enteros (nunca «espera 0 segundos») — [Cierto] — revertir:
  `>=` en el filtro y `round`. La hora es la del reloj del servidor (`time.time()`), inyectable en
  los tests — [Cierto] — revertir: no aplica.

- [x] T-009 Documento de términos en el registro pendiente
  RF: RF-009 (M-07, D-10) | Depende de: — | Archivos: 3
  Archivos: `models.py`, `migrations/0012_pendingregistration_terms.py`,
  `tests/test_pending_registration_model.py`.
  Hecho cuando: `migrate` aplica `0012`; `PendingRegistration` guarda `terms_version` y
  `terms_locale`, vacíos por defecto en los registros existentes (C-13);
  `makemigrations accounts --check --dry-run` no detecta cambios; suite verde.

- [x] T-010 Empezar el registro con el documento
  RF: RF-006, RF-007, RF-008 (M-07; S-11) | Depende de: T-009 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: `start` recibe `terms_version` y `terms_locale` y los guarda en el `payload` de la
  plaza; al resolverla con un correo nuevo, el registro pendiente tiene ese documento y se encola el
  código (RF-006); con un registro pendiente vigente, se conservan sus datos y su documento aunque la
  solicitud traiga otros (RF-007); con un correo con cuenta, no hay registro pendiente con ese
  `public_id` (CF-3) y el aviso se encola solo si la cuenta está activa (RF-008); los comandos de
  consola de RF-023 de `procesos-pendientes` siguen funcionando sin documento; suite verde.
  Decisiones: el `payload` de la plaza solo lleva `terms_version` y `terms_locale` cuando se indica
  un documento, para no cambiar la plaza de los registros de consola — [Cierto] — revertir:
  guardarlos siempre, vacíos si no hay documento.

- [x] T-011 Aceptación de los términos al completar
  RF: RF-009 (M-07, D-11; S-12) | Depende de: T-005, T-010 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: completar un registro con un documento vigente crea la cuenta y una aceptación de
  ese documento con la fecha de compleción, en la misma transacción (si la creación de la cuenta
  falla, no queda aceptación); con un documento que dejó de ser vigente, borrado, o sin documento
  guardado, la cuenta se crea sin aceptación; antes de completar no existe ninguna aceptación nueva
  para ese correo, y las de una cuenta borrada con el mismo correo no cambian; suite verde.
  Decisiones: se omite la aceptación ante cualquier `ValidationError` de `accept_terms` (documento
  inexistente, de otro tipo o no vigente), no solo ante «no vigente», porque todos significan que el
  documento guardado ya no se puede aceptar — [Probable] — revertir: filtrar por `error.code`. La
  atomicidad se prueba con un fallo al borrar el registro pendiente, que ocurre después de la
  aceptación — [Cierto] — revertir: no aplica.

- [x] T-012 Vista y rutas de la API
  RF: RF-001, RF-002, RF-005, RF-013, RF-014 (M-01, D-01…D-04, D-12) | Depende de: T-003, T-004, T-006, T-010 | Archivos: 4
  Archivos: `api/views.py`, `api/urls.py`, `backend/config/urls.py`,
  `tests/test_registration_api.py`.
  Hecho cuando: `POST /api/browser/v1/registration` y `POST /api/app/v1/registration` con datos
  válidos responden `202` con `public_id` y el mensaje neutro, y llaman a `start` con los datos,
  el documento y el idioma resuelto; con errores responden `400` con
  `{"errors": {campo: [{code, message}]}}` y los textos en el idioma pedido; la ruta web sin CSRF
  (`APIClient(enforce_csrf_checks=True)`) responde `403` sin llamar a `start`, y con CSRF responde
  `202`; la ruta de aplicación sin CSRF ni `Origin` responde `202` (S-19); una sesión iniciada no
  cambia la respuesta (S-14); suite verde.
  Excepción: la ruta no se puede probar sin la vista, su `urls.py` y el `include` en
  `config/urls.py`; separar el `include` dejaría una tarea sin comportamiento observable.
  Decisiones: el CSRF de la ruta web se exige con `CSRFCheck` de DRF en `initial()` de una subclase
  de la vista, no con `csrf_protect`, porque `csrf_protect` no actúa sobre una vista marcada como
  exenta (todas las de DRF lo están); el efecto es el de D-02 — [Cierto] — revertir: no aplica. El
  `403` es el de DRF (`{"detail": …}`), no la página de Django — [Probable] — revertir: devolver
  la respuesta de `process_view`. Un código de error que no esté en el catálogo provoca un error 500
  en vez de un texto genérico: los tests garantizan que todos los que emite el serializador están
  (T-006) — [Probable] — revertir: texto de `invalid` como respaldo en `_render`.

- [ ] T-013 Límites en la vista
  RF: RF-010, RF-011 (M-01, D-12) | Depende de: T-008, T-012 | Archivos: 2
  Archivos: `api/views.py`, `tests/test_registration_api_limits.py`.
  Hecho cuando: superado el límite por IP, la vista responde `429` con `retry_after` y la cabecera
  `Retry-After` sin validar (un cuerpo inválido también recibe `429`); superado el de correo e IP,
  responde `429` tras validar; una solicitud inválida cuenta para la IP pero no para el correo; una
  rechazada por CSRF o por un límite no cuenta; en ningún `429` se llama a `start`; suite verde.

- [ ] T-014 Respuesta neutra en los tres casos
  RF: RF-005, RF-008, RF-010 (CF-2, CF-3) | Depende de: T-012, T-013 | Archivos: 1
  Archivos: `tests/test_registration_api_neutrality.py`.
  Hecho cuando: para un correo nuevo, uno con registro pendiente vigente, uno con cuenta activa y
  uno con cuenta inactiva, por las dos rutas, las respuestas `202` tienen el mismo código, el mismo
  cuerpo salvo el valor de `public_id` (mismo formato), las mismas cabeceras y las mismas cookies; lo
  mismo para las respuestas `429` del límite por correo e IP; tras resolver la plaza del correo con
  cuenta, su `public_id` no corresponde a ningún registro pendiente (CF-3); suite verde.

- [ ] T-015 Configuración de ejemplo, resumen y acciones humanas
  RF: RF-012 (M-08; CF-5) | Depende de: T-014 | Archivos: 3
  Archivos: `backend/.env.example`, `specs/registro-api/resumen.md`,
  `specs/cambio-contrasena/HUMAN_TODO.md`.
  Hecho cuando: `.env.example` lista los tres límites con sus valores por defecto; `resumen.md`
  explica qué se hizo y cómo probar con `curl` cada caso, las dos rutas (la web obteniendo antes el
  token CSRF), los errores por campo, los dos límites y el idioma, leyendo el código en el correo que
  muestra el proveedor local, con un «Marco teórico» de los conceptos que generaron dudas; el
  `HUMAN_TODO.md` de `cambio-contrasena` indica que el límite del formulario de registro ya existe y
  que los del reenvío, la verificación y el restablecimiento siguen pendientes (S-15); cada comando
  de `resumen.md` se ha ejecutado contra el entorno Docker y da lo que el texto dice.

- [ ] T-016 Resumen de procesos-pendientes tras el cambio de términos
  RF: RF-009 | Depende de: T-011 | Archivos: 1
  Archivos: `specs/procesos-pendientes/resumen.md`.
  Hecho cuando: el resumen explica que el registro pendiente guarda el documento de términos
  aceptado, que completar el registro registra su aceptación si sigue vigente, y que un registro
  empezado desde consola o antes del cambio se completa sin aceptación; los comandos que cite se
  han ejecutado y dan lo que el texto dice.

## RF sin tarea
Ninguno.
