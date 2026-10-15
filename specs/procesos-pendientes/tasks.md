# Tareas: procesos-pendientes
Estado: aprobado

Rutas relativas a `backend/apps/accounts/` salvo que se indique. "Suite verde" =
`cd backend && pytest -q` + `mypy .` + `ruff check .` + `black --check .` sin errores. En cada
tarea, antes de marcarla, se prueba al menos un mutante del código que introduce y debe hacer
fallar sus tests.

- [x] T-001 Límites configurables con valores por defecto
  RF: RF-019 | Depende de: — | Archivos: 3
  Archivos: `conf.py`, `backend/config/settings.py`, `tests/test_registration_conf.py`.
  Hecho cuando: sin variables de entorno, `conf` devuelve 5 intentos, 15 min de código, 15 min de
  gracia, 1 h de vida, 1 h de transición del secreto y 2 s de espera de HIBP, y el secreto vale
  `SECRET_KEY`; con `override_settings` devuelve los valores cambiados; suite verde.

- [x] T-002 Código, identificador público y huella
  RF: RF-007, RF-008 | Depende de: T-001 | Archivos: 2
  Archivos: `codes.py`, `tests/test_codes.py`.
  Hecho cuando: el código tiene 6 dígitos (también con ceros a la izquierda); `public_id` es
  aleatorio y apto para URL; la huella es HMAC del `public_id` + código, no contiene el código y
  cambia con otro secreto o con otro `public_id`; la verificación acepta el código correcto y
  rechaza el resto; suite verde.

- [x] T-003 Rotación del secreto de los códigos
  RF: RF-015 | Depende de: T-002 | Archivos: 2
  Archivos: `codes.py`, `tests/test_codes.py`.
  Hecho cuando: una huella hecha con el secreto anterior se acepta dentro del periodo de
  transición y se rechaza fuera de él o sin secreto anterior configurado; suite verde.

- [x] T-004 Documentar las variables nuevas y el secreto de producción
  RF: RF-019, RF-015 (documentación) | Depende de: T-001 | Archivos: 2
  Archivos: `backend/.env.example`, `HUMAN_TODO.md`.
  Hecho cuando: `.env.example` lista las variables nuevas sin valores reales y `HUMAN_TODO.md`
  pide definir `REGISTRATION_CODE_SECRET` cifrado con SOPS en producción.

- [x] T-005 Modelo `PendingRegistration` con sus restricciones únicas
  RF: RF-001, RF-003, RF-007 | Depende de: T-002 | Archivos: 3
  Archivos: `models.py`, `migrations/0005_pendingregistration.py`,
  `tests/test_pending_registration_model.py`.
  Hecho cuando: `migrate` aplica `0005`; se guardan todos los campos de RF-001; dos registros con
  "Ana@x.com" y "ana@x.com" chocan también por `bulk_create` (`IntegrityError`); dos con el mismo
  `public_id` chocan; suite verde. (CF-1)

- [x] T-006 Validación del registro pendiente y correo con cuenta
  RF: RF-002, RF-004 | Depende de: T-005 | Archivos: 2
  Archivos: `models.py`, `tests/test_pending_registration_model.py`.
  Hecho cuando: el correo se guarda sin espacios y en minúsculas, el nombre recortado y el país en
  mayúsculas; un nombre, edad o país inválido lanza `ValidationError`; un correo que pertenece a
  una cuenta (activa o no, sin distinguir mayúsculas) no se guarda; suite verde.

- [x] T-007 Caducidad y bloqueo calculados
  RF: RF-010, RF-011 | Depende de: T-006 | Archivos: 2
  Archivos: `models.py`, `tests/test_pending_registration_model.py`.
  Hecho cuando: un registro caduca a los 15 min de caducar su código o a la 1 h de su alta, lo que
  llegue antes (moviendo las fechas con `update()`); está bloqueado con 5 intentos fallidos; con
  otros límites en `override_settings` cambian los resultados; suite verde.

- [x] T-008 Iniciar el registro
  RF: RF-004, RF-017 | Depende de: T-007 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: `start` crea el registro y devuelve `public_id` y el código en claro (que no queda
  guardado); con un correo con cuenta devuelve "cuenta existente" sin guardar nada; borra antes un
  registro caducado del mismo correo; suite verde.

