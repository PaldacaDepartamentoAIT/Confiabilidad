# Spec: correo-asincrono-plantillas
Estado: borrador
Aprobación: ligera

## Objetivo (por qué)
Hoy el sistema no envía ningún correo: los códigos de registro y de restablecimiento de contraseña
solo se ven en la consola. Esta feature hace que los correos del módulo de cuentas (códigos, aviso
"ya tienes cuenta" y avisos de seguridad) lleguen al titular, en español, portugués de Brasil o
inglés, a través de un proveedor de envío configurable e intercambiable y desde una cola de tareas
con reintentos. Así la respuesta de una operación no depende de la entrega, y su tiempo no revela
si un correo tiene cuenta. Los textos se editan desde el panel de administración, con límites que
impiden quitar la forma de reportar un uso no autorizado. Depende de `infra-persistencia-y-colas`
(CUMPLIDA).

## Requisitos funcionales
### RF-001 Tipos de correo
El sistema deberá tener siete tipos de correo, cada uno con asunto y cuerpo en español (`es`),
portugués de Brasil (`pt-BR`) e inglés (`en`): código de registro, código de restablecimiento de
contraseña, aviso "ya tienes cuenta", aviso de contraseña restablecida, aviso de contraseña
cambiada, aviso de cuenta deshabilitada y aviso de cierre remoto de sesiones. Los cinco avisos
(todos menos los dos de código) son avisos de seguridad.

### RF-002 Envío desde la cola
Cuando una operación provoque un correo, el sistema deberá guardarlo en una bandeja de salida en la
base de datos, dentro de esa misma operación, y terminarla sin esperar a que el proveedor lo acepte.
La entrega al proveedor se hace desde la cola de tareas, nunca dentro de la operación. Si la cola no
está disponible, el correo espera en la bandeja y se encola cuando vuelva a estarlo.

### RF-003 Solo operaciones confirmadas
Si la operación que provoca un correo falla o se deshace, entonces el sistema no deberá enviarlo.

### RF-004 Correo con el código de registro
Cuando se emita un código de registro (al empezar el registro o al reenviar el código), el sistema
deberá enviar al correo del registro pendiente un correo con el nombre de la persona, el código, el
plazo de vigencia que le queda (RF-014) y un enlace que contiene el identificador público del
registro para retomarlo.

### RF-005 Correo con el código de restablecimiento
Cuando se emita un código de restablecimiento de contraseña (al pedirlo o al reenviarlo), el sistema
deberá enviar al correo de la cuenta un correo con el nombre del titular, el código, el plazo de
vigencia que le queda (RF-014) y un enlace que contiene el identificador público de la solicitud
para retomarla.

### RF-006 Aviso "ya tienes cuenta"
Cuando se intente empezar un registro con un correo que ya pertenece a una cuenta activa, el sistema
deberá enviar a ese correo un aviso que diga que alguien intentó registrarse con él, que ya tiene
cuenta y que puede iniciar sesión o restablecer su contraseña, sin código ni enlace con
identificador público. Si la cuenta está deshabilitada, entonces el sistema no deberá enviar ningún
correo.

### RF-007 Tope del aviso "ya tienes cuenta"
Si una cuenta ya recibió un aviso "ya tienes cuenta" dentro de la ventana configurada (1 hora por
defecto), entonces el sistema no deberá enviarle otro. El resultado de la operación que lo provocó
no cambia. El tope no se aplica a ningún otro tipo de correo.

### RF-008 Aviso de contraseña restablecida
Cuando se complete un restablecimiento de contraseña, el sistema deberá enviar al correo de la
cuenta el aviso de contraseña restablecida.

### RF-009 Avisos sin acción que los provoque
El sistema deberá permitir enviar desde consola, a una cuenta indicada, los avisos de contraseña
cambiada, cuenta deshabilitada y cierre remoto de sesiones, por el mismo camino que cualquier otro
correo (RF-002). Las features que implementen esas acciones los usarán.

### RF-010 Bloque de reporte en los avisos de seguridad
El sistema deberá incluir en cada aviso de seguridad, después del texto editable, un bloque fijo en
el idioma del aviso que indique qué hacer si no fue el titular: escribir a la dirección de soporte
configurada y restablecer su contraseña. Ese bloque no se puede editar desde el panel.

### RF-011 Avisos de seguridad no desactivables
El sistema no deberá ofrecer ninguna forma de dejar de recibir los avisos de seguridad: ni
preferencia de la cuenta ni enlace para darse de baja.

