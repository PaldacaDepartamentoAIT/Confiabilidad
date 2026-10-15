# Plan: cambio-contrasena
Estado: aprobado

## Módulos
### M-01 Base común de los procesos con código (`apps/accounts/models.py`)
Responsabilidad: modelo abstracto `CodeProcess` con los campos y el cálculo que hoy tiene
`PendingRegistration` (`public_id`, `code_hash`, `code_expires_at`, `failed_attempts`,
`code_validated_at`, `created_at`; `expires_at`, `is_expired`, `is_locked`) y su queryset con
`expired()`. `PendingRegistration` pasa a heredarlo sin cambiar su tabla (D-02).
RF: RF-005, RF-006, RF-012

### M-02 Modelo `PasswordResetRequest` (`apps/accounts/models.py`)
Responsabilidad: la solicitud de cambio de contraseña: hereda `CodeProcess`, apunta a la cuenta
con una relación uno a uno que se borra con ella y guarda la huella de la cuenta (D-04).
RF: RF-001, RF-010

### M-03 Huellas con dominio (`apps/accounts/codes.py`)
Responsabilidad: la huella del código pasa a incluir el tipo de proceso (D-01) y se añade la huella
de la cuenta (correo + hash de la contraseña) para detectar cambios tras la solicitud (D-04). Ambas
se comprueban con el secreto vigente y, durante la transición, con el anterior (RF-015 de
`procesos-pendientes`).
RF: RF-005, RF-014, RF-015

### M-04 Operaciones comunes del código (`apps/accounts/processes.py`, nuevo)
Responsabilidad: emitir un código para un proceso, comprobar un código presentado (ya validado,
bloqueado, código caducado, erróneo con suma de intento, validado) y reemitirlo en un reenvío, sobre
cualquier `CodeProcess` ya bloqueado. `registration.py` pasa a usarlas en vez de su propia copia
(D-03). `VerifyResult` se mueve aquí y `registration` lo sigue exponiendo con el mismo nombre.
RF: RF-005, RF-007

### M-05 Servicio de cambio de contraseña (`apps/accounts/password_reset.py`, nuevo)
Responsabilidad: `start`, `verify`, `resend`, `complete` y `purge_expired`, cada una en una
transacción. Es la puerta que usan el comando ahora y la API después. Desde el cambio del
2026-10-14, `start` y `resend` hacen en la respuesta solo el trabajo que no depende de la cuenta
(D-13); `verify`, `resend` y `complete` buscan siempre en las solicitudes y en las plazas de cambio
de contraseña, y responden "caducada" cuando la cuenta está inactiva, se borró o cambió su correo o
su contraseña (D-14, D-15). `complete` deja además el aviso de contraseña restablecida en la bandeja
(D-16).
RF: RF-002, RF-003, RF-004, RF-006, RF-007, RF-008, RF-009, RF-011, RF-014, RF-015, RF-016, RF-017

### M-06 Comando `manage.py password_reset` (`management/commands/password_reset.py`) y utilidades de consola (`management/console.py`, nuevo)
Responsabilidad: subcomandos `start`, `verify`, `resend`, `complete` y `purge`, que solo llaman a
M-05. Desde el 2026-10-14 muestran el `public_id` y el resultado, nunca el código ni si hay cuenta
elegible; `start` admite `--language`; desaparecen los mensajes propios de cuenta inactiva o
cambiada (RF-013). Las utilidades que hoy están en el comando `registration` (mostrar `public_id` y código,
formatear errores de validación, pedir la contraseña sin eco) pasan a `console.py` y las usan los
dos comandos (D-09).
RF: RF-011, RF-013

### M-07 Migración `0006_passwordresetrequest`
Responsabilidad: crear la tabla con `public_id` único y la cuenta única (uno a uno) con borrado en
cascada. La herencia de M-01 no debe generar migración para `PendingRegistration`.
RF: RF-001, RF-010 (CF-1)