- [x] T-009 Registro repetido
  RF: RF-005, RF-003 | Depende de: T-008 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: repetir `start` con un correo con registro vigente conserva sus datos, descarta
  los nuevos, cambia el `public_id`, emite un código nuevo, pone los intentos a 0 y anula la
  validación del código; el `public_id` y el código anteriores dejan de valer; suite verde.

- [x] T-010 Verificar el código
  RF: RF-009, RF-010, RF-011 | Depende de: T-008 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: el código correcto marca el código como validado; uno incorrecto suma un intento;
  con 5 fallos se rechaza incluso el correcto; se rechaza en un registro caducado o con el código
  ya validado; un `public_id` desconocido se rechaza; suite verde.

- [x] T-011 Reenviar el código
  RF: RF-016 | Depende de: T-010 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: `resend` conserva el `public_id`, emite un código nuevo (el anterior deja de valer)
  y pone los intentos a 0, también tras un bloqueo; se rechaza con el código ya validado o en un
  registro caducado; suite verde.

- [x] T-012 Política de contraseñas local
  RF: RF-022 | Depende de: — | Archivos: 2
  Archivos: `backend/config/settings.py`, `tests/test_password_policy.py`.
  Hecho cuando: `validate_password` rechaza 11 caracteres, una contraseña parecida al correo o al
  nombre de un `User` sin guardar y una común, y acepta una buena de 12; los 27 tests del spike y
  los de `auth-headless` siguen en verde; suite verde.

- [x] T-013 Validador de contraseñas filtradas
  RF: RF-022 | Depende de: T-001 | Archivos: 2
  Archivos: `password_validation.py`, `tests/test_password_policy.py`.
  Hecho cuando, con la respuesta del servicio simulada: rechaza una contraseña cuyo sufijo de
  SHA-1 aparece con recuento > 0; acepta si no aparece o aparece con 0 (relleno); solo envía los 5
  primeros caracteres; con tiempo agotado o error de red acepta y escribe un aviso en el log;
  suite verde.

- [x] T-014 Activar el validador de filtradas y apagarlo en los tests
  RF: RF-022, RF-019 | Depende de: T-013, T-012 | Archivos: 3
  Archivos: `backend/config/settings.py`, `tests/conftest.py`, `tests/test_password_policy.py`.
  Hecho cuando: `AUTH_PASSWORD_VALIDATORS` incluye el validador; con `PWNED_PASSWORDS_ENABLED`
  apagado no hace ninguna petición (lo comprueba un test); un fixture automático lo apaga en toda
  la suite de `accounts`; suite verde sin acceso a internet.

- [x] T-015 Completar el registro
  RF: RF-020, RF-012, RF-022 | Depende de: T-011, T-014 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: con el código validado y una contraseña válida se crea la cuenta (correo, nombre,
  fecha y país del registro; `EmailAddress` verificado y principal) y se borra el registro, todo o
  nada; esa cuenta inicia sesión por app; una contraseña inválida se rechaza con cada regla
  incumplida y conserva el registro; sin código validado o caducado se rechaza; si el correo ya
  tiene cuenta se rechaza y se borra el registro; suite verde.

- [x] T-016 Purgar registros caducados
  RF: RF-013 | Depende de: T-008 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: `purge_expired` borra solo los caducados (por gracia o por vida máxima) y devuelve
  cuántos borró; suite verde.

- [x] T-017 Comando `registration`: iniciar, verificar y reenviar
  RF: RF-023 | Depende de: T-011 | Archivos: 2
  Archivos: `management/commands/registration.py`, `tests/test_registration_command.py`.
  Hecho cuando: `registration start` muestra el `public_id` y el código (o "cuenta existente");
  `verify` y `resend` muestran el resultado o el error; los datos inválidos muestran el error de
  cada campo; suite verde.

- [x] T-018 Comando `registration`: completar y purgar
  RF: RF-023, RF-013 | Depende de: T-017, T-015, T-016 | Archivos: 2
  Archivos: `management/commands/registration.py`, `tests/test_registration_command.py`.
  Hecho cuando: `registration complete` acepta `--password` (y la pide sin eco si falta) y crea la
  cuenta o muestra cada regla incumplida; `registration purge` muestra cuántos borró; el recorrido
  `start → verify → complete` crea una cuenta que inicia sesión; suite verde. (CF-4)

