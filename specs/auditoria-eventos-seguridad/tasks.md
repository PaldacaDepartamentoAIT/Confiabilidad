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

- [x] T-004 Huellas de auditoría en el punto único (M-09)
  RF: RF-011 | Depende de: T-001, huellas-hmac-unificadas en `main` | Archivos: 3
  Excepción: el check de arranque necesita `apps/core/checks.py` y un `ready()` en `apps/core/apps.py` para registrarse; y `backend/.env.example` recibe la variable nueva. Son archivos de configuración sin lógica de huellas, confirmados por el usuario.
  Hecho cuando: `pytest backend/apps/core/tests/test_audit_fingerprints.py` pasa con vectores fijos del correo normalizado y de la clave de sesión; sin `AUDIT_HASH_SECRET` la configuración lanza `ImproperlyConfigured`; el guardián de huellas sigue en verde.
  Decisiones: `AUDIT_HASH_SECRET` falla al arrancar mediante un check de Django (`manage.py check`, `runserver`) además de al usar la clave, decisión del usuario (D-05). El check necesita un archivo más: se declara aquí como Excepción al implementar T-004. Confianza: [Cierto] (decisión explícita).
  Decisiones: las huellas de auditoría separan finalidades con un prefijo (`audit_email:` y `audit_session:`) además de la clave propia, para que un correo y una clave de sesión con el mismo texto no produzcan la misma huella. Confianza: [Probable]. Cómo revertirla: quitar el prefijo y aceptar la colisión teórica entre correo y clave de sesión.

- [x] T-005 Registrador `record_event`
  RF: RF-001, RF-011 | Depende de: T-002, T-004 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_recorder.py` pasa: la IP sale de `REMOTE_ADDR`, el correo se guarda solo como huella normalizada, no aparece ningún valor en claro y los metadatos se guardan.

- [x] T-006 Receptor de inicio de sesión exitoso
  RF: RF-003 | Depende de: T-005 | Archivos: 3
  Hecho cuando: `pytest backend/apps/audit/tests/test_login_success.py` pasa: un login correcto crea una fila `LOGIN` con `success=True` cuyo `session_key` es la huella de la clave de la sesión ya rotada.
  Decisiones: el receptor escucha `django.contrib.auth.signals.user_logged_in`, no la de allauth, porque Django la emite en cualquier login (también el del panel de administración) y allauth la usa a través de `login()`. Confianza: [Probable]. Cómo revertirla: conectar la señal de allauth y aceptar que el admin no quede auditado.
  Nota: el middleware con `ContextVar` (decisión de T-011) no se necesita aquí; se implementa en T-014, que es donde los receptores de señales propias de accounts lo necesitan.

- [x] T-007 Adaptador y registro de fallo de inicio de sesión
  RF: RF-004 | Depende de: T-005 | Archivos: 3
  Hecho cuando: `pytest backend/apps/audit/tests/test_login_failed.py` pasa: una contraseña incorrecta crea una fila `LOGIN` con `success=False` y el motivo en metadatos; un correo inexistente crea la fila sin clave de sesión; la prueba también confirma que el flujo headless llama al mismo adaptador (D-03).
  Decisiones: los rechazos por límite no llegan a `authentication_failed` (allauth los lanza en `pre_authenticate` con `too_many_login_attempts`, `allauth/account/adapter.py`, línea 800). Por eso T-008 sobrescribe también `pre_authenticate`. El adaptador lleva `# type: ignore[misc]` porque allauth no publica tipos. Confianza: [Cierto]. Cómo revertirla: no aplica; es la forma de heredar de una clase sin tipos bajo mypy estricto. Los tests vacían la caché de límites en cada test para no arrastrar intentos entre pruebas.

- [x] T-008 Bloqueo por límite de intentos
  RF: RF-005, RF-006 | Depende de: T-007 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_lockout.py` pasa: superar el límite crea dos filas para el mismo intento (`LOGIN` fallido y `LOCKOUT`); el contador de límite de allauth tiene el mismo valor con y sin el adaptador de auditoría. Antes de escribir el test hay que confirmar en `allauth` cómo señala el límite, porque no hay señal para ello.
  Decisiones: el registro de bloqueo se hace en `pre_authenticate`, junto a la fila de fallo, porque allauth rechaza antes de autenticar (ver T-007). RF-006 se verifica comprobando que el sexto intento es el que dispara el límite de allauth, sin que el adaptador consuma ni reinicie el contador. Confianza: [Probable]. Cómo revertirla: quitar el registro de `pre_authenticate` y dejar solo el de `authentication_failed`, lo que perdería los bloqueos.

- [x] T-009 Cierre de sesión
  RF: RF-009 | Depende de: T-006 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_logout.py` pasa: un cierre de sesión crea una fila `LOGOUT` con la huella de la sesión que se cierra, capturada antes de vaciarla.
  Decisiones: se usa `user_logged_out` de Django, que se emite antes de vaciar la sesión, así que la clave aún existe. Confianza: [Cierto] (comportamiento de Django). Cómo revertirla: no aplica.

