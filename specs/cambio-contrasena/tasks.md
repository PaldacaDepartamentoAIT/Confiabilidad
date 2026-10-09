# Tareas: cambio-contrasena
Estado: aprobado

Rutas relativas a `backend/apps/accounts/` salvo que se indique. "Suite verde" =
`cd backend && pytest -q` + `mypy .` + `ruff check .` + `black --check .` sin errores. En cada
tarea, antes de marcarla, se prueba al menos un mutante del código que introduce y debe hacer
fallar sus tests, ejecutando el archivo de tests completo (nunca con `-k`). Mientras la feature no
esté terminada, `migrations/0006_passwordresetrequest.py` se regenera en cada tarea que cambia el
esquema, para que al final quede una sola migración (M-07).

- [x] T-001 Huella del código con el tipo de proceso
  RF: RF-005 (D-01) | Depende de: — | Archivos: 5
  Archivos: `codes.py`, `tests/test_codes.py`, `registration.py`,
  `tests/test_registration_service.py`, `tests/test_registration_command.py`.
  Hecho cuando: `code_fingerprint` y `verify_code` exigen el tipo (`registration` o
  `password_reset`); la huella es el HMAC-SHA256 de `<tipo>:<public_id>:<código>`; el mismo
  `public_id` y código dan huellas distintas con tipos distintos, y una huella de un tipo no valida
  con el otro (también con el secreto anterior en transición); la suite del registro sigue en verde
  con el tipo `registration`; suite verde.
  Excepción: el cambio de firma obliga a ajustar las llamadas existentes en el servicio y en dos
  archivos de tests del registro; es un cambio mecánico que no se puede separar sin dejar la suite
  rota entre tareas.

- [x] T-002 Huella de la cuenta
  RF: RF-014, RF-015 (D-04) | Depende de: T-001 | Archivos: 2
  Archivos: `codes.py`, `tests/test_codes.py`.
  Hecho cuando: `account_stamp(email, password_hash)` es el HMAC-SHA256 de
  `password_reset_account:<correo en minúsculas>:<hash>` (64 hexadecimales, sin el correo);
  `"Ana@X.com"` y `"ana@x.com"` dan la misma; otro correo u otro hash dan otra;
  `account_stamp_matches` acepta la del secreto vigente y la del anterior durante la transición, y
  rechaza la anterior fuera de ella; suite verde.

- [x] T-003 Base abstracta `CodeProcess`
  RF: RF-005, RF-006, RF-012 (D-02, refactor) | Depende de: — | Archivos: 2
  Archivos: `models.py`, `tests/test_migrations.py`.
  Hecho cuando: `PendingRegistration` hereda de `CodeProcess` (campos, `expires_at`, `is_expired`,
  `is_locked` y el queryset con `expired()`); un test nuevo ejecuta
  `makemigrations accounts --check --dry-run` y no detecta cambios; la suite del registro sigue en
  verde sin tocarla; suite verde.
  Decisiones: `CodeProcessQuerySet` es genérico en el modelo para que mypy tipe `expired()` en cada
  proceso — [Cierto] — revertir: un queryset por modelo.

- [x] T-004 Modelo `PasswordResetRequest` y migración `0006`
  RF: RF-001, RF-006, RF-010 | Depende de: T-003 | Archivos: 3
  Archivos: `models.py`, `migrations/0006_passwordresetrequest.py`,
  `tests/test_password_reset_model.py`.
  Hecho cuando: `migrate` aplica `0006`; se guardan los campos de RF-001 con `account_stamp`; una
  segunda solicitud para la misma cuenta falla también por `bulk_create` (`IntegrityError`); un
  `public_id` repetido falla; borrar la cuenta borra su solicitud; `expired()` incluye las caducadas
  por gracia y por vida máxima y excluye las vigentes; `makemigrations --check` sin cambios; suite
  verde. (CF-1)