- [x] T-019 Flujo de registro en Mermaid
  RF: — (documentación, S-02) | Depende de: T-018 | Archivos: 1
  Archivos: `specs/procesos-pendientes/diagramas/flujo-registro.md`.
  Hecho cuando: el flujo en Mermaid refleja la spec aprobada (intentos, reenvío, gracia, vida
  máxima, registro repetido, reanudar con el `public_id`) y enlaza a la imagen original.

- [x] T-020 Resumen de la feature
  RF: todos (documentación) | Depende de: T-001…T-019 | Archivos: 1
  Archivos: `specs/procesos-pendientes/resumen.md`.
  Hecho cuando: el resumen contiene qué se hizo, cómo recorrer el registro con `manage.py
  registration` (pasos ejecutables), los límites conocidos y el marco teórico; se probó en una
  instalación limpia como en `usuario-personalizado`. (CF-3, CF-4)

- [x] T-021 Corrección: rechazar un secreto de códigos vacío
  Tipo: corrección | Origen: hallazgo al implementar T-004
  RF: RF-008 | Depende de: T-001 | Archivos: 2
  Archivos: `conf.py`, `tests/test_registration_conf.py`.
  Causa: `env("REGISTRATION_CODE_SECRET", default=SECRET_KEY)` devuelve `""` si la variable
  existe pero está vacía, y las huellas se firmarían con un secreto vacío.
  Hecho cuando: `conf.code_secret()` lanza `ImproperlyConfigured` si el secreto está vacío o solo
  tiene espacios, y si el secreto anterior es igual al vigente; suite verde.

- [x] T-022 Corrección: `public_id` que empiezan por "-" en el comando `registration`
  Tipo: corrección | Origen: validación (RF-023)
  RF: RF-023 | Depende de: — | Archivos: 3
  Archivos: `codes.py`, `tests/test_codes.py`, `tests/test_registration_command.py`.
  Causa: `token_urlsafe` puede devolver un valor que empieza por "-" (1 de cada 64) y argparse lo
  toma por una opción en `verify`, `resend` y `complete`.
  Hecho cuando: `generate_public_id` repite la generación hasta obtener un valor que no empieza
  por "-" (un test fuerza primero "-…"); un test del comando recorre `verify`, `resend` y
  `complete` con un `public_id` que empezaría por "-"; suite verde.

- [x] T-023 Corrección: un registro caducado del mismo correo no se trata como repetido
  Tipo: corrección | Origen: validación (RF-011, RF-017)
  RF: RF-011, RF-017 | Depende de: — | Archivos: 1
  Archivos: `tests/test_registration_service.py`.
  Causa: el test solo compara `public_id` y solo cubre la caducidad por vida máxima.
  Hecho cuando: con un registro caducado por gracia y otro por vida máxima, con mayúsculas
  distintas, `start` deja un único registro con los datos nuevos, vigente y cuyo código verifica;
  los mutantes `iexact`→`exact` y "solo vida máxima" fallan; suite verde.

- [x] T-024 Corrección: completar cuando el correo tiene una cuenta inactiva
  Tipo: corrección | Origen: validación (RF-012)
  RF: RF-012 | Depende de: — | Archivos: 1
  Archivos: `tests/test_registration_service.py`.
  Causa: solo se prueba con una cuenta activa.
  Hecho cuando: el test de cuenta creada entretanto se parametriza con cuenta activa e inactiva,
  devuelve `ACCOUNT_EXISTS` y borra el registro; el mutante `User.active` falla; suite verde.

- [x] T-025 Corrección: límites leídos de variables de entorno y vigencia del código al repetir
  Tipo: corrección | Origen: validación (RF-019)
  RF: RF-019 | Depende de: — | Archivos: 2
  Archivos: `tests/test_registration_conf.py`, `tests/test_registration_service.py`.
  Causa: solo se prueba con `override_settings` y la vigencia al repetir coincide con la gracia
  por defecto.
  Hecho cuando: un test carga la configuración con las variables de entorno de los límites y
  comprueba los valores; repetir un registro con `REGISTRATION_CODE_TTL_MINUTES=5` deja una
  vigencia de 5 min; los mutantes "nombre de variable mal escrito" y `code_ttl`→`grace_period`
  fallan; suite verde.

