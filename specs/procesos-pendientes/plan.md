# Plan: procesos-pendientes
Estado: borrador

## Módulos
### M-01 Modelo `PendingRegistration` (`apps/accounts/models.py`)
Responsabilidad: guardar el registro pendiente; normalizar el correo como `User`; validar correo,
nombre, fecha y país con `validators.py`; rechazar el guardado si el correo ya tiene cuenta;
calcular si está caducado o bloqueado. Desde el cambio del 2026-10-14, la validación que no
consulta la base de datos (nombre, fecha, país y formato del correo) se ejecuta sola en la respuesta
(M-03); `save()` sigue rechazando un correo con cuenta, pero ya solo se llama fuera de la respuesta
(M-09).
RF: RF-001, RF-002, RF-003, RF-004, RF-011, RF-024

### M-02 Códigos (`apps/accounts/codes.py`)
Responsabilidad: generar el código de 6 dígitos y el identificador público, calcular la huella con
el secreto vigente y verificarla, aceptando también el secreto anterior durante la transición.
RF: RF-007, RF-008, RF-015

### M-03 Servicio de registro (`apps/accounts/registration.py`)
Responsabilidad: operaciones `start`, `verify`, `resend`, `complete` y `purge_expired`, cada una
en una transacción. `start` y `resend` hacen en la respuesta solo el trabajo que no depende de la
cuenta y dejan el resto a las tareas de M-09 (D-11, D-13). `verify`, `resend` y `complete` buscan
siempre el identificador en los registros pendientes y en los identificadores sin registro detrás
(M-08, D-14) y les aplican las mismas reglas de `processes.py`. `start` ya no devuelve el código ni
"cuenta existente": solo el identificador. Es la única puerta que usarán los comandos ahora y la API
después.
RF: RF-005, RF-009, RF-010, RF-011, RF-012, RF-013, RF-016, RF-017, RF-020, RF-024, RF-025

### M-04 Configuración (`config/settings.py`, `apps/accounts/conf.py`, `.env.example`)
Responsabilidad: límites con valores por defecto (5 intentos, 15 min, 15 min, 1 h, 1 h, 2 s y,
desde el 2026-10-14, 5 min de reintento del trabajo de empezar el registro en
`REGISTRATION_START_RETRY_MINUTES`), ajustables por variable de entorno, y el secreto de los códigos
con su secreto anterior.
RF: RF-019, RF-015

### M-05 Política de contraseñas (`config/settings.py`, `apps/accounts/password_validation.py`)
Responsabilidad: `AUTH_PASSWORD_VALIDATORS` con longitud 12, similitud con `email` y `name`,
contraseñas comunes y un validador propio de contraseñas filtradas contra el servicio de rangos de
Have I Been Pwned.
RF: RF-022

### M-06 Comando `manage.py registration` (`management/commands/registration.py`)
Responsabilidad: subcomandos `start`, `verify`, `resend`, `complete` y `purge`, que solo llaman a
M-03 y muestran el `public_id` y el resultado de la operación, nunca el código ni si el correo tiene
cuenta (S-10). `start` admite `--language` (`es` por defecto).
RF: RF-023, RF-013

### M-07 Migración `0005_pendingregistration`
Responsabilidad: crear la tabla con las restricciones únicas de `public_id` y `Lower(email)`.
RF: RF-003, RF-007 (CF-1)

### M-08 Identificador sin registro detrás (`apps/accounts/models.py`)
Responsabilidad: modelo `PhantomProcess`, una "plaza" con identificador público que hereda de
`CodeProcess` y nunca acepta un código. Se crea en la respuesta de `start` para toda solicitud
válida; si el correo no tiene cuenta, M-09 la convierte en registro pendiente, y si la tiene, queda
como identificador sin registro detrás hasta caducar o ser reemplazada (D-11, D-12). Lo reutilizará
`cambio-contrasena` con su propio propósito.
RF: RF-024, RF-025

### M-09 Trabajo fuera de la respuesta (`apps/accounts/tasks.py` y funciones de `registration.py`)
Responsabilidad: tareas de Celery `resolve_registration(public_id)` (D-16), `reissue_code(purpose,
public_id)` (D-13) y el barrido `sweep_unresolved()` (D-15), con sus reintentos. Llaman a la bandeja
de `correo-asincrono-plantillas` (`outbox.enqueue`) para el código y el aviso "ya tienes cuenta".
RF: RF-004, RF-005, RF-016, RF-017, RF-019, RF-024, RF-025

