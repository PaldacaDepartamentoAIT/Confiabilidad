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

- [x] T-016 Receptores de perfil y deshabilitación
  RF: RF-010 (parcial, residual aceptado) | Depende de: T-011 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_profile_events.py` pasa: enviar `profile_edited` crea una fila `PROFILE_EDIT` y enviar `account_disabled` crea una fila `ACCOUNT_DISABLE`. La prueba envía la señal a mano porque ningún flujo la emite todavía.
  Decisiones: ningún flujo emite hoy `profile_edited` ni `account_disabled`; el test las envía a mano. Es el residual de RF-010 aceptado en el plan. Confianza: [Cierto]. Cómo revertirla: no aplica.

- [x] T-017 Permiso de consulta (permiso por defecto)
  RF: RF-013 | Depende de: T-002 | Archivos: 1
  Decisiones: se usa el permiso por defecto `view_securityevent` que Django crea para `SecurityEvent`; sin `Meta.permissions` ni migración, decisión del usuario (D-06). Confianza: [Cierto] (decisión explícita).
  Hecho cuando: `pytest backend/apps/audit/tests/test_permission.py` pasa: tras migrar, existe `auth.Permission` con codename `view_securityevent` para `audit`.
  Decisiones: esta tarea no escribe código. El test pasa sin implementación porque Django crea `view_securityevent`; no prueba un comportamiento nuevo. El comportamiento que sí depende del permiso (el admin deniega sin él) se prueba en T-018. Confianza: [Cierto]. Cómo revertirla: no aplica.

- [x] T-018 Admin de solo lectura
  RF: RF-012, RF-013 | Depende de: T-017 | Archivos: 2
  Hecho cuando: `pytest backend/apps/audit/tests/test_admin.py` pasa: con el permiso se listan las filas con los filtros de RF-013; sin el permiso se deniega el acceso; añadir, cambiar y borrar están desactivados.
  Decisiones: los filtros por IP y por huella del correo se implementan como búsqueda (`search_fields`), no como filtros laterales, porque Django solo ofrece filtros laterales para valores enumerables. Confianza: [Probable]. Cómo revertirla: añadir `SimpleListFilter` personalizados para IP y huella.

- [x] T-019 Comando de purga
  RF: RF-014, RF-012 | Depende de: T-003 | Archivos: 3
  Excepción: `management/__init__.py` y `management/commands/__init__.py` son paquetes que Django exige; no son lógica.
  Hecho cuando: `pytest backend/apps/audit/tests/test_purge.py` pasa: `manage.py purge_security_events --dry-run` informa del número sin borrar nada; sin `--dry-run` borra solo filas de más de un año y deja las recientes intactas.
  Decisiones: "un año" se implementa como 365 días fijos (`timedelta(days=365)`), no como calendario (366 en años bisiestos). Confianza: [Suposición]. Cómo revertirla: usar `dateutil.relativedelta(years=1)` o equivalente y ajustar el test de la frontera.

- [x] T-020 Confianza en el proxy de entrada
  RF: RF-015 | Depende de: — | Archivos: 3
  Hecho cuando: `pytest backend/apps/core/tests/test_real_ip.py` pasa: un `X-Forwarded-For` desde una conexión no confiable se ignora; desde `TRUSTED_PROXY_IPS` se usa la última entrada. El test existente que asumía confianza en cualquier cabecera se actualiza. Este cambio afecta a toda la aplicación, no solo a la auditoría.
  Decisiones: `TRUSTED_PROXY_IPS` por defecto es lista vacía, es decir, no se confía en ningún proxy hasta configurarlo; en un despliegue detrás del proxy la IP registrada será la del proxy hasta que se fije su IP. Confianza: [Probable]. Cómo revertirla: restaurar la lectura de la última entrada sin comprobación (no recomendado).

- [x] T-021 Prueba de aceptación de la feature
  RF: RF-001, RF-003, RF-004, RF-015 | Depende de: T-006, T-007, T-020 | Archivos: 1
  Hecho cuando: `pytest backend/apps/audit/tests/test_acceptance.py` pasa: un login correcto y otro fallido enviados por HTTP desde el proxy de confianza generan dos filas con la IP real del cliente.
  Decisiones: el test de aceptación de la feature pasó al primer intento, porque cierra la cadena de piezas ya verificadas por separado. Se añadió el caso de cabecera falsa desde conexión directa para matar un mutante que sobrevivía. Confianza: [Cierto]. Cómo revertirla: no aplica.

- [x] T-022 Corrección: código caducado tras el periodo de gracia no se registra
  Tipo: corrección | Origen: validación de RF-008 | RF: RF-008 | Depende de: T-012, T-013 | Archivos: 4
  Excepción: son dos flujos con el mismo cambio, cada uno con su servicio y su test (`registration.py` y `test_registration_signals.py`; `password_reset.py` y `test_password_reset_signals.py`).
  Causa: `verify` devuelve `EXPIRED` antes de emitir la señal cuando el proceso superó el periodo de gracia; no queda fila.
  Hecho cuando: `pytest backend/apps/accounts/tests/test_registration_signals.py backend/apps/accounts/tests/test_password_reset_signals.py` pasa con un caso de código caducado tras la gracia que emite la señal con `success=False`, y la suite completa sigue en verde.

- [x] T-023 Corrección: el admin concede la vista solo con `view_securityevent`
  Tipo: corrección | Origen: validación de RF-013 | RF: RF-013 | Depende de: T-018 | Archivos: 2
  Causa: `ModelAdmin.has_view_permission` acepta el permiso de vista o el de cambio; un usuario con solo `change_securityevent` ve el listado.
  Hecho cuando: `pytest backend/apps/audit/tests/test_admin.py` pasa con un caso en el que un usuario con solo `change_securityevent` recibe 403 en el listado.

- [x] T-024 Filtros y búsqueda de RF-013 en el admin
  Tipo: implementación y test | Origen: validación de RF-013 y cambio de spec aprobado | RF: RF-013 | Depende de: T-018, T-023 | Archivos: 3
  Excepción: la plantilla del filtro de rango (D-11, `apps/audit/templates/admin/audit/filter_date_range.html`) es el tercer archivo; no tiene lógica de negocio.
  Hecho cuando: `pytest backend/apps/audit/tests/test_admin.py` pasa: los filtros laterales por tipo, resultado y rango de fechas (`desde`, `hasta`) devuelven solo los eventos del rango; la búsqueda por huella del correo es exacta y la búsqueda por IP es parcial.
  Decisiones: el `force_login` de los tests genera filas `LOGIN` por el receptor de auditoría, así que los tests de conteo usan tipos que el propio login no produce (`CODE_SENT`, `LOGOUT`). Confianza: [Cierto]. Cómo revertirla: no aplica, es el comportamiento correcto de la auditoría.

- [x] T-025 Test: ningún secreto en ningún flujo
  Tipo: test | Origen: validación de RF-011 | RF: RF-011 | Depende de: T-006, T-007, T-008, T-009, T-010, T-012, T-013, T-014, T-015, T-016 | Archivos: 1
  Hecho cuando: `pytest backend/apps/audit/tests/test_secrets_by_flow.py` pasa: para cada flujo (login ok, login fallido, bloqueo, cierre de sesión, registro, código, restablecimiento, cambio de contraseña), ni la contraseña, ni el código, ni el token de sesión, ni el correo en claro aparecen en ningún campo de las filas.
  Decisiones: el test pasó sin cambios de código porque el registro ya era seguro en los siete flujos; por eso se verificó con un mutante que guarda el correo en claro, que hace fallar los siete casos. Confianza: [Cierto]. Cómo revertirla: no aplica.

- [x] T-026 Test: lista de proxies vacía no confía en ningún proxy
  Tipo: test | Origen: cambio de RF-015 | RF: RF-015 | Depende de: T-020 | Archivos: 1
  Hecho cuando: `pytest backend/apps/core/tests/test_real_ip.py` pasa con un caso en el que `TRUSTED_PROXY_IPS` vacía no confía en ninguna cabecera y registra la IP de la conexión directa, y otro en el que una IP parecida pero distinta de una entrada de la lista no se considera de confianza.
  Decisiones: el código ya cumplía (pertenencia exacta y lista vacía por defecto); el test se verificó con un mutante de coincidencia por prefijo, que hace fallar el caso de IP parecida. Confianza: [Cierto]. Cómo revertirla: no aplica.

- [x] T-027 Corrección: rechazar la modificación por las vías de inserción
  Tipo: corrección | Origen: validación de RF-012 | RF: RF-012 | Depende de: T-003 | Archivos: 2
  Causa: `save()` sobre una instancia nueva con pk existente hace UPDATE en Django y sobrescribe la fila; `bulk_create(update_conflicts=True)` tampoco tenía guarda. Confirmado con una prueba que cambió `success` de una fila.
  Hecho cuando: `pytest backend/apps/audit/tests/test_insert_only.py` pasa con casos en los que una instancia nueva con pk existente y `bulk_create` con `update_conflicts` lanzan `InsertOnlyError` y dejan la fila intacta; la suite de auditoría sigue en verde.
  Decisiones: `save()` rechaza cualquier instancia con pk antes de guardar, así que ya no admite claves explícitas; la aplicación nunca las usa. `bulk_create` rechaza `update_conflicts`. Confianza: [Probable]. Cómo revertirla: permitir claves explícitas solo si la fila no existe, comprobándolo antes de guardar.

- [x] T-028 Corrección: retención de un año de calendario
  Tipo: corrección | Origen: validación de RF-014 | RF: RF-014 | Depende de: T-019 | Archivos: 2
  Causa: `timedelta(days=365)` no equivale a un año de calendario cuando la ventana incluye un 29 de febrero.
  Hecho cuando: `pytest backend/apps/audit/tests/test_purge.py` pasa con casos de frontera en un año bisiesto (1 de marzo de 2028 y 29 de febrero de 2028) y la suite de auditoría sigue en verde.
  Decisiones: la retención usa la biblioteca estándar, sin dependencias nuevas; si la fecha de referencia es 29 de febrero, el corte cae el 28 de febrero del año anterior. Confianza: [Cierto]. Cómo revertirla: volver a `timedelta(days=365)`, lo que la spec actual no acepta.

- [x] T-029 Cuenta inactiva con credenciales válidas registrada como fallo
  Tipo: implementación y test | Origen: cambio de RF-004 (análisis de impacto aprobado) | RF: RF-004 | Depende de: T-007 | Archivos: 3
  Causa: allauth rechaza la cuenta inactiva en `pre_login`, después de comprobar la contraseña; `authentication_failed` no se llama y no queda fila.
  Hecho cuando: `pytest backend/apps/audit/tests/test_login_failed.py backend/apps/audit/tests/test_secrets_by_flow.py` pasa: una cuenta inactiva con contraseña correcta genera una fila `LOGIN` con `success=False` y `reason=inactive_account`, tanto por el flujo de navegador como por el headless.
  Decisiones: el motivo `inactive_account` se añade a la lista cerrada de D-14; el punto de extensión es `pre_login` (D-13). Confianza: [Cierto]. Cómo revertirla: quitar el override de `pre_login`, lo que devolvería el hueco de RF-004.

- [x] T-030 Corrección: el adaptador no altera el contador de allauth
  Tipo: corrección | Origen: validación de RF-006 | RF: RF-006 | Depende de: T-008 | Archivos: 1
  Causa: ningún test comparaba el límite de allauth con y sin `AuditAccountAdapter`.
  Hecho cuando: `pytest backend/apps/audit/tests/test_lockout.py` pasa con un caso que compara el intento en el que allauth dispara el límite con el adaptador de auditoría y con el adaptador por defecto (ambos en el intento 6).
  Decisiones: la comparación se hace sobre el intento que dispara el límite, no sobre el valor interno del contador, porque allauth no expone el contador en su API pública. Confianza: [Probable]. Cómo revertirla: quitar el test; no afecta al código.

- [x] T-031 Receptores de M-03 que faltaban: password_set, password_reset y user_signed_up de allauth
  Tipo: implementación y test | Origen: desviación de M-03 detectada en la validación | RF: RF-007, RF-010 | Depende de: T-010, T-014 | Archivos: 2
  Causa: M-03 lista estas señales de allauth, pero `receivers.py` no las conectaba.
  Hecho cuando: `pytest backend/apps/audit/tests/test_allauth_signals.py` pasa: `password_set` crea `PASSWORD_CHANGE`, `password_reset` crea `PASSWORD_RESET` y `user_signed_up` crea `ACCOUNT_REGISTRATION`, cada uno con IP real.
  Decisiones: `password_set` se registra como cambio de contraseña, porque RF-002 no tiene un tipo propio. `user_signed_up` solo se emite si se usa el registro de allauth; hoy el registro es propio y emite sus señales, así que no hay duplicado. Confianza: [Probable]. Cómo revertirla: quitar los tres receptores; si se activa el registro de allauth junto al propio, habrá que deduplicar `ACCOUNT_REGISTRATION`.

- [x] T-032 Corrección: rechazar `bulk_create` con `update_conflicts` también en llamada posicional
  Tipo: corrección | Origen: validación de RF-012 | RF: RF-012 | Depende de: T-027 | Archivos: 2
  Causa: la guarda de `bulk_create` inspeccionaba solo los argumentos con nombre; Django acepta `update_conflicts` en cualquier posición y el valor posicional cambiaba la fila (confirmado con una prueba).
  Hecho cuando: `pytest backend/apps/audit/tests/test_insert_only.py` pasa con la llamada posicional lanzando `InsertOnlyError` y la fila intacta; la suite de auditoría sigue en verde.
  Decisiones: la firma de `bulk_create` se declara explícitamente con los parámetros de Django, para que la guarda vea `update_conflicts` sin importar cómo se pase. Confianza: [Cierto]. Cómo revertirla: volver a `*args, **kwargs`, lo que reabre el hueco.

- [x] T-033 Corrección: `_base_manager` y el POST del admin no saltan las guardas de solo inserción
  Tipo: corrección | Origen: validación de RF-012 | RF: RF-012 | Depende de: T-032 | Archivos: 3
  Causa: `SecurityEvent._base_manager` era un `Manager` plano sin guardas (confirmado con una prueba); el admin no tenía test de POST al cambio y al borrado.
  Hecho cuando: `pytest backend/apps/audit/tests/test_insert_only.py backend/apps/audit/tests/test_admin.py` pasa con `_base_manager` lanzando `InsertOnlyError` y la fila intacta, y con POST al cambio y al borrado devolviendo 403 con la fila intacta; `makemigrations --check` sin cambios; la suite completa sigue en verde.
  Decisiones: se fija `base_manager_name = "objects"` en `Meta`, para que el gestor base sea el mismo que el de guardas. Confianza: [Cierto]. Cómo revertirla: quitar la línea, lo que reabre el hueco.

- [x] T-034 Corrección: `save_base()` sobre una fila existente debe rechazarse
  Tipo: corrección | Origen: validación de RF-012 | RF: RF-012 | Depende de: T-033 | Archivos: 2
  Causa: `save_base()` escribe la fila sin pasar por la guarda de `save()`; confirmado con una prueba que cambió `success` de True a False.
  Hecho cuando: `pytest backend/apps/audit/tests/test_insert_only.py` pasa con `save_base()` sobre una fila existente lanzando `InsertOnlyError` y la fila intacta; la suite de auditoría sigue en verde.
  Decisiones: `save_base()` aplica la misma guarda que `save()`. Confianza: [Cierto]. Cómo revertirla: quitar el override, lo que reabre el hueco.

- [x] T-035 Corrección: la purga no puede borrar eventos de menos de un año
  Tipo: corrección | Origen: validación de RF-014 | RF: RF-014 | Depende de: T-028 | Archivos: 2
  Causa: `purge_older_than(ahora)` aceptaba cualquier corte y borró un evento de hace un día (confirmado).
  Hecho cuando: `pytest backend/apps/audit/tests/test_purge.py` pasa: el gestor ya no expone `purge_older_than`, y la purga (función interna `purge_expired`) usa siempre el corte de un año; el comando sigue purgando solo eventos de más de un año; la suite de auditoría sigue en verde.
  Decisiones: mecanismo elegido por el usuario: quitar el método público. La purga pasa a la función interna `purge_expired(now)` en `models.py`, que calcula el corte con `retention_cutoff`; el comando la usa y la lógica del corte se mueve a `models.py`. Confianza: [Cierto]. Cómo revertirla: volver a exponer un método que acepte fecha de corte, lo que reabre el hueco.

- [x] T-036 Corrección: la purga no borra eventos de menos de un año aunque se pase una fecha posterior
  Tipo: corrección | Origen: validación de RF-014 | RF: RF-014 | Depende de: T-035 | Archivos: 3
  Causa: `purge_expired(now)` recibe la fecha de referencia del llamador; con una fecha futura el corte también queda en el futuro y borra eventos recientes (confirmado: referencia ahora+800 días borró un evento de hace un día).
  Hecho cuando: `pytest backend/apps/audit/tests/test_purge.py` pasa con un caso que, con referencia posterior, conserva un evento reciente; `purge_expired` toma el reloj dentro de la función y no recibe la fecha del llamador; la suite de auditoría sigue en verde.
  Decisiones: `purge_expired()` no recibe parámetros y toma `timezone.now()` dentro de la función. Confianza: [Cierto]. Cómo revertirla: volver a aceptar `now`, lo que reabre el hueco.

- [x] T-037 Test: un cambio o restablecimiento rechazado por contraseña no válida no deja evento
  Tipo: test | Origen: aclaración de RF-010 | RF: RF-010 | Depende de: T-031 | Archivos: 2 (`apps/audit/tests/test_password_reset_events.py`, `apps/audit/tests/test_password_changed.py`)
  Causa: ningún test comprobaba que el rechazo por contraseña no válida no deja fila; la regla nueva no tenía prueba.
  Hecho cuando: `pytest backend/apps/audit/tests/test_password_reset_events.py backend/apps/audit/tests/test_password_changed.py` pasa con un intento rechazado por contraseña no válida sin filas nuevas de restablecimiento ni de fallo; un mutante que registra un fallo en el cambio lo detecta.
  Mutantes: (1) cambio: registrar un fallo desde el adaptador de allauth → detectado (1 fallo). (2) restablecimiento: registrar un fallo con la señal dentro de la transacción de `complete()` → sin efecto observable, porque la transacción revierte la fila al relanzar el error. Anotado como mutante equivalente; no detiene.
  Decisiones: el cambio se prueba con el formulario de allauth y el restablecimiento con el servicio real. Confianza: [Cierto]. Cómo revertirla: quitar los dos tests.

- [x] T-038 Test: un código caducado dentro del periodo de gracia deja una validación fallida
  Tipo: test | Origen: validación (H4) | RF: RF-008 | Depende de: T-022 | Archivos: 2 (`apps/audit/tests/test_registration_events.py`, `apps/audit/tests/test_password_reset_events.py`)
  Causa: `CODE_EXPIRED` (código caducado con el proceso aún dentro de la gracia) no tenía test propio; la rama genérica lo cubría sin ninguna aserción.
  Hecho cuando: `pytest backend/apps/audit/tests/test_registration_events.py backend/apps/audit/tests/test_password_reset_events.py` pasa con un código caducado dentro de la gracia, enviado al servicio real de registro y al de restablecimiento, que deja una fila `CODE_VERIFIED` con `success=False`; un mutante que registra éxito con `CODE_EXPIRED` lo detecta.
  Mutantes: `success` verdadero también con `CODE_EXPIRED`, en `registration.verify` y en `password_reset.verify` → ambos detectados.
  Decisiones: el test pasa sin cambiar código, porque el comportamiento ya existía; lo que prueba que sirve son los mutantes. El código se caduca un minuto (gracia de 15 minutos por defecto). Los tests van del servicio a la fila, lo que cubre también la mitad de H7 para la caducidad. Confianza: [Cierto]. Cómo revertirla: quitar los dos tests.

- [x] T-039 Corrección: el mensaje del check `audit.E001` se marca para traducción
  Tipo: corrección | Origen: validación (H5) | RF: — (convención de `AGENTS.md`; D-05) | Depende de: — | Archivos: 2 (`apps/core/checks.py`, `apps/core/tests/test_audit_fingerprints.py`)
  Causa: el mensaje «AUDIT_HASH_SECRET must not be empty.» no usa `gettext_lazy`, que `AGENTS.md` exige para los textos de error.
  Hecho cuando: `pytest backend/apps/core/tests/test_audit_fingerprints.py` pasa con el mensaje de `audit.E001` como texto perezoso de traducción y el mismo contenido; un mutante que quita `gettext_lazy` lo detecta.
  Mutantes: mensaje como `str` sin `gettext_lazy` → detectado.
  Decisiones: los stubs de Django tipan `msg` de `Error` como `str`, aunque Django acepta textos perezosos; se usa `# type: ignore[arg-type]` en esa línea, con un comentario que lo explica. Confianza: [Cierto]. Cómo revertirla: volver al texto plano, lo que incumple la convención de `AGENTS.md`.