### M-08 Configuración y documentación operativa (`.env.example`, `HUMAN_TODO.md`)
Responsabilidad: indicar en `.env.example` que los límites `REGISTRATION_*` y el secreto de los
códigos valen también para el cambio de contraseña (D-10); añadir a `HUMAN_TODO.md` el límite de
frecuencia y la neutralización de RF-004 como requisitos previos a la API (CF-5), y ampliar la
entrada de `REGISTRATION_CODE_SECRET`, que ahora protege también los códigos de cambio de contraseña.
RF: RF-012 (CF-5)

### M-09 Trabajo fuera de la respuesta (`password_reset.py` y `tasks.py`)
Responsabilidad: `resolve_password_reset(public_id)` convierte una plaza en solicitud si el correo
tiene una cuenta activa (D-13), con su tarea de Celery y sus reintentos; el barrido y `reissue_code`
de `procesos-pendientes` (D-15 y D-13 de esa feature) atienden también al propósito
`password_reset`.
RF: RF-002, RF-003, RF-004, RF-005, RF-007, RF-016, RF-017

### M-10 Respuesta "caducada" tras borrar la cuenta (`models.py`, migración `0009`)
Responsabilidad: campo `answers_expired` en `PhantomProcess` y un receptor `pre_delete` de `User`
que, antes de borrar la cuenta, deja en su lugar una plaza con el `public_id` y las fechas de su
solicitud que responde "caducada" (D-15).
RF: RF-010

### M-11 Migración `0010_passwordresetrequest_language`
Responsabilidad: añadir a `PasswordResetRequest` el idioma de la petición (D-17).
RF: RF-007

## Modelo de datos
`accounts.CodeProcess` (abstracto, sin tabla), con los campos actuales de `PendingRegistration`:
- `public_id` CharField(64), único en la tabla de cada proceso.
- `code_hash` CharField(64): HMAC-SHA256 en hexadecimal (D-01).
- `code_expires_at` DateTimeField.
- `failed_attempts` PositiveSmallIntegerField, por defecto 0.
- `code_validated_at` DateTimeField, nulo mientras no se valide.
- `created_at` DateTimeField al crear (en el reemplazo se reasigna a "ahora", RF-003). Desde el
  2026-10-15, "ahora" es el momento de la resolución, también para la plaza sin solicitud (D-13).

`accounts.PasswordResetRequest(CodeProcess)`:
- `user` OneToOneField(`User`, `on_delete=CASCADE`, `related_name="password_reset_request"`):
  una solicitud por cuenta garantizada por la base de datos, también en `bulk_create` y SQL directo
  (RF-001, CF-1), y borrado con la cuenta (RF-010).
- `account_stamp` CharField(64): HMAC-SHA256 del correo en minúsculas y del hash de la contraseña
  de la cuenta en el momento de pedir o reemplazar la solicitud (D-04).
- `language` CharField(5) con los tres idiomas (cambio del 2026-10-15): idioma de la petición que
  creó o reemplazó la solicitud, tomado del `payload` de la plaza; lo usa el correo del reenvío
  (D-17).

`accounts.PhantomProcess` (de `procesos-pendientes`, M-08 de esa feature) se usa con
`purpose = "password_reset"`: `email` es el correo pedido, haya o no cuenta, y `payload` guarda el
idioma de la petición. Desde este cambio tiene además `answers_expired` (booleano, falso por
defecto): la plaza que deja una cuenta borrada responde "caducada" hasta su caducidad natural (M-10).

Sin `used_at` ni historial: la fila se borra al completar o al purgarse (S-02 de la spec). La
caducidad se calcula como en el registro: mín(`code_expires_at` + gracia, `created_at` + vida
máxima).