- [x] T-005 Operaciones comunes del código
  RF: RF-005, RF-007 (D-03) | Depende de: T-001, T-003 | Archivos: 3
  Archivos: `processes.py`, `registration.py`, `tests/test_processes.py`.
  Hecho cuando: `issue_code`, `check_code` y `renew_code` cubren, sobre un `CodeProcess`, ya
  validado, bloqueado, código caducado, código erróneo (suma un intento), código correcto (marca la
  validación) y reenvío (mismo `public_id`, código nuevo, intentos a 0); `VerifyResult` vive en
  `processes.py` y `registration.VerifyResult` sigue existiendo; `registration.verify`,
  `registration.resend` y `registration.start` las usan y la suite del registro sigue en verde sin
  tocarla; suite verde.
  Decisiones: `issue_code` no guarda (cada servicio decide entre alta y reemplazo, y el reemplazo
  usa `ISSUED_FIELDS`), mientras que `renew_code` y `check_code` sí guardan — [Cierto] — revertir:
  que `issue_code` guarde y devuelva el proceso. `registration` reexporta `VerifyResult`
  explícitamente porque mypy estricto no admite la reexportación implícita — [Cierto] — revertir:
  importar `VerifyResult` desde `processes` en el comando y los tests.

- [x] T-006 Pedir el cambio de contraseña
  RF: RF-002, RF-003, RF-004 (D-05, D-06) | Depende de: T-002, T-004, T-005 | Archivos: 2
  Archivos: `password_reset.py`, `tests/test_password_reset_service.py`.
  Hecho cuando: `start` con el correo de una cuenta activa (con mayúsculas y espacios) crea la
  solicitud y devuelve `public_id` y código que verifica con el tipo `password_reset`; repetir
  reemplaza la vigente y la caducada (`public_id`, código y huella de la cuenta nuevos, intentos a
  0, sin validar, `created_at` nuevo) y el código anterior deja de valer; un correo sin cuenta y una
  cuenta inactiva devuelven el mismo `NoEligibleAccount` sin crear ni tocar ninguna solicitud
  (tampoco la que la cuenta inactiva tuviera); un `IntegrityError` simulado en el alta se traduce en
  reemplazo; suite verde.
  Decisiones: un `IntegrityError` en el alta que no se explica por una solicitud de la misma cuenta
  (p. ej. un `public_id` repetido) se propaga en vez de ocultarse — [Cierto] — revertir: reintentar
  el alta con otro `public_id`.

- [x] T-007 Verificar y reenviar
  RF: RF-005, RF-006, RF-007, RF-008, RF-014, RF-015 | Depende de: T-006 | Archivos: 2
  Archivos: `password_reset.py`, `tests/test_password_reset_service.py`.
  Hecho cuando: `verify` acepta el código correcto, suma intentos con el erróneo, bloquea al 5.º,
  rechaza el código caducado, la solicitud caducada (por gracia y por vida máxima), el código ya
  validado y un `public_id` de registro pendiente; `resend` conserva el `public_id`, emite código
  nuevo y pone los intentos a 0, y se rechaza si está validada o caducada; con la cuenta inactiva,
  con el correo cambiado o con la contraseña cambiada, ambos rechazan sin modificar la fila, y al
  reactivar la cuenta vuelven a funcionar; suite verde.
  Decisiones: el orden de comprobación es existencia → caducidad → estado de la cuenta → reglas del
  código, así que una solicitud caducada responde "caducada" aunque la cuenta también haya cambiado
  — [Probable] — revertir: mover `_account_refusal` antes de la caducidad. `ResendRefusal` es propio
  de este servicio (mismos valores que el del registro) para no acoplarlo a `registration` —
  [Probable] — revertir: moverlo a `processes.py` y compartirlo. El bloqueo usa
  `select_for_update(of=("self",))` para no bloquear la fila de la cuenta, según D-05 — [Cierto].

- [x] T-008 Completar el cambio
  RF: RF-008, RF-009, RF-014, RF-015 (D-05, D-07) | Depende de: T-007 | Archivos: 2
  Archivos: `password_reset.py`, `tests/test_password_reset_service.py`.
  Hecho cuando: con el código validado, `complete` fija la contraseña (la cuenta inicia sesión con
  ella), marca verificada la `EmailAddress` existente, la crea verificada y principal si no existe,
  y no principal si la cuenta ya tiene otra principal, y borra la solicitud; acepta la contraseña
  actual si cumple la política; una contraseña débil o parecida al correo o al nombre de la cuenta
  lanza `ValidationError` con cada regla y conserva la solicitud y la contraseña anterior; se rechaza
  sin cambiar nada con código sin validar, solicitud caducada, cuenta inactiva, correo cambiado o
  contraseña cambiada; suite verde.
  Decisiones: si la dirección de correo de la cuenta ya existe y está verificada, no se toca
  (tampoco su marca de principal) — [Cierto] — revertir: forzar `primary=True` en esa dirección.
  Si la solicitud cambia de cuenta o desaparece entre la lectura sin bloqueo y el bloqueo, se
  responde `NOT_FOUND` — [Cierto] — revertir: reintentar la lectura.