### M-10 Migración `0008_phantomprocess`
Responsabilidad: crear la tabla de `PhantomProcess` con la unicidad de `public_id`.
RF: RF-025 (CF-1)

## Modelo de datos
`accounts.PendingRegistration`:
- `email` EmailField + `UniqueConstraint(Lower("email"))` (como `User`).
- `name` CharField(150), `birthdate` DateField, `country` CharField(2).
- `public_id` CharField(64), único.
- `code_hash` CharField(64): HMAC-SHA256 en hexadecimal.
- `code_expires_at` DateTimeField.
- `failed_attempts` PositiveSmallIntegerField, por defecto 0.
- `code_validated_at` DateTimeField, nulo mientras no se valide.
- `created_at` DateTimeField al crear.

Sin historial (`simple-history`): son datos de un proceso que se borran al terminar.
La caducidad no se guarda; se calcula: mín(`code_expires_at` + gracia, `created_at` + vida máxima).

`accounts.PhantomProcess` (cambio del 2026-10-14), hereda de `CodeProcess` los mismos campos de
código, intentos, validación y fecha de alta:
- `purpose` CharField: `registration` aquí; `password_reset` en `cambio-contrasena`.
- `email` EmailField, normalizado: sirve para reemplazar la plaza anterior del mismo correo (RF-025).
- `payload` JSONField nulo: nombre, fecha, país e idioma de la solicitud mientras M-09 no la
  resuelve; se vacía al resolverla o al agotar los reintentos (D-15).
- `code_hash` vacío: ninguna huella coincide con él, así que ningún código se acepta (D-12).

Sin historial; se purga con los registros pendientes caducados (RF-013).

## Decisiones
### D-01 Huella del código
Elegida: HMAC-SHA256 con un secreto del servidor sobre `public_id` + código, comparada en tiempo
constante.
Descartada: hash lento de contraseña (PBKDF2/Argon2) sin secreto.
Motivo: un código de 6 dígitos tiene 1 millón de valores; cualquier hash sin secreto se rompe por
fuerza bruta con la base de datos en la mano (RF-008). El HMAC exige además el secreto, y atar la
huella al `public_id` impide reutilizarla en otro proceso. *Nota del 2026-10-14:* mientras su
correo espera en la bandeja, el código vive además oculto con la máscara de
`huellas-hmac-unificadas` (D-06 de `correo-asincrono-plantillas`, RF-008).

### D-02 Secreto y rotación
Elegida: variable `REGISTRATION_CODE_SECRET` (por defecto, `SECRET_KEY`, para que desarrollo y CI
funcionen igual), más `REGISTRATION_CODE_SECRET_PREVIOUS` y `REGISTRATION_CODE_SECRET_ROTATED_AT`:
el anterior se acepta hasta `ROTATED_AT` + periodo de transición.
Descartada: guardar en cada fila qué versión de secreto se usó.
Motivo: cumple RF-015 sin columnas extra; los procesos viven como mucho 1 hora, así que basta con
probar dos secretos. En producción el secreto va cifrado con SOPS (P-01): queda en `HUMAN_TODO`.

### D-03 Identificador público y código
Elegida: `secrets.token_urlsafe(32)` (256 bits) para `public_id` y `secrets.randbelow(10**6)`,
rellenado a 6 dígitos, para el código.
Descartada: UUID4 y `random`.
Motivo: `secrets` es criptográficamente seguro; `token_urlsafe` va bien en URL (S-06, futura API).

### D-04 Crear la cuenta
Elegida: dentro de una transacción, `User.objects.create_user` con los datos del registro y la
contraseña, `EmailAddress.objects.create(..., verified=True, primary=True)` de allauth y borrar el
registro pendiente.
Descartada: `adapter.confirm_email` de allauth.
Motivo: D-01 del spike permite usar los gestores de los modelos públicos de allauth, y
`confirm_email` exige una petición con sesión (C-14), que no existe en consola. La transacción
cumple el "en una sola operación" de RF-020.

### D-05 Política de contraseñas global
Elegida: cambiar `AUTH_PASSWORD_VALIDATORS` del proyecto (longitud 12, similitud con
`("email", "name")`, comunes, filtradas) y validar en `complete` con un `User` sin guardar que
lleva el correo y el nombre del registro pendiente.
Descartada: una política solo para el registro.
Motivo: una única política para todo el sistema; el futuro cambio de contraseña (S-11) la hereda.
Se mantiene `NumericPasswordValidator`, que ya existía: rechaza contraseñas solo numéricas y no
contradice RF-022. *Efecto:* el signup de allauth, todavía expuesto, también la aplica.