## Decisiones
### D-01 Separación de dominio en la huella del código
Elegida: el mensaje del HMAC pasa a ser `<tipo>:<public_id>:<código>`, con el tipo
`registration` o `password_reset`, también para el registro.
Descartada: mantener `<public_id>:<código>` y confiar en que los dos tipos viven en tablas distintas
con `public_id` aleatorios de 256 bits.
Motivo: hoy no hay un ataque práctico que lo exija [Probable]: los `public_id` los genera el servidor
y una colisión entre tablas es despreciable. Pero la garantía de que una huella de un tipo nunca
valida en el otro dejaría de depender de dos hechos externos (tablas separadas, identificadores no
elegibles por el cliente) y pasaría a estar en la propia huella. Una API futura que aceptara
identificadores o una tabla común no la rompería. Cuesta un parámetro. *Efecto:* los registros
pendientes en curso al desplegar no aceptan su código; basta con reenviarlo. No hay flujo de
registro en producción, así que hoy el coste es nulo. Descartado también un secreto por tipo: añade
variables y rotaciones sin ganar nada frente al prefijo.

### D-02 Base abstracta en lugar de copiar campos
Elegida: `CodeProcess` abstracto, del que heredan `PendingRegistration` y `PasswordResetRequest`.
Descartada: duplicar campos y propiedades en el modelo nuevo.
Motivo: la caducidad, el bloqueo y los campos deben ser idénticos (RF-005, RF-006, RF-012); una copia
divergiría. La herencia abstracta no cambia la tabla de `PendingRegistration`; una tarea comprueba
con `makemigrations --check` que no aparece migración para ella.

### D-03 Operaciones comunes del código en un módulo propio
Elegida: `processes.py` con `issue_code`, `check_code` y `renew_code` sobre un `CodeProcess` ya
bloqueado. Cada servicio hace antes sus comprobaciones propias (existencia, caducidad, estado de la
cuenta) y delega en ellas. `registration.verify` y `registration.resend` se reescriben sobre estas
funciones sin cambiar su comportamiento; sus tests actuales son la red de seguridad.
Descartada: copiar `verify` y `resend` en `password_reset.py`.
Motivo: el usuario pidió reutilizar en vez de copiar; las reglas RF-008…RF-010 y RF-016 de
`procesos-pendientes` deben ser las mismas en los dos procesos.

### D-04 Huella de la cuenta para detectar cambios de correo y de contraseña
Elegida: `account_stamp` = HMAC(secreto, `password_reset_account:<correo en minúsculas>:<hash de
la contraseña>`), calculada al pedir o reemplazar la solicitud y recalculada en `verify`, `resend`
y `complete`; si no coincide (con el secreto vigente ni, durante la transición, con el anterior),
se rechaza con `ACCOUNT_CHANGED` sin tocar la fila (RF-014, RF-015).
Descartadas: (a) guardar el correo y una copia del hash de la contraseña en la solicitud: duplica un
dato personal y el hash de la contraseña en otra tabla; (b) añadir a `User` una fecha de último
cambio de contraseña: toca el modelo de cuenta y obliga a mantenerla en cada vía que cambie la
contraseña (panel, consola, allauth).
Motivo: una sola columna cubre los dos RF sin guardar el correo ni el hash, como hace el generador
de tokens de restablecimiento de Django. *Limitación conocida:* Django recalcula el hash de la
contraseña al iniciar sesión si cambian los parámetros del algoritmo (por ejemplo, al actualizar
Django). Eso invalida una solicitud en curso aunque la contraseña no haya cambiado; el coste es
pedir otra. Un secreto rotado sin periodo de transición también las invalida, como a los códigos.
*Cambio del 2026-10-15 (2.ª validación):* esas dos invalidaciones distinguen una solicitud real de
una plaza (RF-017). Se aceptan como riesgo residual (S-14) en vez de firmar la huella con una clave
que no rote: esa clave sería un secreto más y el recálculo del hash seguiría distinguiendo.

### D-05 Orden de bloqueo y concurrencia
*Cambio del 2026-10-14:* el bloqueo de `start` se aplica ahora en `resolve_password_reset`, fuera de
la respuesta. *Cambio del 2026-10-15 (validación):* todas las operaciones bloquean primero la plaza,
como D-18 de `procesos-pendientes`.
Elegida:
- La resolución bloquea la plaza, después la fila de la cuenta (`select_for_update` sobre `User`) y
  después la solicitud; así dos peticiones para la misma cuenta se ordenan y la más reciente
  reemplaza a la anterior (RF-003). El alta va en un punto de guardado: si choca con la unicidad por
  una escritura ajena al servicio, el `IntegrityError` se traduce en reemplazar la fila existente,
  nunca sale al llamante (lección de `procesos-pendientes`).