### RF-012 Idioma guardado
El sistema deberá guardar un idioma (`es`, `pt-BR` o `en`) en cada registro pendiente y en cada
cuenta. El registro pendiente toma el idioma de la petición que lo empieza, y la cuenta lo hereda al
completarse el registro. Las cuentas que ya existen antes de esta feature quedan con el idioma por
defecto (español).

### RF-013 Idioma de cada correo
El sistema deberá enviar cada correo de código en el idioma de la petición que emite el código, y
cada aviso de seguridad en el idioma guardado de la cuenta, nunca en el de la petición que lo
provoca. Si la petición no indica uno de los tres idiomas, o la cuenta no tiene idioma guardado,
entonces el sistema deberá usar el idioma por defecto, español.

### RF-014 Plazo relativo
El sistema deberá expresar en los correos de código el plazo de vigencia en minutos enteros
redondeados hacia abajo ("el código vence en 9 minutos" si quedan 9 minutos y 40 segundos),
calculado en el momento en que el correo se entrega al proveedor y no al encolarlo. Si queda menos
de un minuto, deberá decir que vence en menos de un minuto. Nunca deberá expresarlo como fecha u
hora absoluta.

### RF-015 Reintento de los correos con código
Si el proveedor rechaza de forma temporal un correo de código (RF-026), entonces el sistema deberá
reintentarlo solo, con esperas crecientes, mientras el código siga vigente. Si el código caduca, se
valida o se reemplaza por otro antes de que el proveedor acepte el correo, entonces el sistema
deberá descartarlo sin enviarlo.

### RF-016 Reintento de los avisos
Si el proveedor rechaza de forma temporal un aviso de seguridad (RF-026), entonces el sistema deberá
reintentarlo solo, con esperas crecientes, durante la ventana configurada (24 horas por defecto).

### RF-017 Registro de los correos fallidos
Cuando se agoten los reintentos de un correo, o el proveedor lo rechace de forma definitiva
(RF-026), el sistema deberá registrar su tipo, idioma, destinatario, fecha de encolado, número de
intentos y el último error del proveedor, sin el código, y mostrarlo en el panel de administración a
los miembros de «Soporte técnico», que podrán borrarlo. El registro se conserva hasta que lo borren.

### RF-018 Código en claro
El sistema deberá guardar el código de un correo pendiente solo cifrado con una clave propia,
distinta de la que protege las huellas de los códigos, y deberá borrarlo en cuanto su correo se
entregue, se descarte o falle de forma definitiva. El código nunca deberá aparecer en claro en la
base de datos, en el registro de fallos ni en los registros de actividad.

### RF-019 Mismo trabajo exista o no la cuenta
Cuando se empiece un registro o se pida un restablecimiento de contraseña, el sistema deberá
devolver siempre un identificador público con el mismo formato, tenga o no una cuenta el correo, y
hacer fuera de la respuesta todo el trabajo que depende de que la tenga (buscar la cuenta, crear o
reemplazar el proceso, emitir el código y decidir qué correo se envía). Los comandos de consola de
esas dos operaciones solo mostrarán ese identificador. Si se pide un restablecimiento para un correo
sin cuenta o con la cuenta inactiva, entonces el sistema no deberá enviar ningún correo, y el
identificador devuelto deberá responder al verificarlo, reenviarlo o completarlo igual que el de un
proceso real con un código incorrecto.

### RF-020 Edición desde el panel
El sistema deberá permitir a los miembros de «Soporte técnico» editar desde el panel de
administración el asunto y el cuerpo de cada tipo de correo en cada idioma, y deberá conservar el
historial de cada cambio: quién, cuándo y el texto anterior.

### RF-021 Validación de las plantillas
Si al guardar una plantilla falta alguno de los datos obligatorios de su tipo (el código, el enlace
y el plazo en los correos de código), aparece un dato que su tipo no admite, contiene un enlace a
un dominio distinto del de la aplicación configurado o su asunto contiene un salto de línea,
entonces el sistema deberá rechazarla indicando cada problema y conservar la versión anterior.

### RF-022 Plantillas iniciales y completas
El sistema deberá incluir desde su instalación un texto para cada tipo de correo en los tres
idiomas, y deberá impedir borrar cualquiera de ellos.

### RF-023 Nombres en los correos
El sistema deberá mostrar en asunto y cuerpo el nombre de la persona con sus caracteres Unicode
exactos (acentos, alfabetos no latinos, emojis), siempre como texto: nunca se interpreta como
formato ni como enlace.