- [x] T-010 Cambio de contraseña
  RF: RF-010 (cambio) | Depende de: T-006 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_password_changed.py` pasa: la señal `password_changed` de allauth crea una fila `PASSWORD_CHANGE` con `success=True`.
  Decisiones: el test dispara la señal `password_changed` de allauth directamente, no a través de un formulario, porque el flujo HTTP de cambio exige sesión y contraseña previa; el receptor es el mismo. Además, el helper `_session_key` tolera peticiones sin sesión. Confianza: [Probable]. Cómo revertirla: añadir un test de integración con el endpoint de cambio de contraseña.

- [x] T-011 Señales propias de accounts
  RF: RF-007, RF-008, RF-010 (contrato) | Depende de: — | Archivos: 2
  Hecho cuando: `pytest backend/apps/accounts/tests/test_signals.py` pasa: existen las nueve señales de M-08 con argumentos documentados (solicitud de registro, código enviado y validado en registro, cuenta creada, código enviado y validado en restablecimiento, restablecimiento completado, perfil editado, cuenta deshabilitada).
  Decisiones: las señales no llevan la petición HTTP. La petición llega a los receptores por un middleware de `apps/audit` que guarda la petición actual en un `ContextVar`; las firmas de los servicios no cambian, decisión del usuario. El middleware se implementa en T-014 (antes de sus receptores) y se registra en `MIDDLEWARE` como Excepción de esa tarea. Confianza: [Cierto] (decisión explícita).
  Decisiones: las nueve señales se definen como `Signal()` sin argumentos declarados en Django; los argumentos `email` y `success` se documentan en el módulo. Confianza: [Probable]. Cómo revertirla: añadir `providing_args` no existe en Django 5; bastaría con un tipo que valide los argumentos al enviar.

- [x] T-012 Emisión de las señales desde el registro
  RF: RF-007, RF-008 | Depende de: T-011 | Archivos: 2
  Hecho cuando: `pytest backend/apps/accounts/tests/test_registration_signals.py` pasa: `start()`, `resend()`, `verify()` y `complete()` de `registration.py` emiten sus señales con el resultado correcto.
  Decisiones: la regresión de 33 logins en accounts vino de los receptores de login con `AUDIT_HASH_SECRET` vacía en tests; se corrigió con `backend/conftest.py`, un fixture autouse que fija una clave de prueba, no con cambios de producción. Tras la corrección, `apps/accounts` pasa entero (358). Confianza: [Cierto]. Cómo revertirla: quitar el fixture y definir la variable en el entorno de CI.

- [x] T-013 Emisión de las señales desde el restablecimiento de contraseña
  RF: RF-008, RF-010 (restablecimiento) | Depende de: T-011 | Archivos: 2
  Hecho cuando: `pytest backend/apps/accounts/tests/test_password_reset_signals.py` pasa: `start()`, `verify()` y `complete()` de `password_reset.py` emiten `password_reset_code_sent`, `password_reset_code_verified` y `password_reset_completed`.
  Decisiones: no se emite `password_reset_code_sent` cuando `start()` devuelve `NoEligibleAccount`, porque no se envía ningún código; así evita registrar peticiones para correos inexistentes como si hubieran sido enviadas. Confianza: [Probable]. Cómo revertirla: emitir también en `NoEligibleAccount` con `success=False`, lo que cambiaría el conteo de filas de esos casos.

- [x] T-014 Receptores de registro
  RF: RF-007, RF-008 | Depende de: T-012, T-005 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_registration_events.py` pasa: cada señal de registro crea exactamente una fila del tipo correspondiente, con `success` y metadatos correctos.
  Excepción (aprobada por el usuario al elegir el middleware): además de los dos archivos de la tarea, se crea `apps/audit/middleware.py` y se registra `apps.audit.middleware.CurrentRequestMiddleware` en `MIDDLEWARE`; el middleware guarda la petición en un `ContextVar` que leen los receptores. Es el middleware que decidió el usuario para las señales sin petición, y se implementa aquí porque es donde lo necesitan los receptores de registro. Confianza: [Cierto]. Cómo revertirla: pasar `request` a cada servicio, decisión descartada.