- `verify`, `resend` y `reissue_code` bloquean primero la plaza por su `public_id` y después la
  solicitud (no escriben en la cuenta).
- `complete` bloquea primero la plaza, después lee la solicitud sin bloqueo para conocer la cuenta,
  bloquea la cuenta y después la solicitud, y comprueba que sigue siendo la misma solicitud: el
  mismo orden que la resolución (plaza → cuenta → solicitud), sin interbloqueos.
Descartada: bloquear solo la solicitud en todas las operaciones, y consultar la solicitud antes que
la plaza.
Motivo: `complete` escribe en la cuenta y en `EmailAddress`; con órdenes distintos en la resolución
y en `complete`, Postgres abortaría una de las dos por interbloqueo. Consultar la solicitud antes que
la plaza daba "desconocida", solo con cuenta, si la resolución estaba en curso (RF-017). *Riesgo
residual heredado:* hasta este cambio, ningún test ejercía dos transacciones reales a la vez; desde
ahora lo hace el test de equivalencia simultánea.

### D-06 Resultados del servicio
*Cambio del 2026-10-14:* `Started` ya solo lleva el `public_id`, `NoEligibleAccount` desaparece
(RF-004) y `AccountRefusal` también: sus casos responden como una solicitud caducada (D-14).
Elegida: resultados tipados, como en el registro (D-10 de `procesos-pendientes`): `Started`,
`NoEligibleAccount` (RF-004, único para "sin cuenta" y "cuenta inactiva"), `VerifyResult` común más
un `AccountRefusal` propio (`INACTIVE`, `ACCOUNT_CHANGED`) para RF-008, RF-014 y RF-015, `Resent`,
`Completed` y las negativas de `complete`. La contraseña inválida sale como `ValidationError` con
cada regla, igual que en `registration.complete`.
Descartada: excepciones para los casos de negocio.
Motivo: la API futura debe convertir `NoEligibleAccount` en la misma respuesta que `Started`
(S-01); con un resultado tipado es una rama explícita, no un `except` que se puede olvidar.

### D-07 Completar
*Cambio del 2026-10-14:* en la misma transacción se deja en la bandeja el aviso de contraseña
restablecida (D-16).
Elegida: en una transacción, `validate_password(password, user=cuenta)` (la política de RF-022 con
el correo y el nombre reales de la cuenta), `set_password` + `save(update_fields=["password"])`
(no genera versión de historial: `password` está excluida), marcar como verificada la
`EmailAddress` de la cuenta con su correo, o crearla verificada y principal si la cuenta no tiene
otra principal, y borrar la solicitud. El contador de inicios fallidos se borra con
`transaction.on_commit`, para que no se borre si la transacción falla.
Descartada: el flujo de cambio de contraseña de allauth (`flows.password_reset`).
Motivo: exige una petición HTTP y envía correo y mensajes, cosas del flujo (S-01); como en D-04 de
`procesos-pendientes`, se usan los gestores de los modelos públicos de allauth.

### D-08 Contador de inicios de sesión fallidos de allauth
Elegida: calcular la clave con `adapter._get_login_attempts_cache_key(None, email=...)` (con
`django.contrib.sites` y `SITE_ID`, no necesita la petición) y borrar en la caché solo las tasas
"por clave" de la acción `login_failed`, con las funciones de `allauth.core.internal.ratelimit`.
La tasa por IP no se toca (RF-009, S-12).
Descartadas: (a) `adapter._delete_login_attempts_cached_email`, que también recorre la tasa por IP y
necesita una petición con IP, inexistente en consola; (b) reconstruir a mano el formato de la clave.
Motivo: (b) se rompería en silencio si allauth cambia el formato; usar sus funciones falla de forma
visible al actualizar. *Riesgo:* son funciones internas de allauth; un test de extremo a extremo (5
fallos, completar, el inicio de sesión vuelve a funcionar) detecta cualquier rotura al actualizar.