- [x] T-040 Test: el permiso interno de purga solo se usa en el modelo y la purga de auditoría solo la llama su comando
  Tipo: test | Origen: validación (H3) y aclaración de RF-012 | RF: RF-012, RF-014 | Depende de: T-036 | Archivos: 1 (`apps/audit/tests/test_purge_access.py`)
  Causa: `_purge_allowed` se puede importar desde cualquier módulo, y nada comprobaba que solo la purga lo usa.
  Hecho cuando: `pytest backend/apps/audit/tests/test_purge_access.py` pasa: fuera de `apps/audit/models.py` y de los tests, ningún archivo del backend nombra `_purge_allowed` ni `_purge_context`, y fuera de `apps/audit/management/commands/purge_security_events.py` ningún archivo importa `purge_expired` de `apps.audit.models`; un mutante que usa `_purge_allowed` en otro módulo lo detecta.
  Mutantes: (1) `apps/audit/admin.py` importa `_purge_allowed` → detectado. (2) El escáner deja de resolver `modulo.purge_expired` → lo detectan sus tests unitarios (2 fallos).
  Decisiones: análisis estático con `ast`, con el mismo patrón que `apps/core/tests/test_fingerprint_guard.py`. Cubre imports absolutos y relativos, alias, atributos y `getattr` con el nombre literal. No cubre accesos dinámicos con nombres construidos en ejecución, que quedan como riesgo residual junto al SQL directo (RF-012). El test pasa sin cambiar código, porque hoy solo el modelo y el comando usan la purga. Confianza: [Cierto]. Cómo revertirla: quitar el archivo.