### D-06 Contraseñas filtradas sin dependencias ni red en los tests
Elegida: validador propio con `urllib` de la librería estándar contra
`https://api.pwnedpasswords.com/range/<5 caracteres del SHA-1>` (con la cabecera `Add-Padding`),
con tiempo máximo configurable. Si falla, aviso en el log y se acepta (S-09). Un ajuste
`PWNED_PASSWORDS_ENABLED` lo apaga; los tests lo apagan por defecto y prueban el validador
simulando la respuesta.
Descartada: un paquete externo (p. ej. `pwnedpasswords`).
Motivo: no añade dependencias (AGENTS.md); la suite no depende de internet ni de un servicio
externo.

### D-07 Tiempo en los tests
Elegida: el servicio usa `timezone.now()`; los tests mueven las fechas guardadas
(`created_at`, `code_expires_at`) con `update()` para simular el paso del tiempo.
Descartada: `freezegun` u otra librería de reloj.
Motivo: no añade dependencias y prueba la caducidad igual.

### D-08 Concurrencia
*Cambio del 2026-10-14:* lo que sigue se aplica ahora en `resolve_registration` (M-09), fuera de la
respuesta.
Elegida: `start` bloquea la fila existente con `select_for_update` y, si dos altas simultáneas
chocan en la restricción única del correo, trata la segunda como registro repetido (RF-005).
Descartada: confiar solo en el orden de llegada.
Motivo: RF-003 lo garantiza la base de datos; el servicio no debe devolver un error de base de
datos.

### D-09 Comando con subcomandos
Elegida: un único `manage.py registration <start|verify|resend|complete|purge>`; `complete` pide
la contraseña sin eco (`getpass`) o la acepta con `--password` para scripts y tests.
Descartada: cinco comandos sueltos.
Motivo: el proceso se descubre en un solo `--help`. *Riesgo:* `--password` queda en el historial
de la consola; se documenta.

### D-10 Correo con cuenta en `start` — OBSOLETA
OBSOLETA (2026-10-14): `start` ya no distingue el correo con cuenta; la sustituye D-11.
Texto original: Elegida: el servicio devuelve un resultado "cuenta existente" sin guardar nada, y el comando lo
muestra tal cual.
Descartada: lanzar una excepción.
Motivo: la futura API debe responder igual en los tres casos (respuesta 8); un resultado tipado se
lo pone fácil. En consola no hay riesgo de enumeración (S-10).

### D-11 Plaza en la respuesta para toda solicitud válida
Elegida: `start` valida los datos sin consultar cuentas, crea en la respuesta una `PhantomProcess`
con un `public_id` nuevo y los datos en `payload`, y encola `resolve_registration` al confirmar.
Descartada: mandar los datos solo en el mensaje de la cola. Si el mensaje se pierde, el identificador
no tiene nada detrás y responde "desconocido", distinto de un registro real; además, los datos
personales quedarían en el broker.
Motivo: la respuesta hace el mismo trabajo (una inserción) tenga o no cuenta el correo (RF-024), y
si el trabajo de fuera falla, la plaza ya se comporta como un identificador sin registro (C-03).

### D-12 Identificador sin registro con las mismas reglas
Elegida: `PhantomProcess` hereda de `CodeProcess` con `code_hash` vacío. `processes.check_code` le
da `WRONG_CODE`, el bloqueo al quinto intento y la caducidad exactamente como a un registro real.
Descartada: una marca en `PendingRegistration` (su unicidad por correo y su rechazo de correos con
cuenta impedirían la plaza de una cuenta existente) y simularlo en memoria (no guarda intentos ni
caducidad).
Motivo: RF-025 pide los mismos resultados en el mismo orden; con las mismas reglas no hay que
imitarlas.

### D-13 Reenvío en dos tiempos
Elegida: en la respuesta, `resend` invalida el código vigente (`code_hash` vacío) y pone los
intentos a 0; fuera, `reissue_code` emite el código nuevo y, si es un registro real, encola su
correo. Una plaza recibe también un código nuevo, que nunca se envía.
Descartada: poner los intentos a 0 en la respuesta y dejar vivo el código anterior hasta emitir el
nuevo.
Motivo: no se abre una ventana de 5 intentos más contra un código que va a reemplazarse. Los
correos pendientes del código anterior se descartan al entregarlos (D-05 de
`correo-asincrono-plantillas`).