- [x] T-026 Corrección: el registro caducado del mismo correo con espacios se reemplaza
  Tipo: corrección | Origen: segunda validación (RF-017)
  RF: RF-017 | Depende de: — | Archivos: 1
  Archivos: `tests/test_registration_service.py`.
  Causa: el test de reemplazo de caducados no usa un correo con espacios; el mutante "sin
  `.strip()`" sobrevive.
  Hecho cuando: con un registro caducado de "ana@x.com", `start(" ANA@X.com ")` deja un único
  registro con los datos nuevos y vigente; el mutante falla; suite verde.

- [x] T-027 Corrección: el código usa todo el rango de 6 dígitos
  Tipo: corrección | Origen: segunda validación (RF-008)
  RF: RF-008 | Depende de: — | Archivos: 1
  Archivos: `tests/test_codes.py`.
  Causa: el mutante `randbelow(10**5)` sobrevive.
  Hecho cuando: un test comprueba que `randbelow` recibe `10**6`; el mutante falla; suite verde.

- [x] T-028 Corrección: una respuesta cortada de Have I Been Pwned también falla abierto
  Tipo: corrección | Origen: segunda validación (RF-022)
  RF: RF-022 | Depende de: — | Archivos: 2
  Archivos: `password_validation.py`, `tests/test_password_policy.py`.
  Causa: solo se capturan `OSError` y `ValueError`; `http.client.IncompleteRead` (y el resto de
  `HTTPException`) escapan y romperían el registro.
  Hecho cuando: con el servicio simulado lanzando `http.client.IncompleteRead`, la contraseña se
  acepta y queda el aviso en el log; suite verde.

- [x] T-029 Modelo `PhantomProcess` y migración `0008`
  RF: RF-025 (D-12, M-08, M-10) | Depende de: — | Archivos: 3
  Archivos: `models.py`, `migrations/0008_phantomprocess.py`, `tests/test_phantom_model.py`.
  Hecho cuando: `PhantomProcess` hereda los campos de `CodeProcess` y tiene `purpose`
  (`registration` o `password_reset`), `email` normalizado y `payload` nulo; su `public_id` es
  único en la base de datos; con `code_hash` vacío, `processes.check_code` da `WRONG_CODE` para
  cualquier código, `LOCKED` tras 5 intentos fallidos, `CODE_EXPIRED` y caducidad igual que un
  registro pendiente; `migrate` se aplica sobre la última de `main`; suite verde.
  Decisiones: (1) `PhantomProcess.save()` normaliza el correo y valida con `full_clean` (salvo la
  huella vacía), como `PendingRegistration`. [Cierto] (2) `__str__` muestra propósito y
  `public_id`, no el correo. [Cierto]

- [x] T-030 Validar los datos sin consultar cuentas
  RF: RF-002, RF-024 (M-01) | Depende de: — | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: `validate_registration_data` rechaza con un error por campo un nombre, una fecha,
  un país o un formato de correo inválidos; un correo con cuenta, activa o no, no da error; no
  hace ninguna consulta a la base de datos (`django_assert_num_queries(0)`); suite verde.
  Decisiones: (1) `PhantomProcess.save()` normaliza el correo y valida con `full_clean` (salvo la
  huella vacía), como `PendingRegistration`. [Cierto] (2) `__str__` muestra propósito y
  `public_id`, no el correo. [Cierto]

- [x] T-031 Tiempo de reintento de empezar el registro
  RF: RF-019 (M-04) | Depende de: — | Archivos: 3
  Archivos: `conf.py`, `config/settings.py` (en `backend/`), `tests/test_registration_conf.py`.
  Hecho cuando: `conf.start_retry_window()` vale 5 min por defecto, sigue a
  `REGISTRATION_START_RETRY_MINUTES` con `override_settings` y se lee de la variable de entorno;
  suite verde.

