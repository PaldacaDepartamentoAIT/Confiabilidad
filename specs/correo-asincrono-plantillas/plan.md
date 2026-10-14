# Plan: correo-asincrono-plantillas
Estado: borrador

## Módulos
### M-01 App `apps/emails`: modelos y migraciones
Responsabilidad: guardar las plantillas editables (con historial), la bandeja de salida con los
correos pendientes y fallidos, y la marca del último aviso "ya tienes cuenta" de cada cuenta. La
migración de datos crea las 21 plantillas iniciales y da al grupo «Soporte técnico» los permisos del
panel.
RF: RF-001, RF-017, RF-020, RF-022

### M-02 Plantillas (`apps/emails/rendering.py`)
Responsabilidad: variables admitidas y obligatorias por tipo, sustitución de `{{ variable }}`,
validación al guardar (datos que faltan o sobran y enlaces a otros dominios), bloque fijo de
reporte por idioma, plazo relativo por idioma y construcción de los enlaces con el identificador
público. Los valores se insertan siempre como texto.
RF: RF-010, RF-014, RF-021, RF-023

### M-03 Bandeja (`apps/emails/outbox.py`)
Responsabilidad: única puerta de entrada para pedir un correo. Guarda la fila en la transacción de
quien llama y, al confirmarse, la encola en Celery. Resuelve el idioma, aplica el tope del aviso "ya
tienes cuenta" y cifra el código. No añade cabeceras ni enlaces de baja.
RF: RF-002, RF-003, RF-007, RF-011, RF-013

### M-04 Cifrado del código (`apps/emails/crypto.py`)
Responsabilidad: cifrar y descifrar el código de un correo pendiente con una clave propia (con clave
anterior opcional para rotarla).
RF: RF-018

### M-05 Entrega y reintentos (`apps/emails/delivery.py`, `apps/emails/tasks.py`, `apps/emails/errors.py`)
Responsabilidad: tarea `deliver(email_id)` y barrido periódico `dispatch_due()`. Cada intento
comprueba si el correo sigue sirviendo (código vigente o ventana de 24 h), lo renderiza en ese
momento, lo entrega al proveedor y, según el resultado, lo borra, programa el siguiente intento o lo
marca como fallido. `errors.py` clasifica el error del proveedor en temporal o definitivo.
RF: RF-002, RF-014, RF-015, RF-016, RF-017, RF-018, RF-024, RF-026

### M-06 Panel de administración (`apps/emails/admin.py`)
Responsabilidad: editar el asunto y el cuerpo de las plantillas existentes, sin crearlas ni
borrarlas, con historial de solo lectura; consultar y borrar los correos fallidos. Solo para el grupo
«Soporte técnico» y los superusuarios.
RF: RF-017, RF-020, RF-021, RF-022

### M-07 Comando `manage.py emails` (`apps/emails/management/commands/emails.py`)
Responsabilidad: subcomandos `test` (encola un correo de prueba de un tipo e idioma a una
dirección), `notify` (encola un aviso de contraseña cambiada, cuenta deshabilitada o cierre remoto
de sesiones a una cuenta) y `dispatch` (ejecuta el barrido en el momento).
RF: RF-009, RF-025

### M-08 Configuración (`config/settings.py`, `backend/.env.example`, `HUMAN_TODO.md`)
Responsabilidad: proveedor SMTP por variables de entorno (consola en desarrollo), remitente,
dirección de soporte, dirección base del frontend, clave de cifrado de los códigos, ventanas
configurables (aviso "ya tienes cuenta" y reintento de avisos) y el barrido en el planificador.
RF: RF-007, RF-016, RF-018, RF-024

### M-09 Cambios en `apps/accounts`
Responsabilidad: campo `language` en `User` y `PendingRegistration` (migración `0007`); copiar el
idioma a la cuenta al completar el registro; y `apps/accounts/email_checks.py`, que registra en
`apps/emails` cómo saber si el código de un proceso sigue vigente.
RF: RF-012, RF-013, RF-015