- [x] T-015 Receptores de restablecimiento de contraseña
  RF: RF-008, RF-010 (restablecimiento) | Depende de: T-013, T-010 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_password_reset_events.py` pasa: las señales de restablecimiento crean filas `CODE_SENT`, `CODE_VERIFIED` y `PASSWORD_RESET`, y un código rechazado crea `CODE_VERIFIED` con `success=False`.
  Decisiones: `password_reset_completed` se registra como `PASSWORD_RESET` (restablecimiento), no como `PASSWORD_CHANGE`, que es el cambio con contraseña conocida de T-010. Confianza: [Cierto] (distinción de RF-002). Cómo revertirla: cambiar el mapeo en `receivers.py`.

- [ ] T-016 Receptores de perfil y deshabilitación
  RF: RF-010 (parcial, residual aceptado) | Depende de: T-011 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_profile_events.py` pasa: enviar `profile_edited` crea una fila `PROFILE_EDIT` y enviar `account_disabled` crea una fila `ACCOUNT_DISABLE`. La prueba envía la señal a mano porque ningún flujo la emite todavía.

- [ ] T-017 Permiso de consulta (permiso por defecto)
  RF: RF-013 | Depende de: T-002 | Archivos: 1
  Decisiones: se usa el permiso por defecto `view_securityevent` que Django crea para `SecurityEvent`; sin `Meta.permissions` ni migración, decisión del usuario (D-06). Confianza: [Cierto] (decisión explícita).
  Hecho cuando: `pytest backend/apps/audit/tests/test_permission.py` pasa: tras migrar, existe `auth.Permission` con codename `view_securityevent` para `audit`.

- [ ] T-018 Admin de solo lectura
  RF: RF-012, RF-013 | Depende de: T-017 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_admin.py` pasa: con el permiso se listan las filas con los filtros de RF-013; sin el permiso se deniega el acceso; añadir, cambiar y borrar están desactivados.

- [x] T-019 Comando de purga
  RF: RF-014, RF-012 | Depende de: T-003 | Archivos: 3
  Excepción: `management/__init__.py` y `management/commands/__init__.py` son paquetes que Django exige; no son lógica.
  Hecho cuando: `pytest backend/apps/audit/tests/test_purge.py` pasa: `manage.py purge_security_events --dry-run` informa del número sin borrar nada; sin `--dry-run` borra solo filas de más de un año y deja las recientes intactas.
  Decisiones: "un año" se implementa como 365 días fijos (`timedelta(days=365)`), no como calendario (366 en años bisiestos). Confianza: [Suposición]. Cómo revertirla: usar `dateutil.relativedelta(years=1)` o equivalente y ajustar el test de la frontera.

- [x] T-020 Confianza en el proxy de entrada
  RF: RF-015 | Depende de: — | Archivos: 3
  Hecho cuando: `pytest backend/apps/core/tests/test_real_ip.py` pasa: un `X-Forwarded-For` desde una conexión no confiable se ignora; desde `TRUSTED_PROXY_IPS` se usa la última entrada. El test existente que asumía confianza en cualquier cabecera se actualiza. Este cambio afecta a toda la aplicación, no solo a la auditoría.
  Decisiones: `TRUSTED_PROXY_IPS` por defecto es lista vacía, es decir, no se confía en ningún proxy hasta configurarlo; en un despliegue detrás del proxy la IP registrada será la del proxy hasta que se fije su IP. Confianza: [Probable]. Cómo revertirla: restaurar la lectura de la última entrada sin comprobación (no recomendado).

- [ ] T-021 Prueba de aceptación de la feature
  RF: RF-001, RF-003, RF-004, RF-015 | Depende de: T-006, T-007, T-020 | Archivos: 1
  Hecho cuando: `pytest backend/apps/audit/tests/test_acceptance.py` pasa: un login correcto y otro fallido enviados por HTTP desde el proxy de confianza generan dos filas con la IP real del cliente.

## RF sin tarea
Ninguno. Todos los RF de la spec (RF-001 a RF-016) aparecen en al menos una tarea. RF-010 aparece como cubierto en su parte aceptada (el residual de perfil y deshabilitación queda en T-016, con emisión pendiente de otra feature).

## Historial
- 2026-10-13 — Borrador inicial de tareas — RF: RF-001 a RF-016 — Estado: borrador
- 2026-10-13 — Aprobación de las tareas (T-001 a T-021) por el usuario; sin implementar — RF: RF-001 a RF-016 — Estado: aprobado