- [x] T-032 Resolver una plaza fuera de la respuesta
  RF: RF-004, RF-005, RF-006, RF-008, RF-017, RF-025 (D-16, M-09) | Depende de: T-029 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_background.py`.
  Hecho cuando, llamando a `resolve_registration(public_id)` sobre una plaza sin resolver:
  - sin cuenta ni registro pendiente: crea el registro pendiente con los datos y el `public_id` de
    la plaza, borra la plaza y deja en la bandeja el correo con el código (oculto) en el idioma de
    la solicitud;
  - con un registro pendiente vigente del mismo correo: le asigna el `public_id` de la plaza, código
    nuevo, intentos a 0 y sin validar, conserva sus datos, borra la plaza y encola el correo;
  - con cuenta activa: la plaza se queda con `payload` vacío y se encola un aviso "ya tienes
    cuenta" a la cuenta; con cuenta inactiva, sin correo;
  - borra antes los registros pendientes caducados y las demás plazas del mismo correo;
  - una plaza ya resuelta o inexistente no hace nada; un choque de unicidad del correo se trata
    como registro repetido;
  - suite verde.
  Decisiones: (1) `processes.issue_code` acepta un `public_id` opcional para emitir el código con el
  identificador de la plaza; cambio fuera de los archivos de la tarea, en el módulo común. [Cierto]
  (2) El correo del registro repetido va en el idioma de la solicitud nueva, con el nombre guardado
  (RF-005 conserva los datos; RF-013 de correo pide el idioma de la petición). [Probable]
  (3) Si la cuenta aparece entre la comprobación y el alta, `save()` lanza `ValidationError` y la
  tarea de T-033 reintenta, que ya ve la cuenta. [Probable]

- [x] T-033 Tareas, reintentos y barrido de plazas sin resolver
  RF: RF-019, RF-024 (D-15, M-09) | Depende de: T-031, T-032 | Archivos: 3
  Archivos: `tasks.py`, `config/settings.py` (en `backend/`), `tests/test_registration_background.py`.
  Hecho cuando: la tarea `apps.accounts.tasks.resolve_registration` llama a la resolución; si
  falla, se reintenta con espera creciente mientras la plaza tenga menos de la ventana de T-031;
  pasada la ventana, vacía el `payload`, deja la plaza como identificador sin registro y registra el
  fallo en el log; `sweep_unresolved()` encola las plazas sin resolver dentro de la ventana y no
  las demás; `CELERY_BEAT_SCHEDULE` lo ejecuta cada 60 s; suite verde.
  Decisiones: (1) `processes.issue_code` acepta un `public_id` opcional para emitir el código con el
  identificador de la plaza; cambio fuera de los archivos de la tarea, en el módulo común. [Cierto]
  (2) El correo del registro repetido va en el idioma de la solicitud nueva, con el nombre guardado
  (RF-005 conserva los datos; RF-013 de correo pide el idioma de la petición). [Probable]
  (3) Si la cuenta aparece entre la comprobación y el alta, `save()` lanza `ValidationError` y la
  tarea de T-033 reintenta, que ya ve la cuenta. [Probable]

- [x] T-034 Empezar el registro en la respuesta solo con el identificador
  RF: RF-023, RF-024 (D-11, M-03, M-06) | Depende de: T-030, T-033 | Archivos: 7
  Archivos: `registration.py`, `management/commands/registration.py`, `tests/factories.py`,
  `tests/test_registration_service.py`, `tests/test_registration_command.py`,
  `tests/test_email_checks.py`, `tests/test_password_reset_service.py`.
  Hecho cuando: `start` con datos válidos crea la plaza con los datos, encola la resolución al
  confirmar y devuelve solo el `public_id`, con el mismo tipo de resultado y el mismo número de
  consultas con y sin cuenta; con datos inválidos, rechaza cada error sin mencionar la cuenta y sin
  crear plaza; `manage.py registration start` admite `--language` y muestra solo el `public_id`,
  igual con y sin cuenta; los tests que necesitan un registro real usan el ayudante
  `make_pending` de `tests/factories.py`, que resuelve la plaza y devuelve su código del correo de
  la bandeja; suite verde.
  Excepción: cambiar lo que devuelve `start` rompe a la vez todos los tests que lo llaman
  (`test_password_reset_command.py` incluido si lo usa); el ajuste es mecánico y no se puede repartir
  sin dejar la suite en rojo entre tareas.
  Decisiones: (1) También se ajusta `tests/test_password_reset_command.py`, cubierto por la
  Excepción. [Cierto] (2) `manage.py registration start` ya no muestra el código: en desarrollo se
  lee en la salida del backend de consola cuando el worker resuelve la plaza. [Cierto] (3) El test de
  «mismo trabajo» compara la secuencia de sentencias SQL de `start`, no solo su número. [Cierto]
  (4) Si la cola no responde al confirmar, `start` responde igual y deja un aviso en el log; el
  barrido de T-033 recoge la plaza (D-15). [Cierto]

- [x] T-035 Verificar y completar buscando en las dos tablas
  RF: RF-009, RF-010, RF-011, RF-012, RF-025 (D-12, D-14, CF-5) | Depende de: T-034 | Archivos: 2
  Archivos: `registration.py`, `tests/test_phantom_equivalence.py`.
  Hecho cuando: para un correo con cuenta, la misma secuencia de `verify` (con el bloqueo al quinto
  intento), `complete` y caducidad da los mismos resultados con la plaza que con un registro real
  cuyo código nunca se acierta; una solicitud nueva del mismo correo deja la plaza anterior como
  desconocida, igual que a un registro real repetido; `verify` y `complete` hacen el mismo número
  de consultas en los dos casos; suite verde.
  Decisiones: (1) `complete` rechaza una plaza con `CODE_NOT_VERIFIED` aunque estuviera marcada como
  validada: no tiene datos detrás con los que crear la cuenta; un test lo fija. [Cierto] (2) La plaza
  solo se busca con el propósito del registro: la de otro propósito responde «desconocido». [Cierto]
  (3) El número de consultas se compara midiendo los dos casos en el mismo test, no con una cifra
  fija. [Cierto]

- [x] T-036 Reenvío en dos tiempos
  RF: RF-016, RF-023, RF-025 (D-13, M-09) | Depende de: T-035 | Archivos: 5
  Archivos: `registration.py`, `tasks.py`, `management/commands/registration.py`,
  `tests/test_phantom_equivalence.py`, `tests/test_registration_command.py`.
  Hecho cuando: `resend` invalida en la respuesta el código vigente, pone los intentos a 0, encola
  `reissue_code` y no devuelve el código, igual para plaza y registro real (mismo resultado y mismas
  consultas); la tarea emite el código nuevo y, si es real, encola su correo; un código anterior ya
  no se acepta; `manage.py registration resend` muestra solo el `public_id`; suite verde.
  Excepción: el reenvío cambia a la vez el servicio, su tarea y el comando que lo muestra.
  Decisiones: (1) También se ajusta `tests/test_registration_service.py`: sus tests de reenvío leían
  el código de la respuesta; es el test del mismo módulo (M-03) y el cambio es mecánico. [Cierto]
  (2) La anulación del código en la respuesta se hace con `update()`, sin `save()`: la validación de
  un registro real no admite la huella vacía. [Cierto] (3) `reissue_code` no emite nada si el
  proceso caducó, ya se validó o desapareció; tampoco reintenta: si la cola falla, el usuario pide
  otro reenvío. [Probable] (4) El correo reenviado va en el idioma guardado del registro. [Probable]

- [x] T-037 La purga borra también las plazas caducadas
  RF: RF-013 | Depende de: T-029 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: `purge_expired` borra los registros pendientes y las plazas de registro caducados,
  cuenta los dos, y no toca las plazas de cambio de contraseña ni las vigentes; suite verde.
  Decisiones: (1) Se purgan también las plazas caducadas que aún no se habían resuelto: pasada la vida
  máxima ya no se resolverán. [Probable]

- [x] T-038 Documentación del registro con correo
  RF: — (CF-4) | Depende de: T-036, T-037 | Archivos: 2
  Archivos: `backend/.env.example`, `specs/procesos-pendientes/resumen.md` (rutas desde la raíz).
  Hecho cuando: `.env.example` documenta `REGISTRATION_START_RETRY_MINUTES`; el resumen explica la
  plaza, el identificador sin registro detrás y el recorrido completo por consola leyendo el código
  en la salida del worker, con cada comando en su bloque.

## RF sin tarea
Ninguno.
