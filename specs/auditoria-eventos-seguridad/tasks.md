# Tareas: auditoria-eventos-seguridad
Estado: aprobado

Bloqueo externo (S-02): T-004 necesita que `huellas-hmac-unificadas` esté en `main`, porque
`apps/core/fingerprints.py` no existe todavía en `main`. Las tareas que no dependen de T-004 pueden
empezar antes.

- [x] T-001 Andamiaje de la app `audit`
  RF: ninguno (base de T-002) | Depende de: — | Archivos: 3
  Excepción: el test de registro necesita `apps/audit/tests/test_app.py` y `apps/audit/tests/__init__.py` (como en el resto de apps); son el cuarto y quinto archivo, y no tienen lógica.
  Hecho cuando: `python manage.py check` pasa con `audit` en `INSTALLED_APPS`.

- [x] T-002 Modelo SecurityEvent con tipos, campos e índice
  RF: RF-001, RF-002, RF-016 | Depende de: T-001 | Archivos: 3
  Excepción: `makemigrations` genera `migrations/__init__.py` junto a `0001_initial.py`; no es lógica.
  Hecho cuando: `pytest backend/apps/audit/tests/test_model.py` pasa y `python manage.py makemigrations --check` no detecta cambios.

- [x] T-003 Guardas de solo inserción
  RF: RF-012 | Depende de: T-002 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_insert_only.py` pasa: `save()` sobre una fila existente, `delete()` y `update()`/`delete()` del QuerySet lanzan error; crear filas sigue funcionando. Deja un contexto privado `_purge_allowed` que solo usa T-019.
  Decisiones: el permiso de borrado de la purga es un `ContextVar` (`_purge_allowed`), no un parámetro, para que el admin y el ORM no puedan activarlo por accidente. Confianza: [Probable]. Cómo revertirla: sustituir el contexto por un método de clase `purge_older_than` que llame a `QuerySet.delete` sin guarda, y quitar `_purge_allowed`.

- [ ] T-004 Huellas de auditoría en el punto único (M-09)
  RF: RF-011 | Depende de: T-001, huellas-hmac-unificadas en `main` | Archivos: 3
  Hecho cuando: `pytest backend/apps/core/tests/test_audit_fingerprints.py` pasa con vectores fijos del correo normalizado y de la clave de sesión; sin `AUDIT_HASH_SECRET` la configuración lanza `ImproperlyConfigured`; el guardián de huellas sigue en verde.

- [ ] T-005 Registrador `record_event`
  RF: RF-001, RF-011 | Depende de: T-002, T-004 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_recorder.py` pasa: la IP sale de `REMOTE_ADDR`, el correo se guarda solo como huella normalizada, no aparece ningún valor en claro y los metadatos se guardan.

- [ ] T-006 Receptor de inicio de sesión exitoso
  RF: RF-003 | Depende de: T-005 | Archivos: 3
  Hecho cuando: `pytest backend/apps/audit/tests/test_login_success.py` pasa: un login correcto crea una fila `LOGIN` con `success=True` cuyo `session_key` es la huella de la clave de la sesión ya rotada.

- [ ] T-007 Adaptador y registro de fallo de inicio de sesión
  RF: RF-004 | Depende de: T-005 | Archivos: 3
  Hecho cuando: `pytest backend/apps/audit/tests/test_login_failed.py` pasa: una contraseña incorrecta crea una fila `LOGIN` con `success=False` y el motivo en metadatos; un correo inexistente crea la fila sin clave de sesión; la prueba también confirma que el flujo headless llama al mismo adaptador (D-03).

- [ ] T-008 Bloqueo por límite de intentos
  RF: RF-005, RF-006 | Depende de: T-007 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_lockout.py` pasa: superar el límite crea dos filas para el mismo intento (`LOGIN` fallido y `LOCKOUT`); el contador de límite de allauth tiene el mismo valor con y sin el adaptador de auditoría. Antes de escribir el test hay que confirmar en `allauth` cómo señala el límite, porque no hay señal para ello.

- [ ] T-009 Cierre de sesión
  RF: RF-009 | Depende de: T-006 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_logout.py` pasa: un cierre de sesión crea una fila `LOGOUT` con la huella de la sesión que se cierra, capturada antes de vaciarla.