### M-10 Puntos de envío en los procesos (planes de `procesos-pendientes` y `cambio-contrasena`)
Responsabilidad: llamar a M-03 desde el trabajo de fuera de la respuesta de empezar el registro
(código o aviso "ya tienes cuenta"), desde pedir el restablecimiento (código), desde el reenvío de
los dos procesos (código) y desde completar el restablecimiento (aviso de contraseña restablecida).
Se diseña e implementa en los planes de esas dos features, que ya cambian esas mismas funciones;
este plan solo fija la interfaz de M-03 que usarán.
RF: RF-004, RF-005, RF-006, RF-008, RF-019

## Modelo de datos
- `EmailTemplate`: `kind` (los siete tipos de RF-001), `locale` (`es`, `pt-BR`, `en`, como
  `consents`), `subject`, `body`, `updated_at`. Única por (`kind`, `locale`). Historial con
  `simple_history` (autor por `HistoryRequestMiddleware`).
- `OutboundEmail`: `kind`, `locale`, `recipient`, `context` (JSON con el nombre y los datos no
  secretos), `purpose` y `public_id` (solo en los de código), `encrypted_code` (nulo salvo en los de
  código pendientes), `status` (`pending` | `failed`), `attempts`, `next_attempt_at`, `last_error`,
  `created_at`. Índice por (`status`, `next_attempt_at`). Los entregados y los descartados se borran;
  los fallidos se quedan, sin código, hasta que soporte los borre.
- `FailedEmail`: modelo proxy de `OutboundEmail` con `status = failed`, solo para el panel.
- `AccountExistsNotice`: `user` (uno a uno con la cuenta, borrado en cascada) y `last_queued_at`.
- `accounts.User.language` y `accounts.PendingRegistration.language`: `es` | `pt-BR` | `en`, por
  defecto `es` (las cuentas existentes quedan en español, RF-012).

## Decisiones
### D-01 Bandeja en la base de datos con encolado al confirmar y barrido periódico
Elegida: la fila `OutboundEmail` se guarda en la transacción de la operación, y
`transaction.on_commit` encola `deliver`. Si encolar falla (cola caída), se registra y no se propaga.
Un barrido cada 30 s (`dispatch_due`) encola las filas pendientes con el intento vencido.
Descartada: encolar directamente en Celery sin fila (se pierde el correo si la cola está caída o si
se cae el worker) y librerías como `django-celery-email` (dependencia nueva, sin bandeja).
Motivo: cumple RF-002 y RF-003 sin perder correos y sin dependencias; la cola solo transporta el id.

### D-02 Proveedor: SMTP de Django contra MXroute
Elegida: `django.core.mail.backends.smtp.EmailBackend` configurado por entorno (`EMAIL_HOST`,
`EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_SSL`/`EMAIL_USE_TLS`,
`EMAIL_TIMEOUT`, `DEFAULT_FROM_EMAIL`). En desarrollo, el backend de consola (el correo completo
sale en la salida del worker, S-14); en los tests, el de memoria de Django o el simulado de D-15.
Descartada: un proveedor transaccional por API con `django-anymail`.
Motivo: no añade dependencias y cambiar de proveedor es cambiar variables de entorno (RF-024). Los
proveedores transaccionales también ofrecen SMTP.

### D-03 Clasificación de los errores del proveedor
Elegida: definitivos los rechazos SMTP con código 5xx del destinatario, del remitente o de los
datos (`SMTPRecipientsRefused`, `SMTPSenderRefused`, `SMTPDataError`). Temporales los códigos 4xx,
la desconexión, el tiempo agotado, los errores de red y la autenticación fallida.
Descartada: tratar la autenticación fallida como definitiva.
Motivo: una contraseña mal configurada no es culpa del correo; como temporal, al corregirla los
correos pendientes salen dentro de su ventana. Cualquier excepción no reconocida cuenta como
temporal y se registra.