### D-09 Comando y utilidades de consola compartidas
Elegida: `manage.py password_reset <start|verify|resend|complete|purge>`, con los mismos nombres de
subcomando que `registration` (`start --email`, `complete [--password]`, que sin `--password` la pide
sin eco). Las utilidades comunes pasan a `apps/accounts/management/console.py`, fuera de
`commands/` para que Django no lo trate como comando.
Descartadas: importar las funciones privadas del comando `registration` desde el nuevo, o copiarlas.
Motivo: reutilizar sin acoplar un comando a otro. *Cambio del 2026-10-14:* sin cuenta elegible, el
comando muestra lo mismo que con cuenta; ya no hay mensaje propio (RF-013, S-06).

### D-10 Nombres de los límites y del secreto
Elegida: se mantienen los nombres `REGISTRATION_*` y `conf.py` sin cambios; `.env.example` y el
resumen indican que valen para los dos procesos (RF-012).
Descartada: renombrarlos (por ejemplo, `CODE_*`) con compatibilidad hacia atrás.
Motivo: renombrar obliga a migrar variables en producción y en `HUMAN_TODO.md` sin cambiar ningún
comportamiento. Si se separan los límites (S-10), se hará con `sdd-cambio`.

### D-11 Tiempo en los tests
Elegida: como D-07 de `procesos-pendientes`: mover `created_at` y `code_expires_at` con `update()`.
Descartada: `freezegun`.
Motivo: no añade dependencias.

### D-12 Sesiones abiertas (S-03)
Elegida: un test de integración inicia sesión por navegador (cookie) y por app (`X-Session-Token`),
completa el cambio con el servicio y comprueba que ambas reciben 401 (CF-3). No se borra ninguna
sesión.
Descartada: borrar aquí las sesiones de la cuenta.
Motivo: S-03 lo deja para el flujo; el test fija que, mientras tanto, las sesiones quedan
inservibles, y avisará si una actualización de Django o allauth lo cambia.

### D-13 Plaza en la respuesta, como en el registro
*Cambio del 2026-10-15 (validación):* la resolución aplica D-17 de `procesos-pendientes`, y la plaza
sin solicitud queda como una solicitud recién emitida.
Elegida: `start` valida el formato del correo, crea una `PhantomProcess` de propósito
`password_reset` con un `public_id` nuevo y el idioma en `payload`, y encola
`resolve_password_reset`. La resolución, con la plaza bloqueada, aplica D-17 de
`procesos-pendientes`: si hay una plaza posterior sin resolver del mismo correo, se borra sin hacer
nada; si no, borra las anteriores. Si hay una cuenta activa con ese correo, crea o reemplaza su
solicitud con el `public_id` de la plaza y el idioma de la petición (RF-002, RF-003, D-17), borra la
plaza y encola el correo con el código en ese idioma. Si no, la plaza queda como identificador sin
solicitud, en el mismo estado que una solicitud recién emitida: intentos a 0, sin validar, código
vigente desde la resolución y alta en la resolución, porque el reemplazo de una solicitud real
también cuenta su vida de nuevo (RF-003, RF-004, RF-017). Reintentos (con la ventana comprobada en
cada ejecución), barrido y reenvío en dos tiempos, como D-13 y D-15 de `procesos-pendientes`.
Descartada: un diseño propio para el cambio de contraseña.
Motivo: el mismo mecanismo, probado una sola vez, para las dos features (RF-016, RF-017).

### D-14 "Caducada" en vez de rechazos propios
Elegida: con la cuenta inactiva, o con el correo o la contraseña cambiados desde la solicitud,
`verify`, `resend` y `complete` devuelven el mismo resultado que con una solicitud caducada, sin
modificarla; si la cuenta se reactiva antes de que caduque, vuelve a funcionar (RF-008, RF-014,
RF-015).
Descartada: mantener `AccountRefusal`.
Motivo: una plaza nunca da esos rechazos; responderlos revelaría que el correo tenía cuenta (C-01
del cambio). *Riesgo aceptado:* S-13 de la spec.

