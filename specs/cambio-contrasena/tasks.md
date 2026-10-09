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

- [ ] T-006 Pedir el cambio de contraseña
  RF: RF-002, RF-003, RF-004 (D-05, D-06) | Depende de: T-002, T-004, T-005 | Archivos: 2
  Archivos: `password_reset.py`, `tests/test_password_reset_service.py`.
  Hecho cuando: `start` con el correo de una cuenta activa (con mayúsculas y espacios) crea la
  solicitud y devuelve `public_id` y código que verifica con el tipo `password_reset`; repetir
  reemplaza la vigente y la caducada (`public_id`, código y huella de la cuenta nuevos, intentos a
  0, sin validar, `created_at` nuevo) y el código anterior deja de valer; un correo sin cuenta y una
  cuenta inactiva devuelven el mismo `NoEligibleAccount` sin crear ni tocar ninguna solicitud
  (tampoco la que la cuenta inactiva tuviera); un `IntegrityError` simulado en el alta se traduce en
  reemplazo; suite verde.

- [ ] T-007 Verificar y reenviar
  RF: RF-005, RF-006, RF-007, RF-008, RF-014, RF-015 | Depende de: T-006 | Archivos: 2
  Archivos: `password_reset.py`, `tests/test_password_reset_service.py`.
  Hecho cuando: `verify` acepta el código correcto, suma intentos con el erróneo, bloquea al 5.º,
  rechaza el código caducado, la solicitud caducada (por gracia y por vida máxima), el código ya
  validado y un `public_id` de registro pendiente; `resend` conserva el `public_id`, emite código
  nuevo y pone los intentos a 0, y se rechaza si está validada o caducada; con la cuenta inactiva,
  con el correo cambiado o con la contraseña cambiada, ambos rechazan sin modificar la fila, y al
  reactivar la cuenta vuelven a funcionar; suite verde.

- [ ] T-008 Completar el cambio
  RF: RF-008, RF-009, RF-014, RF-015 (D-05, D-07) | Depende de: T-007 | Archivos: 2
  Archivos: `password_reset.py`, `tests/test_password_reset_service.py`.
  Hecho cuando: con el código validado, `complete` fija la contraseña (la cuenta inicia sesión con
  ella), marca verificada la `EmailAddress` existente, la crea verificada y principal si no existe,
  y no principal si la cuenta ya tiene otra principal, y borra la solicitud; acepta la contraseña
  actual si cumple la política; una contraseña débil o parecida al correo o al nombre de la cuenta
  lanza `ValidationError` con cada regla y conserva la solicitud y la contraseña anterior; se rechaza
  sin cambiar nada con código sin validar, solicitud caducada, cuenta inactiva, correo cambiado o
  contraseña cambiada; suite verde.

- [ ] T-009 Contador de inicios fallidos y sesiones abiertas
  RF: RF-009 (D-08, D-12; CF-3) | Depende de: T-008 | Archivos: 2
  Archivos: `password_reset.py`, `tests/test_password_reset_sessions.py`.
  Hecho cuando: tras 5 inicios de sesión fallidos por app, el correcto se rechaza
  (`too_many_login_attempts`); tras completar el cambio, el inicio de sesión con la nueva contraseña
  funciona; si `complete` falla, el contador se conserva; una sesión de navegador y un
  `X-Session-Token` abiertos antes de completar reciben 401 después; suite verde.

- [ ] T-010 Purga y límites compartidos
  RF: RF-011, RF-012 | Depende de: T-007 | Archivos: 2
  Archivos: `password_reset.py`, `tests/test_password_reset_service.py`.
  Hecho cuando: `purge_expired` borra solo las solicitudes caducadas, devuelve cuántas y no toca
  registros pendientes caducados; con `override_settings` de `REGISTRATION_MAX_FAILED_ATTEMPTS`,
  `REGISTRATION_CODE_TTL_MINUTES`, `REGISTRATION_GRACE_MINUTES` y
  `REGISTRATION_MAX_LIFETIME_MINUTES` cambian el bloqueo, la vigencia del código y la caducidad de
  las solicitudes; suite verde.

- [ ] T-011 Utilidades de consola compartidas
  RF: RF-013 (D-09, refactor) | Depende de: — | Archivos: 2
  Archivos: `management/console.py`, `management/commands/registration.py`.
  Hecho cuando: mostrar `public_id` y código, formatear `ValidationError` y pedir la contraseña sin
  eco viven en `console.py`, el comando `registration` los usa y `tests/test_registration_command.py`
  sigue en verde sin tocarlo; `manage.py help` no lista `console` como comando; suite verde.

- [ ] T-012 Comando `manage.py password_reset`
  RF: RF-004, RF-011, RF-013 | Depende de: T-008, T-010, T-011 | Archivos: 2
  Archivos: `management/commands/password_reset.py`, `tests/test_password_reset_command.py`.
  Hecho cuando: con `call_command`, `start --email` muestra `public_id` y `code`; `verify`,
  `resend` y `complete` (con `--password` y pidiéndola sin eco) recorren el cambio y `complete`
  muestra la cuenta; cada rechazo termina en `CommandError` con su mensaje; sin cuenta elegible
  muestra "No active account with this email."; `purge` muestra `deleted: N`; suite verde. (CF-4)

- [ ] T-013 Documentación operativa
  RF: RF-012 (D-10; CF-5) | Depende de: — | Archivos: 2
  Archivos: `backend/.env.example`, `HUMAN_TODO.md`.
  Hecho cuando: `.env.example` dice que los límites `REGISTRATION_*` y el secreto de los códigos
  valen también para el cambio de contraseña; `HUMAN_TODO.md` incluye, como requisitos previos a
  publicar la API de cambio de contraseña, el límite de frecuencia de pedir y reenviar (por correo y
  por IP, con el riesgo de tomar cuentas ajenas) y la neutralización de "sin cuenta elegible" (mismo
  mensaje y tiempo de respuesta comparable), y la entrada de `REGISTRATION_CODE_SECRET` menciona que
  ahora protege también los códigos de cambio de contraseña.

- [ ] T-014 Resumen de la feature
  RF: — (CF-4) | Depende de: T-001…T-013 | Archivos: 1
  Archivos: `specs/cambio-contrasena/resumen.md`.
  Hecho cuando: el resumen tiene "Qué se hizo", "Límites conocidos", "Cómo probarlo" con comandos
  ejecutables de principio a fin (migrar, pedir, verificar, reenviar, completar, iniciar sesión,
  purgar, suite) y "Marco teórico" con los conceptos que generaron dudas.

## RF sin tarea
Ninguno.