- [x] T-041 Corrección: tests de los rechazos de código sin cobertura
  Tipo: corrección | Origen: validación de RF-008 | RF: RF-008 | Depende de: T-038 | Archivos: 2 (`apps/audit/tests/test_registration_events.py`, `apps/audit/tests/test_password_reset_events.py`)
  Causa: ningún test comprueba que `LOCKED` y `ALREADY_VERIFIED` dejan `CODE_VERIFIED` con `success=False`, ni que `NOT_FOUND` y `AccountRefusal` no dejan fila. D-16 afirmaba lo contrario.
  Hecho cuando: `pytest backend/apps/audit/tests/test_registration_events.py backend/apps/audit/tests/test_password_reset_events.py` pasa con los servicios reales. `LOCKED` y `ALREADY_VERIFIED` dejan una fila con `success=False`. `NOT_FOUND` y la negativa por cuenta inactiva, correo cambiado o contraseña cambiada no dejan fila `CODE_VERIFIED`. Un mutante que no registra `LOCKED` y otro que registra en `AccountRefusal` se detectan.
  Mutantes: no registrar `LOCKED` en `registration.verify` → detectado; lo mismo en `password_reset.verify` → detectado; registrar fallo en `AccountRefusal` → detectado en los tres casos (cuenta inactiva, correo cambiado y contraseña cambiada).
  Decisiones: los tests pasan sin cambiar código, porque el comportamiento ya era el correcto; lo prueban los mutantes. `LOCKED` y `ALREADY_VERIFIED` se prueban en los dos servicios, no solo en uno. Confianza: [Cierto]. Cómo revertirla: quitar los tests.