### RF-024 Proveedor de envío
El sistema deberá enviar todos los correos de esta feature a través de un único proveedor de envío
configurable por entorno (servidor, credenciales y remitente), que se pueda sustituir por otro sin
cambiar el código. En desarrollo y en los tests deberá poder usarse un proveedor local o simulado,
sin enviar correos reales.

### RF-025 Correo de prueba desde consola
El sistema deberá permitir encolar desde consola un correo de prueba de cualquier tipo e idioma a
una dirección indicada, con datos de ejemplo, para comprobar el proveedor real.

### RF-026 Errores temporales y definitivos
El sistema deberá distinguir los rechazos temporales del proveedor (por ejemplo, límite de envío
superado o servidor no disponible), que se reintentan según RF-015 y RF-016, de los definitivos
(por ejemplo, buzón inexistente), que no se reintentan y se registran al momento (RF-017).

## Supuestos
- S-01 Los avisos de cierre remoto de sesiones y de cuenta deshabilitada quedan listos sin la acción
  que los provoca (pregunta 1). El de contraseña cambiada se trata igual: el cambio de contraseña con
  la sesión iniciada tampoco existe (fuera de alcance de `cambio-contrasena`).
- S-02 Idioma guardado en la cuenta (pregunta 2). *Por qué:* el aviso "ya tienes cuenta" lo provoca
  quien intenta registrarse, que puede ser un atacante, y no debe decidir el idioma en que el titular
  recibe su aviso.
- S-03 Los correos de código solo se reintentan mientras sirven; los avisos, durante 24 horas; los
  fallos definitivos quedan en el panel (pregunta 3). *Por qué:* un código entregado después de
  caducar no sirve, y un plazo calculado al encolar mentiría tras un retraso.
- S-04 Edición con red de seguridad (pregunta 4): solo «Soporte técnico», con validación, historial
  y bloque de reporte fijo. *Por qué:* un correo de seguridad sale del dominio legítimo con SPF, DKIM
  y DMARC válidos; si alguien con acceso al panel le quitara el bloque de reporte o le pusiera un
  enlace malicioso, llegaría como auténtico.
- S-05 El idioma por defecto es español, también para las cuentas existentes (C-04).
- S-06 Restablecimiento sin cuenta elegible: el mismo trabajo y ningún correo (pregunta 5). El
  mensaje de respuesta neutro de la futura API sigue pendiente en `HUMAN_TODO.md`.
- S-07 Empezar un registro y pedir un restablecimiento devuelven siempre un identificador público
  (C-01). Esto cambia lo aprobado en `procesos-pendientes` (el resultado de empezar el registro,
  RF-008 sobre el código y sus comandos) y en `cambio-contrasena` (RF-004 y RF-013). Antes de
  implementar las tareas que los toquen, se pasa `sdd-cambio` por esas dos features (CF-6). La
  neutralidad del identificador de un proceso inexistente (RF-019) es consecuencia directa: sin
  ella, verificarlo revelaría si la cuenta existe.
- S-08 El código de un correo pendiente se guarda cifrado en la bandeja (C-02, C-03). *Por qué:* la
  bandeja hace que ningún correo se pierda si la cola cae, y el cifrado evita que leer la base de
  datos baste para usar un código en curso. *Coste:* una clave más, cifrada con SOPS, y una copia
  cifrada del código que hoy RF-008 de `procesos-pendientes` no admite.
- S-09 Tope de un aviso "ya tienes cuenta" por cuenta y ventana (pregunta 6). Los avisos de hechos
  reales nunca se descartan.
- S-10 La forma de reportar es una dirección de soporte configurable, más la recomendación de
  restablecer la contraseña (pregunta 7). El reporte lo atiende una persona.
- S-11 La feature está terminada cuando los tests demuestran, con un proveedor simulado que falla a
  voluntad, que todo sale de la cola y se reintenta solo (pregunta 8). La configuración real del
  proveedor y del DNS queda en `HUMAN_TODO.md`.
- S-12 El enlace con el identificador público apunta a una dirección del frontend configurable por
  entorno; las pantallas que lo reciben llegarán con su propia feature.
- S-13 Los correos son de texto plano. *Por qué:* es lo más seguro de editar desde el panel y lo que
  mejor se entrega; si hace falta HTML, se añade con `sdd-cambio`.