- [ ] T-010 Cambio de contraseña
  RF: RF-010 (cambio) | Depende de: T-006 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_password_changed.py` pasa: la señal `password_changed` de allauth crea una fila `PASSWORD_CHANGE` con `success=True`.

- [ ] T-011 Señales propias de accounts
  RF: RF-007, RF-008, RF-010 (contrato) | Depende de: — | Archivos: 2
  Hecho cuando: `pytest backend/apps/accounts/tests/test_signals.py` pasa: existen las nueve señales de M-08 con argumentos documentados (solicitud de registro, código enviado y validado en registro, cuenta creada, código enviado y validado en restablecimiento, restablecimiento completado, perfil editado, cuenta deshabilitada).

- [ ] T-012 Emisión de las señales desde el registro
  RF: RF-007, RF-008 | Depende de: T-011 | Archivos: 2
  Hecho cuando: `pytest backend/apps/accounts/tests/test_registration_signals.py` pasa: `start()`, `resend()`, `verify()` y `complete()` de `registration.py` emiten sus señales con el resultado correcto.

- [ ] T-013 Emisión de las señales desde el restablecimiento de contraseña
  RF: RF-008, RF-010 (restablecimiento) | Depende de: T-011 | Archivos: 2
  Hecho cuando: `pytest backend/apps/accounts/tests/test_password_reset_signals.py` pasa: `start()`, `verify()` y `complete()` de `password_reset.py` emiten `password_reset_code_sent`, `password_reset_code_verified` y `password_reset_completed`.

- [ ] T-014 Receptores de registro
  RF: RF-007, RF-008 | Depende de: T-012, T-005 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_registration_events.py` pasa: cada señal de registro crea exactamente una fila del tipo correspondiente, con `success` y metadatos correctos.

- [ ] T-015 Receptores de restablecimiento de contraseña
  RF: RF-008, RF-010 (restablecimiento) | Depende de: T-013, T-010 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_password_reset_events.py` pasa: las señales de restablecimiento crean filas `CODE_SENT`, `CODE_VERIFIED` y `PASSWORD_RESET`, y un código rechazado crea `CODE_VERIFIED` con `success=False`.

- [ ] T-016 Receptores de perfil y deshabilitación
  RF: RF-010 (parcial, residual aceptado) | Depende de: T-011 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_profile_events.py` pasa: enviar `profile_edited` crea una fila `PROFILE_EDIT` y enviar `account_disabled` crea una fila `ACCOUNT_DISABLE`. La prueba envía la señal a mano porque ningún flujo la emite todavía.

- [ ] T-017 Permiso de consulta
  RF: RF-013 | Depende de: T-002 | Archivos: 3
  Excepción: `makemigrations` genera `migrations/0002` y la migración es parte del cambio del permiso.
  Hecho cuando: `pytest backend/apps/audit/tests/test_permission.py` pasa: existe el permiso `view_securityevent` y `makemigrations --check` no detecta cambios.

- [ ] T-018 Admin de solo lectura
  RF: RF-012, RF-013 | Depende de: T-017 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_admin.py` pasa: con el permiso se listan las filas con los filtros de RF-013; sin el permiso se deniega el acceso; añadir, cambiar y borrar están desactivados.

- [x] T-019 Comando de purga
  RF: RF-014, RF-012 | Depende de: T-003 | Archivos: 3
  Excepción: `management/__init__.py` y `management/commands/__init__.py` son paquetes que Django exige; no son lógica.
  Hecho cuando: `pytest backend/apps/audit/tests/test_purge.py` pasa: `manage.py purge_security_events --dry-run` informa del número sin borrar nada; sin `--dry-run` borra solo filas de más de un año y deja las recientes intactas.
  Decisiones: "un año" se implementa como 365 días fijos (`timedelta(days=365)`), no como calendario (366 en años bisiestos). Confianza: [Suposición]. Cómo revertirla: usar `dateutil.relativedelta(years=1)` o equivalente y ajustar el test de la frontera.

- [ ] T-020 Confianza en el proxy de entrada
  RF: RF-015 | Depende de: — | Archivos: 3
  Hecho cuando: `pytest backend/apps/core/tests/test_real_ip.py` pasa: un `X-Forwarded-For` desde una conexión no confiable se ignora; desde `TRUSTED_PROXY_IPS` se usa la última entrada. El test existente que asumía confianza en cualquier cabecera se actualiza. Este cambio afecta a toda la aplicación, no solo a la auditoría.

- [ ] T-021 Prueba de aceptación de la feature
  RF: RF-001, RF-003, RF-004, RF-015 | Depende de: T-006, T-007, T-020 | Archivos: 1
  Hecho cuando: `pytest backend/apps/audit/tests/test_acceptance.py` pasa: un login correcto y otro fallido enviados por HTTP desde el proxy de confianza generan dos filas con la IP real del cliente.

## RF sin tarea
Ninguno. Todos los RF de la spec (RF-001 a RF-016) aparecen en al menos una tarea. RF-010 aparece como cubierto en su parte aceptada (el residual de perfil y deshabilitación queda en T-016, con emisión pendiente de otra feature).

## Historial
- 2026-10-13 — Borrador inicial de tareas — RF: RF-001 a RF-016 — Estado: borrador
- 2026-10-13 — Aprobación de las tareas (T-001 a T-021) por el usuario; sin implementar — RF: RF-001 a RF-016 — Estado: aprobado