- [x] T-042 Corrección: el fallo de inicio de sesión por límite lleva su motivo
  Tipo: corrección | Origen: validación de RF-004 y RF-005 | RF: RF-004, RF-005 | Depende de: T-030 | Archivos: 1 (`apps/audit/tests/test_lockout.py`)
  Causa: el test cuenta las filas `LOGIN` fallidas, pero no comprueba el motivo de la fila del intento rechazado por límite.
  Hecho cuando: `pytest backend/apps/audit/tests/test_lockout.py` pasa comprobando que el intento rechazado deja exactamente dos filas: `LOGIN` con `success=False` y `reason=too_many_login_attempts`, y `LOCKOUT`. Un mutante que graba `invalid_credentials` se detecta.
  Mutantes: la fila `LOGIN` del límite con `invalid_credentials` → detectado.
  Decisiones: el test toma solo las filas con `id` mayor que la última anterior al intento rechazado, para contar exactamente las que deja ese intento. Pasa sin cambiar código; lo prueba el mutante. Confianza: [Cierto]. Cómo revertirla: quitar el test.

- [x] T-043 Corrección: el backend arranca en desarrollo sin `.env` y sigue fallando en producción sin clave
  Tipo: corrección | Origen: validación (P-02) | RF: RF-011 (D-05) | Depende de: — | Archivos: 2 (`config/settings.py`, `apps/core/tests/test_audit_fingerprints.py`)
  Causa: D-05 hace fallar el arranque sin `AUDIT_HASH_SECRET`, y Docker Compose no le da valor.
  Hecho cuando: un test en un proceso aparte comprueba que `manage.py check` pasa con `DJANGO_DEBUG=1` y la clave vacía, y falla con `audit.E001` con `DJANGO_DEBUG=0` y la clave vacía. Un mutante que usa el valor de desarrollo también sin `DEBUG` se detecta.
  Mutantes: valor de desarrollo también sin `DEBUG` → detectado.
  Decisiones: una clave vacía cuenta como ausente (`env(...) or ...`), para que `AUDIT_HASH_SECRET=` en el entorno no deje sin valor el desarrollo. Los tests lanzan `manage.py check` en un proceso aparte para leer `settings.py` desde cero. Confianza: [Cierto]. Cómo revertirla: volver a `default=""`, lo que rompe P-02.