### D-14 Buscar siempre en las dos tablas
Elegida: `verify`, `resend` y `complete` consultan `PendingRegistration` y `PhantomProcess` por el
`public_id`, se encuentre o no en la primera.
Descartada: consultar la plaza solo si no hay registro pendiente.
Motivo: el mismo número de consultas en los dos casos; un test lo fija con
`django_assert_num_queries`.

### D-15 Reintentos del trabajo de fuera y barrido
*Cambio del 2026-10-15 (validación):* la ventana se comprueba antes de resolver, en cada ejecución.
Elegida: la tarea `resolve_registration` mira la ventana antes de resolver: si ya han pasado
`REGISTRATION_START_RETRY_MINUTES` desde el alta de la plaza, no la resuelve, también en un primer
intento que la cola atendió tarde. Dentro de la ventana, si falla, reintenta con espera creciente
(15 s, 30 s y 60 s como máximo) sin el tope de 3 reintentos de Celery: la ventana es el único
límite. Un barrido cada 60 s en el planificador vuelve a encolar las plazas sin resolver dentro de
esa ventana. Pasada la ventana, la plaza se queda como identificador sin registro, se vacía su
`payload`, no se envía correo y el fallo se registra en el log del servidor.
Descartada: solo los reintentos de Celery (si la cola estaba caída al confirmar, nadie reintenta), y
mirar la ventana solo después de un fallo (un reintento o una tarea atendida tarde resolvía fuera de
la ventana y enviaba el correo).
Motivo: cumple C-03 aunque la cola caiga, como la bandeja de correos, y RF-024 ("solo durante el
tiempo configurado").

### D-16 Qué hace la resolución
*Cambio del 2026-10-15 (validación):* pasos 1, 2 y 4 ajustados (D-17).
Elegida: en una transacción, con la plaza bloqueada:
1. Si hay una plaza posterior sin resolver del mismo correo y propósito, borra esta plaza y no hace
   nada más: manda la petición más reciente (D-17). Si no, borra los registros pendientes caducados
   del mismo correo (RF-017) y las plazas anteriores del mismo correo y propósito (RF-025).
2. Si el correo tiene cuenta, la plaza queda como identificador sin registro, en el mismo estado en
   que `issue_code` deja un registro real: intentos a 0, sin validar y con el código vigente desde la
   resolución. Su alta es la de la plaza vigente anterior del mismo correo que reemplaza (leída antes
   de borrarla), igual que un registro repetido conserva la suya (RF-005); si no la había, o estaba
   caducada, el alta es la de la resolución, igual que un registro nuevo. Si la cuenta está activa,
   encola el aviso "ya tienes cuenta" (RF-006, con el tope de RF-007).
3. Si hay un registro pendiente vigente del mismo correo, le asigna el `public_id` de la plaza,
   emite un código nuevo con los intentos a 0 y sin validar, conservando sus datos (RF-005), y borra
   la plaza.
4. Si no, crea el registro pendiente con los datos de la plaza y su `public_id`, con el alta de la
   resolución, y borra la plaza.

En los casos 3 y 4 encola el correo con el código en el idioma de la solicitud (RF-004). Un choque
en la unicidad del correo se trata como el caso 3 (D-08).
Descartada: decidir en la respuesta y diferir solo el correo (volvería a filtrar la cuenta por el
tiempo).
Motivo: todo lo que depende de la cuenta ocurre fuera de la respuesta (RF-024). Desde el
2026-10-15, además, la plaza con cuenta y el registro real cuentan intentos y plazos desde el mismo
instante, aunque la resolución se retrase o el correo se repita (RF-025).

### D-17 Manda la petición más reciente
Elegida: entre las plazas del mismo correo y propósito, la más reciente es la de mayor `pk`. La
resolución de una plaza borra solo las anteriores; si encuentra una posterior aún sin resolver, se
borra a sí misma sin crear registro ni enviar correo, y la posterior hace el trabajo al resolverse.
Descartada: borrar "las demás plazas" sin mirar el orden (con dos peticiones resueltas en orden
inverso, la antigua anulaba a la nueva).
Motivo: RF-005 y RF-025 piden que la petición nueva anule a la anterior, también cuando las tareas
se ejecutan desordenadas (doble envío, reintentos, barrido).

### D-18 Orden de bloqueo: primero la plaza
Elegida: `verify`, `resend`, `complete` y `reissue_code` bloquean primero la plaza por su
`public_id` y después consultan y bloquean el registro pendiente, el mismo orden que la resolución
(plaza → registro). Si una resolución está convirtiendo la plaza, la operación espera a que confirme
y después encuentra el registro ya creado.
Descartada: consultar primero el registro pendiente. Con una resolución en curso, el registro aún no
existía al consultarlo y la plaza ya estaba borrada al liberarse el bloqueo: "desconocido", solo en
el caso sin cuenta.
Motivo: RF-025 pide los mismos resultados también con operaciones simultáneas; las consultas siguen
siendo las mismas en los dos casos (D-14).

## Estrategia de tests
- Unitario (`test_codes.py`): formato del código y del `public_id`, la huella no contiene el
  código, verificación en tiempo constante, rotación dentro y fuera de la transición (RF-007,
  RF-008, RF-015).
- Modelo (`test_pending_registration_model.py`): validación y normalización, rechazo con cuenta
  existente, unicidad por `bulk_create` (RF-001…RF-004).
- Servicio (`test_registration_service.py`): el ciclo completo y cada rama — repetido, reenvío,
  intentos y bloqueo, caducidad por gracia y por vida máxima, código ya validado, cuenta creada
  entretanto, purga, caducados del mismo correo, límites cambiados con `override_settings`
  (RF-005, RF-009…RF-013, RF-016, RF-017, RF-019, RF-020).
- Contraseñas (`test_password_policy.py`): cada regla, con la respuesta del servicio simulada,
  incluido el tiempo agotado (RF-022).
- Comando (`test_registration_command.py`): recorrido completo con `call_command` y su salida
  (RF-023, RF-013); desde el 2026-10-14, el código se lee del correo entregado por el backend en
  memoria, y `start` muestra lo mismo tenga o no cuenta el correo.
- Respuesta neutra (`test_registration_service.py`): `start` devuelve el mismo tipo de resultado y
  hace las mismas consultas con y sin cuenta (`django_assert_num_queries`); los errores de datos no
  mencionan la cuenta (RF-024).
- Resolución y reintentos (`test_registration_background.py`): los cuatro casos de D-16 llamando a
  las funciones directamente, el reintento dentro de la ventana, el barrido y la plaza que queda sin
  registro al agotarla (RF-004, RF-005, RF-006, RF-017, RF-024).
- Equivalencia (`test_phantom_equivalence.py`, CF-5): la misma secuencia de verificar (con el
  bloqueo al quinto intento), reenviar, completar y caducar da los mismos resultados con una plaza y
  con un registro real cuyo código nunca se acierta; una solicitud nueva anula la plaza anterior
  (RF-025). Mismo número de consultas en `verify`, `resend` y `complete` (D-14). Desde el
  2026-10-15 también: intentos fallidos antes de resolver, resolución retrasada 4 min, repetición
  con el paso del tiempo (`start`, `resend` y `start`, observando a los 61 min), dos plazas resueltas
  en orden inverso (D-17) y una operación simultánea con la resolución detenida dentro de su
  transacción, con transacciones reales y dos hilos (D-18).
- Ventana (`test_registration_background.py`): la tarea ejecutada fuera de la ventana, sin simular
  la resolución, no crea registro ni encola correo, vacía el `payload` y deja el fallo en el log
  (D-15).
- Login: la cuenta creada inicia sesión por app (cierra el ciclo con allauth).
- Mutaciones en cada tarea, como en `usuario-personalizado`.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-07 | modelo |
| RF-002 | M-01 | modelo |
| RF-003 | M-01, M-07, M-03 (D-08) | modelo (bulk) + servicio |
| RF-004 | M-01, M-03 | modelo + servicio |
| RF-005 | M-03, M-09 (D-16, D-17) | servicio + resolución |
| RF-007 | M-02, M-07 | unitario + modelo |
| RF-008 | M-02 (D-01) | unitario |
| RF-009 | M-03 | servicio |
| RF-010 | M-03, M-04 | servicio |
| RF-011 | M-01, M-03 | servicio |
| RF-012 | M-03 | servicio |
| RF-013 | M-03, M-06 | servicio + comando |
| RF-015 | M-02, M-04 | unitario |
| RF-016 | M-03, M-09 (D-13) | servicio |
| RF-017 | M-03 | servicio |
| RF-019 | M-04 | servicio + unitario |
| RF-020 | M-03 (D-04) | servicio + login |
| RF-022 | M-05 | contraseñas |
| RF-023 | M-06 | comando |
| RF-024 | M-01, M-03, M-08, M-09 (D-11, D-15, D-16) | servicio + resolución |
| RF-025 | M-08, M-10, M-03, M-09 (D-12, D-14, D-16, D-17, D-18) | equivalencia |

## RF sin cobertura
Ninguno (RF-006, RF-014, RF-018 y RF-021 son obsoletos).