### D-15 Tumba al borrar la cuenta
Elegida: un receptor `pre_delete` de `User` crea, por cada solicitud de la cuenta, una
`PhantomProcess` con su `public_id`, `code_expires_at` y `created_at`, y `answers_expired = True`;
después la cascada borra la solicitud. Esa plaza responde "caducada" a todo y la purga la borra al
llegar su caducidad natural (RF-010).
Descartada: `on_delete=SET_NULL` en la solicitud (conservaría la solicitud, contra RF-010, y su
`account_stamp`, derivado del correo de una cuenta borrada).
Motivo: cumple RF-010 sin conservar datos de la cuenta borrada. El receptor también actúa en
borrados masivos, porque Django envía la señal por cada objeto.

### D-16 Aviso de contraseña restablecida en la misma transacción
Elegida: `complete` llama a `outbox.enqueue` con la cuenta (su idioma) dentro de la transacción que
fija la contraseña.
Descartada: encolarlo después de confirmar.
Motivo: la bandeja ya encola al confirmar (D-01 de `correo-asincrono-plantillas`); dentro de la
transacción, si algo falla no queda ni la contraseña ni el aviso (RF-008 de esa feature).

### D-17 Idioma del reenvío
Elegida: `PasswordResetRequest` guarda el idioma de la petición que la creó o la reemplazó (M-11), y
`reissue_code` envía el correo del reenvío en ese idioma.
Descartada: el idioma de la cuenta, que contradice RF-013 de `correo-asincrono-plantillas` (el correo
de código va en el idioma de la petición), y un parámetro de idioma en `resend`, que cambiaría la
operación y el comando y que el registro no tiene.
Motivo: el mismo criterio que el registro, que usa el idioma guardado en el registro pendiente.

## Estrategia de tests
- Unitario (`test_codes.py`, ampliado): la huella depende del tipo de proceso y una huella de un tipo
  no valida en el otro; la huella de la cuenta cambia con el correo (sin distinguir mayúsculas) y con
  el hash de la contraseña, y valida con el secreto anterior durante la transición (RF-005, RF-014,
  RF-015).
- Modelo (`test_password_reset_model.py`): una solicitud por cuenta también con `bulk_create`,
  `public_id` único, borrado en cascada con la cuenta, `expired()` por gracia y por vida máxima
  (RF-001, RF-006, RF-010). Comprobación de que no hay migraciones pendientes (CF-1, D-02).
- Servicio (`test_password_reset_service.py`): cada rama de `start` (alta, reemplazo de vigente y de
  caducada, correo con mayúsculas y espacios, sin cuenta, cuenta inactiva sin tocar su solicitud),
  `verify` (validado, erróneo, bloqueo, código caducado, solicitud caducada, ya validado, registro
  pendiente con el mismo `public_id` no sirve), `resend`, `complete` (política con correo y nombre de
  la cuenta, misma contraseña, `EmailAddress` existente, inexistente y con otra principal, código
  sin validar, caducada), cuenta inactiva y reactivada, correo y contraseña cambiados, límites con
  `override_settings` y purga sin tocar registros pendientes (RF-002…RF-009, RF-011, RF-012, RF-014,
  RF-015).
- Integración con allauth (`test_password_reset_sessions.py`): sesiones abiertas inservibles tras
  completar (CF-3, D-12); 5 inicios fallidos bloquean, completar los desbloquea, y el inicio de
  sesión con la nueva contraseña funciona (RF-009, D-08).
- Comando (`test_password_reset_command.py`): recorrido completo con `call_command`, salida de cada
  paso, sin cuenta elegible y purga (RF-011, RF-013).
- Regresión: la suite de `procesos-pendientes` (`test_registration_*`, `test_codes.py`) pasa sin
  cambios de comportamiento tras D-01, D-02, D-03 y D-09; solo se ajustan las llamadas que cambian de
  firma por el tipo de proceso.