### D-04 Reintentos con espera creciente y reserva del intento
Elegida: espera de 30 s × 2^(intentos − 1), con un tope de 15 min. Antes de enviar, el intento
reserva la fila (`select_for_update(skip_locked=True)` y `next_attempt_at` = ahora + 5 min), envía
fuera de la transacción y actualiza el resultado.
Descartada: reintentos de Celery (`autoretry_for`) sin fila.
Motivo: el estado vive en la base de datos y sobrevive a reinicios; la reserva evita que dos workers
envíen el mismo correo a la vez. *Coste:* si el worker cae entre enviar y guardar, el correo puede
llegar dos veces (entrega al menos una vez).

### D-05 Vigencia del código consultada al entregar
Elegida: `apps/emails` mantiene un registro de comprobadores por propósito, y `apps/accounts` (en
`AppConfig.ready`) registra uno que, con el propósito, el `public_id` y el código descifrado,
devuelve la caducidad del código si el proceso existe, el código coincide con su huella, no está
validado y no ha caducado; si no, nada. Sin caducidad, el correo se descarta (RF-015).
Descartada: copiar la caducidad en la fila (no detecta un código validado ni reemplazado) e importar
los modelos de `accounts` desde `apps/emails` (crea un ciclo de imports, porque `accounts` llama a
la bandeja).
Motivo: detecta caducado, validado y reemplazado con la misma regla de huella que ya usa la
verificación, sin acoplar las apps.

### D-06 Cifrado del código con Fernet
Elegida: `cryptography.fernet` (`MultiFernet` con la clave actual y, si existe, la anterior). Clave
en `EMAIL_CODE_KEY`; si no se define, se deriva de `DJANGO_SECRET_KEY` con SHA-256 para que
desarrollo y CI funcionen igual. El texto cifrado se borra al entregar, descartar o fallar.
`cryptography` ya está instalada (la trae `daphne`), pero hay que **declararla en
`requirements.txt`**: usarla sin declararla dejaría el proyecto a merced de las dependencias de
`daphne`.
Descartada: AES-GCM montado a mano con `cryptography.hazmat` (más código, más fácil de equivocarse)
y no cifrar (rechazado en C-02 de la spec).
Motivo: Fernet autentica y cifra, y su formato está probado.

### D-07 Sintaxis propia de plantilla con lista blanca
Elegida: `{{ variable }}`, sustituida con una expresión regular; cada tipo tiene sus variables
admitidas y obligatorias. Una variable desconocida o una obligatoria ausente impiden guardar.
Descartada: el motor de plantillas de Django y `str.format`.
Motivo: desde el panel, el motor de Django permite etiquetas, filtros y acceso a atributos, y
`str.format` permite recorrer atributos (`{user.__class__}`). La lista blanca solo deja insertar
texto.