- S-14 Los comandos de consola de registro y restablecimiento dejan de mostrar el código y el
  resultado (C-01). En desarrollo, el proveedor local muestra el correo completo, código incluido,
  en la salida del worker.
- S-15 El proveedor inicial es MXroute por SMTP, y se envía desde un buzón propio en el subdominio
  `notificaciones.` del dominio. La decisión se formaliza en el plan. Su límite (400 correos por
  hora y por dirección, según su documentación) y su política sobre correo automático se confirman
  con su soporte. La configuración de DNS y la migración a un proveedor transaccional están en
  `HUMAN_TODO.md`.
- S-16 Los correos salen en orden de llegada, sin prioridades (C-06). Riesgo aceptado: si se alcanza
  el límite por hora del proveedor, una oleada de avisos puede hacer que caduquen códigos
  pendientes.
- S-17 Los 21 textos iniciales los redacta la implementación y se revisan en el PR (C-07).
- S-18 El registro de fallos se conserva hasta que soporte lo borre (C-08). Riesgo aceptado: acumula
  correos de destinatarios sin límite de tiempo.

## Fuera de alcance
- Las acciones de cerrar sesiones de forma remota, deshabilitar la cuenta por su titular y cambiar
  la contraseña con la sesión iniciada (S-01).
- API y pantallas, incluido el mensaje de respuesta neutro de la API (S-06).
- Límites de frecuencia de pedir y reenviar códigos (pendientes en `HUMAN_TODO.md`).
- Configurar el buzón de MXroute y SPF, DKIM y DMARC en Cloudflare (S-11 y S-15; checklist humano en
  `HUMAN_TODO.md`).
- Correos de marketing, boletines y cualquier correo fuera del módulo de cuentas.
- Seguimiento de entregas, aperturas y rebotes informados por el proveedor.
- Correos en HTML (S-13).

## Criterios de finalización
- CF-1 Con un proveedor simulado que falla a voluntad, los tests demuestran que cada tipo de correo
  sale de la cola y no de la operación, que un fallo se reintenta solo hasta entregarse, que un
  correo de código caducado o reemplazado se descarta y que un fallo definitivo queda registrado
  (RF-002, RF-015, RF-016, RF-017).
- CF-2 Hay tests para cada RF; la suite `pytest` está en verde con cobertura ≥ 80 % y
  `mypy`/`ruff`/`black` están limpios.
- CF-3 Tras migrar sobre la última migración de `main`, existen las plantillas de los siete tipos en
  los tres idiomas.
- CF-4 `HUMAN_TODO.md` incluye: la guía de MXroute y Cloudflare (subdominio, buzón, SPF, DKIM y
  DMARC), guardar con SOPS las credenciales SMTP y la clave de cifrado de los códigos de la bandeja,
  y el comando de RF-025 para enviar un correo real de prueba.
- CF-5 `resumen.md` explica cómo provocar desde consola cada tipo de correo y cómo ver un fallo
  reintentado con el proveedor simulado, y recoge la configuración completa del envío (subdominio y
  buzón de MXroute, registros DNS de Cloudflare, variables de entorno y su lugar en SOPS) para poder
  rehacerla o cambiar de proveedor más adelante.
- CF-6 Antes de implementar las tareas que cambian el registro y el restablecimiento,
  `procesos-pendientes` y `cambio-contrasena` tienen aprobado su `sdd-cambio` (S-07).

## Historial de cambios
- 2026-10-14 — Creación (feature nueva) — RF: RF-001…RF-025 — Estado: pendiente de clarificar
- 2026-10-14 — Clarificación (C-01…C-09 y proveedor MXroute) — RF: RF-002, RF-006, RF-012, RF-013,
  RF-014, RF-015, RF-016, RF-017, RF-018, RF-019 y RF-024 ajustados; RF-026 añadido; S-05, S-07,
  S-08, S-11, S-14 y S-15 ajustados; S-16…S-18 añadidos; CF-4 y CF-5 ajustados; CF-6 añadido —
  Estado: clarificado
- 2026-10-14 — Aprobación por el usuario (commit `b49760d`; entrada añadida el 2026-10-15, tras la
  validación) — Estado: aprobada
- 2026-10-15 — Cambio tras la 2.ª validación: el asunto no admite saltos de línea — RF: RF-021
  modificado. Clarificado sin dudas nuevas: un salto de línea es `\n` o `\r`, los que una cabecera
  de correo no admite; el cuerpo los sigue admitiendo — Estado: impacto analizado