- Desde el 2026-10-14:
  - Resolución (`test_password_reset_background.py`): crear y reemplazar la solicitud, sin cuenta o
    con la cuenta inactiva la plaza queda sin solicitud, borrado de plazas anteriores del mismo
    correo, correo con el código en la bandeja, reintento y barrido (RF-002, RF-003, RF-004,
    RF-016).
  - Equivalencia (`test_password_reset_equivalence.py`, CF-6): la misma secuencia de verificar,
    reenviar, completar y caducar da los mismos resultados con una plaza y con una solicitud real
    cuyo código nunca se acierta, con el mismo número de consultas (RF-017). Desde el 2026-10-15
    también: con un correo sin cuenta y con una cuenta inactiva (con y sin solicitud previa); con
    intentos antes de resolver y con la resolución retrasada; con dos plazas resueltas en orden
    inverso; y con una operación simultánea a la resolución detenida dentro de su transacción, con
    transacciones reales y dos hilos (D-05, D-13).
  - Ventana compartida (`test_password_reset_background.py`): cambiar
    `REGISTRATION_START_RETRY_MINUTES` cambia también la ventana del cambio de contraseña, y la
    tarea ejecutada fuera de la ventana no resuelve (RF-012, RF-016).
  - Idioma del reenvío: el correo del reenvío sale en el idioma de la petición guardado en la
    solicitud, no en el de la cuenta (D-17).
  - "Caducada" (`test_password_reset_service.py`): cuenta inactiva, reactivada, correo y contraseña
    cambiados, y la tumba tras borrar la cuenta hasta su caducidad natural (RF-008, RF-010, RF-014,
    RF-015).
  - Aviso: completar deja `password_reset_done` en la bandeja, en el idioma de la cuenta, y nada si
    la transacción falla (RF-009).
- Mutaciones en cada tarea, ejecutando el archivo de tests completo (nunca con `-k`).

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-02, M-07 | modelo |
| RF-002 | M-05, M-09 (D-13) | servicio + resolución |
| RF-003 | M-05, M-09 (D-05, D-13) | resolución + equivalencia |
| RF-004 | M-05, M-09 (D-06, D-13) | resolución + comando |
| RF-005 | M-01, M-03, M-04 | unitario + servicio |
| RF-006 | M-01, M-05 | modelo + servicio |
| RF-007 | M-04, M-05, M-09, M-11 (D-17) | servicio + equivalencia |
| RF-008 | M-05 (D-14) | servicio |
| RF-009 | M-05 (D-07, D-08, D-16) | servicio + integración allauth |
| RF-010 | M-02, M-07, M-10 (D-15) | modelo + servicio |
| RF-011 | M-05, M-06 | servicio + comando |
| RF-012 | M-01, M-08 (D-10) | servicio + resolución |
| RF-013 | M-06 | comando |
| RF-014 | M-03, M-05 (D-04, D-14) | unitario + servicio |
| RF-015 | M-03, M-05 (D-04, D-14) | unitario + servicio |
| RF-016 | M-05, M-09 (D-13) | servicio + resolución |
| RF-017 | M-05, M-09, M-10 (D-05, D-13) | equivalencia |

## RF sin cobertura
Ninguno.

## Límites conocidos del diseño
- Si una `EmailAddress` verificada con el mismo correo pertenece a otra cuenta (posible si un
  administrador cambió el correo de una cuenta sin actualizar sus direcciones de allauth y otra
  cuenta tomó ese correo), la restricción `unique_verified_email` de allauth hace fallar `complete`
  con un `IntegrityError` y la transacción no deja nada a medias. El problema ya existe hoy en
  `registration.complete`; pertenece a la sincronización entre el correo de la cuenta y allauth, no
  a esta feature.
- *Resuelto el 2026-10-14:* el tiempo de respuesta de `start` ya no depende de la cuenta (D-13).
  Queda pendiente para la API solo el mensaje neutro (S-01).
- Rotar el secreto de los códigos sin transición, o el recálculo del hash de la contraseña, deja
  una solicitud real como caducada y una plaza no (S-14, D-04).