### D-08 Textos fijos por idioma en el código
Elegida: el bloque de reporte de RF-010 y las frases del plazo ("9 minutos", "1 minuto", "menos de
un minuto") viven en un diccionario por idioma en `rendering.py`.
Descartada: catálogos `gettext` (`.po`/`.mo`).
Motivo: el proyecto no tiene catálogos de traducción ni `makemessages` en su flujo; un diccionario
se prueba directamente idioma a idioma y no depende de compilar nada.

### D-09 Identificador público en el fragmento del enlace
Elegida: `<FRONTEND_BASE_URL>/register/continue#<public_id>` y
`<FRONTEND_BASE_URL>/password-reset/continue#<public_id>`.
Descartada: el identificador en la ruta o en un parámetro de consulta.
Motivo: el fragmento no viaja al servidor, así que no queda en los registros de proxies ni en la
cabecera `Referer`. El frontend lo leerá cuando exista su pantalla (S-12).

### D-10 Idioma como campo de la cuenta y del registro pendiente
Elegida: campo `language` con valor por defecto `es` en los dos modelos. La normalización acepta
variantes (`pt-br`, `pt_BR`) y convierte cualquier otro valor en `es`.
Descartada: una tabla de preferencias aparte.
Motivo: es un dato por cuenta, sin historia propia; un campo lo deja en el historial de la cuenta.

### D-11 Tope del aviso "ya tienes cuenta" al encolar
Elegida: tabla `AccountExistsNotice` con la hora del último aviso encolado; si cae dentro de la
ventana (`EMAIL_ACCOUNT_EXISTS_WINDOW_MINUTES`, 60 por defecto), no se encola otro.
Descartada: un campo en `User` (ensuciaría su historial con cada intento ajeno) y la caché (se
pierde al vaciarla).
Motivo: dato durable y separado de la cuenta.

### D-12 Solo se conservan los correos fallidos
Elegida: los entregados y descartados se borran de la bandeja; los fallidos se quedan sin el código.
Descartada: conservar un histórico de envíos.
Motivo: la spec solo pide el registro de fallos (RF-017), y cada fila guarda una dirección de correo.

### D-13 Permisos del panel por el grupo «Soporte técnico»
Elegida: una migración de datos añade al grupo existente (lo crea `consents.0002`) los permisos de
ver y cambiar plantillas y de ver y borrar correos fallidos; el panel además exige pertenecer al
grupo o ser superusuario, como D-09 de `consentimientos`.
Descartada: permisos sueltos por usuario.
Motivo: el mismo criterio que ya usa el proyecto para soporte.

### D-14 Barrido en el planificador por configuración
Elegida: `CELERY_BEAT_SCHEDULE` con `dispatch_due` cada 30 s; el `DatabaseScheduler` lo sincroniza
con la base de datos al arrancar el beat.
Descartada: crear el `PeriodicTask` en una migración.
Motivo: queda versionado en `settings.py` y no depende del orden de las migraciones.

### D-15 Proveedor simulado para los tests
Elegida: un backend de correo de test (en `apps/emails/tests/`) al que cada test le indica qué
errores lanzar en los siguientes envíos, y que guarda los correos entregados.
Descartada: simular `smtplib` con `mock`.
Motivo: prueba el camino real de Django (`get_connection`, `send_messages`) y los mismos errores que
lanzaría SMTP.

### D-16 Plantillas fijas: ni nuevas ni borradas
Elegida: tipos e idiomas cerrados (`choices`), unicidad por (`kind`, `locale`) en la base de datos,
panel sin añadir ni borrar, y `delete()` del modelo y del queryset que lo rechazan.
Descartada: confiar solo en el panel.
Motivo: RF-022 exige impedir el borrado por cualquier vía de la aplicación.

## Estrategia de tests
- Unitario (`test_rendering.py`, `test_crypto.py`, `test_errors.py`): variables y validación por
  tipo, enlaces de otro dominio, bloque fijo en los tres idiomas, plazo con redondeo y "menos de un
  minuto", nombres Unicode insertados tal cual, cifrado y rotación de clave, clasificación de cada
  excepción SMTP (RF-010, RF-014, RF-018, RF-021, RF-023, RF-026).
- Servicio (`test_outbox.py`, `test_delivery.py`) con el proveedor simulado (D-15) y fechas movidas
  con `update()` (D-07 de `procesos-pendientes`): encolado al confirmar y nada si se deshace, fila
  pendiente si encolar falla y barrido posterior, reintento hasta entregar, descarte de código
  caducado, validado o reemplazado, ventana de 24 h, fallo definitivo inmediato, registro de fallos
  sin código, tope del aviso, idioma de cada tipo, sin cabeceras de baja (RF-002, RF-003, RF-007,
  RF-011, RF-013, RF-015, RF-016, RF-017, RF-018, RF-026).
- Integración con worker real (como `test_task_worker.py` de `core`): un correo encolado sale por el
  worker (CF-1, RF-002).
- Modelo y migraciones (`test_models.py`, `test_migrations.py`): las 21 plantillas iniciales, no se
  pueden borrar ni duplicar, historial al cambiar, idioma por defecto en cuentas existentes (RF-001,
  RF-012, RF-020, RF-022; CF-3).
- Panel (`test_admin.py`): solo soporte y superusuarios, edición con validación, sin añadir ni
  borrar, fallidos visibles y borrables (RF-017, RF-020, RF-021, RF-022).
- Comando (`test_command.py`): `test`, `notify` y `dispatch` (RF-009, RF-025).
- `apps/accounts`: comprobador de vigencia y copia del idioma al completar (RF-012, RF-015).
- Los RF de M-10 (RF-004, RF-005, RF-006, RF-008, RF-019) se prueban en las suites de
  `procesos-pendientes` y `cambio-contrasena`, que comprueban que cada operación deja el correo
  correcto en la bandeja.
- Mutaciones en cada tarea, como en las features anteriores.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01 | modelo |
| RF-002 | M-03, M-05 (D-01) | servicio + worker real |
| RF-003 | M-03 (D-01) | servicio |
| RF-004 | M-10, M-02 (D-09) | servicio (en `procesos-pendientes`) + unitario |
| RF-005 | M-10, M-02 (D-09) | servicio (en `cambio-contrasena`) + unitario |
| RF-006 | M-10, M-03 | servicio (en `procesos-pendientes`) |
| RF-007 | M-03, M-08 (D-11) | servicio |
| RF-008 | M-10 | servicio (en `cambio-contrasena`) |
| RF-009 | M-07 | comando |
| RF-010 | M-02 (D-08) | unitario |
| RF-011 | M-03 | servicio |
| RF-012 | M-09 (D-10) | modelo + servicio |
| RF-013 | M-03, M-09 (D-10) | servicio |
| RF-014 | M-02, M-05 (D-08) | unitario + servicio |
| RF-015 | M-05, M-09 (D-04, D-05) | servicio |
| RF-016 | M-05, M-08 (D-04) | servicio |
| RF-017 | M-01, M-05, M-06 (D-12) | servicio + panel |
| RF-018 | M-04, M-05 (D-06) | unitario + servicio |
| RF-019 | M-10 | servicio (en `procesos-pendientes` y `cambio-contrasena`) |
| RF-020 | M-01, M-06 | modelo + panel |
| RF-021 | M-02, M-06 (D-07) | unitario + panel |
| RF-022 | M-01, M-06 (D-16) | modelo + panel |
| RF-023 | M-02 (D-07) | unitario |
| RF-024 | M-05, M-08 (D-02) | servicio |
| RF-025 | M-07 | comando |
| RF-026 | M-05 (D-03) | unitario + servicio |

## RF sin cobertura
Ninguno. RF-004, RF-005, RF-006, RF-008 y RF-019 dependen de M-10, que se implementa en las tareas
de `procesos-pendientes` y `cambio-contrasena` (CF-6 de la spec); esta feature no se valida hasta
que esas tareas estén hechas.

## Límites conocidos del diseño
- Un nombre que parezca una dirección web (por ejemplo, `evil.com`) se inserta como texto, pero
  algunos clientes de correo convierten en enlace cualquier texto con forma de dirección. El sistema
  no lo marca como enlace (RF-023), pero no puede impedir lo que haga el cliente.
- Entrega al menos una vez (D-04): un correo puede llegar duplicado si el worker cae justo después
  de enviarlo.
- Con MXroute, el límite de envío por hora (S-15) se manifiesta como errores temporales: los correos
  esperan y se reintentan, en orden de llegada (S-16).
- Sin `EMAIL_CODE_KEY`, la clave se deriva de `DJANGO_SECRET_KEY`: rotar esta última invalida los
  códigos cifrados pendientes, que se descartarán como si hubieran fallado. En producción debe
  definirse aparte (`HUMAN_TODO.md`).