- [ ] T-044 Test: el cambio de contraseña por el flujo real deja su fila
  Tipo: test | Origen: validación (R-5) | RF: RF-010 | Depende de: T-037 | Archivos: 1 (`apps/audit/tests/test_password_changed.py`)
  Causa: el cambio correcto solo se prueba enviando la señal a mano.
  Hecho cuando: `pytest backend/apps/audit/tests/test_password_changed.py` pasa con un cambio por `/_allauth/browser/v1/account/password/change` que deja una fila `PASSWORD_CHANGE` con `success=True`, y con un rechazo por contraseña no válida que no deja fila. Un mutante que desconecta el receptor se detecta.

## RF sin tarea
Ninguno. Todos los RF de la spec (RF-001 a RF-016) aparecen en al menos una tarea. RF-010 aparece como cubierto en su parte aceptada (el residual de perfil y deshabilitación queda en T-016, con emisión pendiente de otra feature).

## Historial
- 2026-10-13 — Borrador inicial de tareas — RF: RF-001 a RF-016 — Estado: borrador
- 2026-10-13 — Aprobación de las tareas (T-001 a T-021) por el usuario; sin implementar — RF: RF-001 a RF-016 — Estado: aprobado
- 2026-10-13 — Tareas actualizadas tras el cambio de RF-013 y RF-015: T-024 reescrita (implementación y test, con Excepción de plantilla) y T-026 añadida — RF: RF-013, RF-015 — Estado: aprobado
- 2026-10-13 — Correcciones de la segunda validación: T-027 (RF-012, inserción sin modificación) y T-028 (RF-014, año de calendario) — RF: RF-012, RF-014 — Estado: impacto analizado
- 2026-10-13 — Nueva tarea T-029 tras el cambio de RF-004 (análisis de impacto aprobado) — RF: RF-004 — Estado: aprobado
- 2026-10-13 — Corrección T-030 (test de RF-006 contra el adaptador por defecto) — RF: RF-006 — Estado: aprobado
- 2026-10-13 — T-031 (receptores de M-03 que faltaban) — RF: RF-007, RF-010 — Estado: aprobado
- 2026-10-13 — Corrección T-032 (bulk_create con update_conflicts posicional) tras la validación — RF: RF-012 — Estado: aprobado
- 2026-10-13 — Corrección T-033 (gestor base sin guardas) tras la validación — RF: RF-012 — Estado: aprobado
- 2026-10-14 — Correcciones T-034 (save_base) y T-035 (purga de un año sin método público) tras la validación — RF: RF-012, RF-014 — Estado: aprobado
- 2026-10-14 — Corrección T-036 (purga sin fecha de referencia del llamador) tras la validación de RF-014 — RF: RF-014 — Estado: aprobado
- 2026-10-14 — T-037 (test de rechazo por contraseña no válida, aclaración de RF-010) — RF: RF-010 — Estado: aprobado
- 2026-10-14 — T-038 (caducidad dentro de la gracia), T-039 (traducción de `audit.E001`) y T-040 (uso del permiso de purga) tras la validación y la aclaración de RF-008 y RF-012 — RF: RF-008, RF-012, RF-014 — Estado: aprobado
- 2026-10-14 — T-041 (rechazos de código), T-042 (motivo del fallo por límite), T-043 (arranque en desarrollo, P-02) y T-044 (cambio de contraseña por el flujo real) tras la tercera validación — RF: RF-004, RF-005, RF-008, RF-010, RF-011 — Estado: aprobado