- [x] T-009 Contador de inicios fallidos y sesiones abiertas
  RF: RF-009 (D-08, D-12; CF-3) | Depende de: T-008 | Archivos: 2
  Archivos: `password_reset.py`, `tests/test_password_reset_sessions.py`.
  Hecho cuando: tras 5 inicios de sesión fallidos por app, el correcto se rechaza
  (`too_many_login_attempts`); tras completar el cambio, el inicio de sesión con la nueva contraseña
  funciona; si `complete` falla, el contador se conserva; una sesión de navegador y un
  `X-Session-Token` abiertos antes de completar reciben 401 después; suite verde.
  Decisiones: el test de sesiones pasó desde el principio porque fija un comportamiento que ya existe
  (S-03, D-12), no uno nuevo — [Cierto]. Las funciones internas de allauth reciben un `HttpRequest`
  vacío: con `SITE_ID` y una tasa por clave no leen nada de la petición — [Cierto] — revertir: pasar
  la petición real cuando exista API. Los tests usan correo e IP aleatorios porque los contadores de
  allauth viven en Redis y sobreviven entre ejecuciones — [Cierto]. Que la tasa por IP no cambie no
  tiene test: borrarla exigiría la IP del cliente, que el servicio no conoce — [Probable].

- [x] T-010 Purga y límites compartidos
  RF: RF-011, RF-012 | Depende de: T-007 | Archivos: 2
  Archivos: `password_reset.py`, `tests/test_password_reset_service.py`.
  Hecho cuando: `purge_expired` borra solo las solicitudes caducadas, devuelve cuántas y no toca
  registros pendientes caducados; con `override_settings` de `REGISTRATION_MAX_FAILED_ATTEMPTS`,
  `REGISTRATION_CODE_TTL_MINUTES`, `REGISTRATION_GRACE_MINUTES` y
  `REGISTRATION_MAX_LIFETIME_MINUTES` cambian el bloqueo, la vigencia del código y la caducidad de
  las solicitudes; suite verde.
  Decisiones: los tests de límites pasaron sin código nuevo porque el servicio ya usa la base y las
  operaciones comunes (T-003, T-005); fijan RF-012 para que una separación futura de límites no
  pase desapercibida — [Cierto].

- [x] T-011 Utilidades de consola compartidas
  RF: RF-013 (D-09, refactor) | Depende de: — | Archivos: 2
  Archivos: `management/console.py`, `management/commands/registration.py`.
  Hecho cuando: mostrar `public_id` y código, formatear `ValidationError` y pedir la contraseña sin
  eco viven en `console.py`, el comando `registration` los usa y `tests/test_registration_command.py`
  sigue en verde sin tocarlo; `manage.py help` no lista `console` como comando; suite verde.
  Decisiones: pedir la contraseña sin eco se queda en cada comando (una línea con `getpass`) en vez
  de pasar a `console.py`: su test parchea `getpass` a través del módulo del comando y moverla
  obligaría a tocar ese test, que la tarea exige dejar intacto — [Cierto] — revertir: moverla y
  cambiar el destino del parche en los tests.

