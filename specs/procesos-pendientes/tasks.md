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

- [ ] T-011 Reenviar el código
  RF: RF-016 | Depende de: T-010 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: `resend` conserva el `public_id`, emite un código nuevo (el anterior deja de valer)
  y pone los intentos a 0, también tras un bloqueo; se rechaza con el código ya validado o en un
  registro caducado; suite verde.

- [ ] T-012 Política de contraseñas local
  RF: RF-022 | Depende de: — | Archivos: 2
  Archivos: `backend/config/settings.py`, `tests/test_password_policy.py`.
  Hecho cuando: `validate_password` rechaza 11 caracteres, una contraseña parecida al correo o al
  nombre de un `User` sin guardar y una común, y acepta una buena de 12; los 27 tests del spike y
  los de `auth-headless` siguen en verde; suite verde.

- [ ] T-013 Validador de contraseñas filtradas
  RF: RF-022 | Depende de: T-001 | Archivos: 2
  Archivos: `password_validation.py`, `tests/test_password_policy.py`.
  Hecho cuando, con la respuesta del servicio simulada: rechaza una contraseña cuyo sufijo de
  SHA-1 aparece con recuento > 0; acepta si no aparece o aparece con 0 (relleno); solo envía los 5
  primeros caracteres; con tiempo agotado o error de red acepta y escribe un aviso en el log;
  suite verde.

- [ ] T-014 Activar el validador de filtradas y apagarlo en los tests
  RF: RF-022, RF-019 | Depende de: T-013, T-012 | Archivos: 3
  Archivos: `backend/config/settings.py`, `tests/conftest.py`, `tests/test_password_policy.py`.
  Hecho cuando: `AUTH_PASSWORD_VALIDATORS` incluye el validador; con `PWNED_PASSWORDS_ENABLED`
  apagado no hace ninguna petición (lo comprueba un test); un fixture automático lo apaga en toda
  la suite de `accounts`; suite verde sin acceso a internet.

- [ ] T-015 Completar el registro
  RF: RF-020, RF-012, RF-022 | Depende de: T-011, T-014 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: con el código validado y una contraseña válida se crea la cuenta (correo, nombre,
  fecha y país del registro; `EmailAddress` verificado y principal) y se borra el registro, todo o
  nada; esa cuenta inicia sesión por app; una contraseña inválida se rechaza con cada regla
  incumplida y conserva el registro; sin código validado o caducado se rechaza; si el correo ya
  tiene cuenta se rechaza y se borra el registro; suite verde.

- [ ] T-016 Purgar registros caducados
  RF: RF-013 | Depende de: T-008 | Archivos: 2
  Archivos: `registration.py`, `tests/test_registration_service.py`.
  Hecho cuando: `purge_expired` borra solo los caducados (por gracia o por vida máxima) y devuelve
  cuántos borró; suite verde.

- [ ] T-017 Comando `registration`: iniciar, verificar y reenviar
  RF: RF-023 | Depende de: T-011 | Archivos: 2
  Archivos: `management/commands/registration.py`, `tests/test_registration_command.py`.
  Hecho cuando: `registration start` muestra el `public_id` y el código (o "cuenta existente");
  `verify` y `resend` muestran el resultado o el error; los datos inválidos muestran el error de
  cada campo; suite verde.

- [ ] T-018 Comando `registration`: completar y purgar
  RF: RF-023, RF-013 | Depende de: T-017, T-015, T-016 | Archivos: 2
  Archivos: `management/commands/registration.py`, `tests/test_registration_command.py`.
  Hecho cuando: `registration complete` acepta `--password` (y la pide sin eco si falta) y crea la
  cuenta o muestra cada regla incumplida; `registration purge` muestra cuántos borró; el recorrido
  `start → verify → complete` crea una cuenta que inicia sesión; suite verde. (CF-4)

- [ ] T-019 Flujo de registro en Mermaid
  RF: — (documentación, S-02) | Depende de: T-018 | Archivos: 1
  Archivos: `specs/procesos-pendientes/diagramas/flujo-registro.md`.
  Hecho cuando: el flujo en Mermaid refleja la spec aprobada (intentos, reenvío, gracia, vida
  máxima, registro repetido, reanudar con el `public_id`) y enlaza a la imagen original.

- [ ] T-020 Resumen de la feature
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

## RF sin tarea
Ninguno.
