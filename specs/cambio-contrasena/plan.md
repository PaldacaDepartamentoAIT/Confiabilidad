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
transacción. Es la puerta que usan el comando ahora y la API después.
RF: RF-002, RF-003, RF-004, RF-006, RF-007, RF-008, RF-009, RF-011, RF-014, RF-015

### M-06 Comando `manage.py password_reset` (`management/commands/password_reset.py`) y utilidades de consola (`management/console.py`, nuevo)
Responsabilidad: subcomandos `start`, `verify`, `resend`, `complete` y `purge`, que solo llaman a
M-05. Las utilidades que hoy están en el comando `registration` (mostrar `public_id` y código,
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

## Modelo de datos
`accounts.CodeProcess` (abstracto, sin tabla), con los campos actuales de `PendingRegistration`:
- `public_id` CharField(64), único en la tabla de cada proceso.
- `code_hash` CharField(64): HMAC-SHA256 en hexadecimal (D-01).
- `code_expires_at` DateTimeField.
- `failed_attempts` PositiveSmallIntegerField, por defecto 0.
- `code_validated_at` DateTimeField, nulo mientras no se valide.
- `created_at` DateTimeField al crear (en el reemplazo se reasigna a "ahora", RF-003).

`accounts.PasswordResetRequest(CodeProcess)`:
- `user` OneToOneField(`User`, `on_delete=CASCADE`, `related_name="password_reset_request"`):
  una solicitud por cuenta garantizada por la base de datos, también en `bulk_create` y SQL directo
  (RF-001, CF-1), y borrado con la cuenta (RF-010).
- `account_stamp` CharField(64): HMAC-SHA256 del correo en minúsculas y del hash de la contraseña
  de la cuenta en el momento de pedir o reemplazar la solicitud (D-04).

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

### D-05 Orden de bloqueo y concurrencia
Elegida:
- `start` bloquea primero la fila de la cuenta (`select_for_update` sobre `User`) y después la
  solicitud; así dos peticiones simultáneas para la misma cuenta se ordenan y la segunda reemplaza
  a la primera (RF-003). El alta va en un punto de guardado: si choca con la unicidad por una
  escritura ajena al servicio, el `IntegrityError` se traduce en reemplazar la fila existente,
  nunca sale al llamante (lección de `procesos-pendientes`).
- `verify` y `resend` bloquean solo la solicitud (no escriben en la cuenta).
- `complete` lee la solicitud sin bloqueo para conocer la cuenta, bloquea la cuenta y después la
  solicitud (mismo orden que `start`, sin interbloqueos), y comprueba que sigue siendo la misma
  solicitud.
Descartada: bloquear solo la solicitud en todas las operaciones.
Motivo: `complete` escribe en la cuenta y en `EmailAddress`; con órdenes distintos en `start` y
`complete`, Postgres abortaría una de las dos por interbloqueo. *Riesgo residual heredado:* como en
`procesos-pendientes`, ningún test ejerce dos transacciones reales a la vez.

### D-06 Resultados del servicio
Elegida: resultados tipados, como en el registro (D-10 de `procesos-pendientes`): `Started`,
`NoEligibleAccount` (RF-004, único para "sin cuenta" y "cuenta inactiva"), `VerifyResult` común más
un `AccountRefusal` propio (`INACTIVE`, `ACCOUNT_CHANGED`) para RF-008, RF-014 y RF-015, `Resent`,
`Completed` y las negativas de `complete`. La contraseña inválida sale como `ValidationError` con
cada regla, igual que en `registration.complete`.
Descartada: excepciones para los casos de negocio.
Motivo: la API futura debe convertir `NoEligibleAccount` en la misma respuesta que `Started`
(S-01); con un resultado tipado es una rama explícita, no un `except` que se puede olvidar.

### D-07 Completar
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
Motivo: reutilizar sin acoplar un comando a otro. Sin cuenta elegible, el comando termina con error
y el mensaje "No active account with this email." (S-06: en consola no hay riesgo de enumeración).

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
- Mutaciones en cada tarea, ejecutando el archivo de tests completo (nunca con `-k`).

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-02, M-07 | modelo |
| RF-002 | M-05 | servicio |
| RF-003 | M-05 (D-05) | servicio |
| RF-004 | M-05 (D-06) | servicio + comando |
| RF-005 | M-01, M-03, M-04 | unitario + servicio |
| RF-006 | M-01, M-05 | modelo + servicio |
| RF-007 | M-04, M-05 | servicio |
| RF-008 | M-05 | servicio |
| RF-009 | M-05 (D-07, D-08) | servicio + integración allauth |
| RF-010 | M-02, M-07 | modelo |
| RF-011 | M-05, M-06 | servicio + comando |
| RF-012 | M-01, M-08 (D-10) | servicio |
| RF-013 | M-06 | comando |
| RF-014 | M-03, M-05 (D-04) | unitario + servicio |
| RF-015 | M-03, M-05 (D-04) | unitario + servicio |

## RF sin cobertura
Ninguno.

## Límites conocidos del diseño
- Si una `EmailAddress` verificada con el mismo correo pertenece a otra cuenta (posible si un
  administrador cambió el correo de una cuenta sin actualizar sus direcciones de allauth y otra
  cuenta tomó ese correo), la restricción `unique_verified_email` de allauth hace fallar `complete`
  con un `IntegrityError` y la transacción no deja nada a medias. El problema ya existe hoy en
  `registration.complete`; pertenece a la sincronización entre el correo de la cuenta y allauth, no
  a esta feature.
- El tiempo de respuesta de `start` es distinto con y sin cuenta elegible; neutralizarlo es de la API
  (S-01, CF-5).