- [x] T-012 Comando `manage.py password_reset`
  RF: RF-004, RF-011, RF-013 | Depende de: T-008, T-010, T-011 | Archivos: 2
  Archivos: `management/commands/password_reset.py`, `tests/test_password_reset_command.py`.
  Hecho cuando: con `call_command`, `start --email` muestra `public_id` y `code`; `verify`,
  `resend` y `complete` (con `--password` y pidiéndola sin eco) recorren el cambio y `complete`
  muestra la cuenta; cada rechazo termina en `CommandError` con su mensaje; sin cuenta elegible
  muestra "No active account with this email."; `purge` muestra `deleted: N`; suite verde. (CF-4)
  Decisiones: la cuenta inactiva y la cuenta cambiada tienen mensajes propios en consola ("The
  account is inactive.", "The account's email or password changed after the request; start
  again."); son seguros en consola (S-06) y la API deberá decidir cómo mostrarlos — [Probable] —
  revertir: un único mensaje genérico.

- [x] T-013 Documentación operativa
  RF: RF-012 (D-10; CF-5) | Depende de: — | Archivos: 2
  Archivos: `backend/.env.example`, `HUMAN_TODO.md`.
  Hecho cuando: `.env.example` dice que los límites `REGISTRATION_*` y el secreto de los códigos
  valen también para el cambio de contraseña; `HUMAN_TODO.md` incluye, como requisitos previos a
  publicar la API de cambio de contraseña, el límite de frecuencia de pedir y reenviar (por correo y
  por IP, con el riesgo de tomar cuentas ajenas) y la neutralización de "sin cuenta elegible" (mismo
  mensaje y tiempo de respuesta comparable), y la entrada de `REGISTRATION_CODE_SECRET` menciona que
  ahora protege también los códigos de cambio de contraseña.

- [x] T-014 Resumen de la feature
  RF: — (CF-4) | Depende de: T-001…T-013 | Archivos: 1
  Archivos: `specs/cambio-contrasena/resumen.md`.
  Hecho cuando: el resumen tiene "Qué se hizo", "Límites conocidos", "Cómo probarlo" con comandos
  ejecutables de principio a fin (migrar, pedir, verificar, reenviar, completar, iniciar sesión,
  purgar, suite) y "Marco teórico" con los conceptos que generaron dudas.

- [x] T-015 Corrección: completar el cambio de contraseña es todo o nada
  Tipo: corrección | Origen: validación de RF-009
  RF: RF-009 | Depende de: — | Archivos: 1
  Archivos: `tests/test_password_reset_service.py`.
  Causa: ningún test provoca un fallo después de `set_password`; el mutante que quita
  `transaction.atomic()` de `complete` sobrevive.
  Hecho cuando: un test hace fallar `complete` después de fijar la contraseña (por ejemplo,
  `_mark_email_verified` lanza `IntegrityError`) y comprueba que la contraseña sigue siendo la
  anterior, que la solicitud se conserva y que no se ha creado ninguna `EmailAddress`; el mutante sin
  `atomic()` muere ejecutando el archivo completo; la suite completa sigue en verde.

- [x] T-016 Corrección: completar no toca el contador de inicios fallidos por IP
  Tipo: corrección | Origen: validación de RF-009
  RF: RF-009 | Depende de: — | Archivos: 1
  Archivos: `tests/test_password_reset_sessions.py`.
  Causa: la cláusula "el contador por IP no cambia" no tiene aserción.
  Hecho cuando: tras inicios fallidos desde una IP conocida, el valor de la clave `login_failed` por
  IP en la caché (calculada con las funciones de `allauth.core.internal.ratelimit` y una petición
  con esa `REMOTE_ADDR`) no está vacío y es el mismo antes y después de `complete`; la suite completa
  sigue en verde.

- [x] T-017 Corrección: el identificador de una solicitud no sirve en el registro, ni a la inversa
  Tipo: corrección | Origen: validación de RF-005
  RF: RF-005 | Depende de: — | Archivos: 1
  Archivos: `tests/test_password_reset_service.py`.
  Causa: solo se prueba la dirección registro → solicitud, y sin `complete`.
  Hecho cuando: el `public_id` de una solicitud da `NOT_FOUND` en `registration.verify`,
  `registration.resend` y `registration.complete`, y el de un registro pendiente da `NOT_FOUND` en
  `password_reset.complete`, sin modificar ninguno de los dos procesos; la suite completa sigue en
  verde.

- [x] T-018 Corrección: el periodo de transición del secreto también rige el cambio de contraseña
  Tipo: corrección | Origen: validación de RF-012
  RF: RF-012 | Depende de: — | Archivos: 1
  Archivos: `tests/test_password_reset_service.py`.
  Causa: `REGISTRATION_SECRET_TRANSITION_MINUTES` solo se prueba con el registro.
  Hecho cuando: con una solicitud emitida con el secreto anterior, `password_reset.verify` rechaza
  el código con una rotación de hace 30 min y una transición de 20, y lo acepta (`VERIFIED`) con una
  transición de 120; la suite completa sigue en verde.
  Decisiones: fuera de la transición el rechazo sale como `ACCOUNT_CHANGED`, no como código erróneo,
  porque la huella de la cuenta también se firmó con el secreto anterior y se comprueba antes que el
  código (D-04) — [Cierto] — revertir: comprobar el código antes que la cuenta.

- [x] T-019 Corrección: la reactivación de la cuenta vuelve a admitir el reenvío y la compleción
  Tipo: corrección | Origen: validación de RF-008
  RF: RF-008 | Depende de: — | Archivos: 1
  Archivos: `tests/test_password_reset_service.py`.
  Causa: solo se prueba `verify` tras reactivar la cuenta; la cláusula sobre `resend` y `complete`
  no tiene aserción.
  Hecho cuando: tras desactivar la cuenta y reactivarla antes de que la solicitud caduque, `resend`
  devuelve `Resent` con el mismo `public_id`, el código nuevo verifica y `complete` devuelve
  `Completed` (contraseña fijada y solicitud borrada); la suite completa sigue en verde.
  Decisiones: el test desactiva y reactiva la cuenta con `save()`, como el panel, y no con
  `update()`: así el mutante que recuerda una desactivación pasada (vía historial) muere — [Cierto].

- [x] T-020 Corrección: la orden `password_reset purge` no borra registros pendientes
  Tipo: corrección | Origen: validación de RF-011
  RF: RF-011 | Depende de: — | Archivos: 1
  Archivos: `tests/test_password_reset_command.py`.
  Causa: el test de la orden no tiene ningún registro pendiente caducado; el mutante que llama
  también a `registration.purge_expired()` desde `_purge` sobrevive.
  Hecho cuando: con una solicitud caducada y un registro pendiente caducado,
  `call_command("password_reset", "purge")` muestra `deleted: 1` y el registro pendiente sigue
  existiendo; ese mutante muere al ejecutar el archivo completo; la suite completa sigue en verde.

- [x] T-021 Corrección: el reenvío no alarga la vida máxima de la solicitud
  Tipo: corrección | Origen: validación de RF-006
  RF: RF-006 | Depende de: — | Archivos: 1
  Archivos: `tests/test_password_reset_service.py`.
  Causa: ningún test fija que la hora de vida cuente desde el alta tras un reenvío; el mutante que
  reinicia `created_at` en `renew_code` sobrevive a la suite completa.
  Hecho cuando: con `created_at` envejecido 50 min, `resend` devuelve `Resent` y `created_at` no
  cambia; al envejecer 61 min desde el alta, `verify`, `resend` y `complete` dan `EXPIRED`; ese
  mutante muere ejecutando el archivo completo; la suite completa sigue en verde.

- [x] T-022 Corrección: se puede reenviar una solicitud vigente con el código caducado
  Tipo: corrección | Origen: validación de RF-007
  RF: RF-007 | Depende de: — | Archivos: 1
  Archivos: `tests/test_password_reset_service.py`.
  Causa: solo se reenvía con el código vigente; el mutante que rechaza el reenvío cuando el código
  caducó dentro de la gracia sobrevive a la suite completa.
  Hecho cuando: con `code_expires_at` 5 min en el pasado (solicitud vigente por la gracia), `resend`
  devuelve `Resent` con el mismo `public_id`, intentos en 0 y `code_expires_at` en el futuro, y el
  código nuevo da `VERIFIED`; ese mutante muere ejecutando el archivo completo; la suite completa
  sigue en verde.

- [ ] T-023 Corrección: completar no marca como principal una dirección secundaria existente
  Tipo: corrección | Origen: validación de RF-009
  RF: RF-009 | Depende de: — | Archivos: 1
  Archivos: `tests/test_password_reset_service.py`.
  Causa: ningún test cubre una cuenta cuyo correo ya existe como dirección no principal junto a otra
  principal; el mutante que la marca como principal sobrevive a la suite completa.
  Hecho cuando: con la dirección del correo de la cuenta no principal y sin verificar, y otra
  dirección principal, `complete` devuelve `Completed`, la dirección queda verificada y no principal
  y la otra sigue siendo la principal; ese mutante muere ejecutando el archivo completo; la suite
  completa sigue en verde.

## RF sin tarea
Ninguno.
