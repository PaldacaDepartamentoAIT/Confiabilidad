# Spec: correo-asincrono-plantillas
Estado: borrador
Aprobación: ligera

## Objetivo (por qué)
Hoy el sistema no envía ningún correo: los códigos de registro y de restablecimiento de contraseña
solo se ven en la consola. Esta feature hace que los correos del módulo de cuentas (códigos, aviso
"ya tienes cuenta" y avisos de seguridad) lleguen al titular, en español, portugués de Brasil o
inglés, a través de un proveedor transaccional dedicado y desde una cola de tareas con reintentos.
Así la respuesta de una operación no depende de la entrega, y su tiempo no revela si un correo
tiene cuenta. Los textos se editan desde el panel de administración, con límites que impiden quitar
la forma de reportar un uso no autorizado. Depende de `infra-persistencia-y-colas` (CUMPLIDA).

## Requisitos funcionales
### RF-001 Tipos de correo
El sistema deberá tener siete tipos de correo, cada uno con asunto y cuerpo en español (`es`),
portugués de Brasil (`pt-BR`) e inglés (`en`): código de registro, código de restablecimiento de
contraseña, aviso "ya tienes cuenta", aviso de contraseña restablecida, aviso de contraseña
cambiada, aviso de cuenta deshabilitada y aviso de cierre remoto de sesiones. Los cinco avisos
(todos menos los dos de código) son avisos de seguridad.

### RF-002 Envío desde la cola
Cuando una operación provoque un correo, el sistema deberá encolarlo y terminar la operación sin
esperar a que el proveedor lo acepte. Ningún correo de esta feature se envía dentro de la operación
que lo provoca.

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
Cuando se intente empezar un registro con un correo que ya pertenece a una cuenta, el sistema deberá
enviar a ese correo un aviso que diga que alguien intentó registrarse con él, que ya tiene cuenta y
que puede iniciar sesión o restablecer su contraseña, sin código ni enlace con identificador público.

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
completarse el registro.

### RF-013 Idioma de cada correo
El sistema deberá enviar cada correo de código en el idioma de la petición que emite el código, y
cada aviso de seguridad en el idioma guardado de la cuenta, nunca en el de la petición que lo
provoca. Si la petición no indica uno de los tres idiomas, o la cuenta no tiene idioma guardado,
entonces el sistema deberá usar el idioma por defecto (S-05).

### RF-014 Plazo relativo
El sistema deberá expresar en los correos de código el plazo de vigencia en términos relativos
("el código vence en 9 minutos"), calculado en el momento en que el correo se entrega al proveedor
y no al encolarlo, y nunca como fecha u hora absoluta.

### RF-015 Reintento de los correos con código
Si el proveedor no acepta un correo de código, entonces el sistema deberá reintentarlo solo, con
esperas crecientes, mientras el código siga vigente. Si el código caduca, se valida o se reemplaza
por otro antes de que el proveedor acepte el correo, entonces el sistema deberá descartarlo sin
enviarlo.

### RF-016 Reintento de los avisos
Si el proveedor no acepta un aviso de seguridad, entonces el sistema deberá reintentarlo solo, con
esperas crecientes, durante la ventana configurada (24 horas por defecto).

### RF-017 Registro de los correos fallidos
Cuando se agoten los reintentos de un correo, el sistema deberá registrar su tipo, idioma,
destinatario, fecha de encolado, número de intentos y el último error del proveedor, sin el código,
y mostrarlo en el panel de administración a los miembros de «Soporte técnico».

### RF-018 Código en claro
El sistema no deberá guardar el código en claro en la base de datos, en el registro de fallos ni en
los registros de actividad, y deberá dejar de conservarlo en cuanto su correo se entregue, se
descarte o se agoten sus reintentos.

### RF-019 Mismo trabajo exista o no la cuenta
Cuando se empiece un registro o se pida un restablecimiento de contraseña, el sistema deberá hacer
fuera de la respuesta todo el trabajo que depende de que el correo tenga una cuenta elegible (buscar
la cuenta, crear o reemplazar el proceso, emitir el código y decidir qué correo se envía). Si se
pide un restablecimiento para un correo sin cuenta o con la cuenta inactiva, entonces el sistema no
deberá enviar ningún correo.

### RF-020 Edición desde el panel
El sistema deberá permitir a los miembros de «Soporte técnico» editar desde el panel de
administración el asunto y el cuerpo de cada tipo de correo en cada idioma, y deberá conservar el
historial de cada cambio: quién, cuándo y el texto anterior.

### RF-021 Validación de las plantillas
Si al guardar una plantilla falta alguno de los datos obligatorios de su tipo (el código, el enlace
y el plazo en los correos de código), aparece un dato que su tipo no admite o contiene un enlace a
un dominio distinto del de la aplicación configurado, entonces el sistema deberá rechazarla
indicando cada problema y conservar la versión anterior.

### RF-022 Plantillas iniciales y completas
El sistema deberá incluir desde su instalación un texto para cada tipo de correo en los tres
idiomas, y deberá impedir borrar cualquiera de ellos.

### RF-023 Nombres en los correos
El sistema deberá mostrar en asunto y cuerpo el nombre de la persona con sus caracteres Unicode
exactos (acentos, alfabetos no latinos, emojis), siempre como texto: nunca se interpreta como
formato ni como enlace.

### RF-024 Proveedor transaccional
El sistema deberá enviar todos los correos de esta feature a través de un único proveedor
transaccional dedicado, con el remitente y las credenciales configurables por entorno. En
desarrollo y en los tests deberá poder usarse un proveedor local o simulado, sin enviar correos
reales.

### RF-025 Correo de prueba desde consola
El sistema deberá permitir encolar desde consola un correo de prueba de cualquier tipo e idioma a
una dirección indicada, con datos de ejemplo, para comprobar el proveedor real.

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
- S-05 **Pendiente de confirmar en la clarificación:** el idioma por defecto es español, también
  para las cuentas existentes, que no tienen idioma guardado.
- S-06 Restablecimiento sin cuenta elegible: el mismo trabajo y ningún correo (pregunta 5). El
  mensaje de respuesta neutro de la futura API sigue pendiente en `HUMAN_TODO.md`.
- S-07 **Conflicto a resolver en la clarificación:** RF-019 cambia el comportamiento de dos features
  aprobadas. Hoy, empezar un registro devuelve al momento "cuenta existente" o el identificador
  público y el código (`procesos-pendientes`), y pedir un restablecimiento devuelve al momento "sin
  cuenta elegible" (RF-004 y RF-013 de `cambio-contrasena`). Si ese trabajo sale de la respuesta,
  la respuesta ya no puede saber ese resultado. Hay que decidir qué devuelven la operación y los
  comandos de consola; probablemente haga falta `sdd-cambio` sobre esas dos features.
- S-08 **Conflicto a resolver en la clarificación:** reintentar un correo de código (RF-015) exige
  conservar el código en claro hasta entregarlo, y RF-008 de `procesos-pendientes` dice que el
  código se guarda solo como huella. RF-018 acota dónde y cuánto tiempo puede estar en claro, pero
  la cola guarda el correo pendiente fuera de la base de datos, y hay que confirmar que eso es
  aceptable.
- S-09 Tope de un aviso "ya tienes cuenta" por cuenta y ventana (pregunta 6). Los avisos de hechos
  reales nunca se descartan.
- S-10 La forma de reportar es una dirección de soporte configurable, más la recomendación de
  restablecer la contraseña (pregunta 7). El reporte lo atiende una persona.
- S-11 La feature está terminada cuando los tests demuestran, con un proveedor simulado que falla a
  voluntad, que todo sale de la cola y se reintenta solo (pregunta 8). La cuenta del proveedor, sus
  credenciales y SPF, DKIM y DMARC del dominio remitente quedan en `HUMAN_TODO.md`.
- S-12 El enlace con el identificador público apunta a una dirección del frontend configurable por
  entorno; las pantallas que lo reciben llegarán con su propia feature.
- S-13 Los correos son de texto plano. *Por qué:* es lo más seguro de editar desde el panel y lo que
  mejor se entrega; si hace falta HTML, se añade con `sdd-cambio`.
- S-14 Los comandos de consola de registro y restablecimiento siguen mostrando el código en claro
  (S-06 de `cambio-contrasena`), además de enviarlo por correo, salvo que la clarificación de S-07
  diga otra cosa.
- S-15 La elección del proveedor es un servicio nuevo: se decide en el plan, con aprobación
  explícita del usuario (`AGENTS.md`).

## Fuera de alcance
- Las acciones de cerrar sesiones de forma remota, deshabilitar la cuenta por su titular y cambiar
  la contraseña con la sesión iniciada (S-01).
- API y pantallas, incluido el mensaje de respuesta neutro de la API (S-06).
- Límites de frecuencia de pedir y reenviar códigos (pendientes en `HUMAN_TODO.md`).
- Contratar el proveedor y configurar SPF, DKIM y DMARC (S-11; checklist humano).
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
- CF-4 `HUMAN_TODO.md` incluye: contratar el proveedor, guardar sus credenciales cifradas con SOPS,
  configurar SPF, DKIM y DMARC del dominio remitente, y el comando de RF-025 para enviar un correo
  real de prueba.
- CF-5 `resumen.md` explica cómo provocar desde consola cada tipo de correo y cómo ver un fallo
  reintentado con el proveedor simulado.

## Historial de cambios
- 2026-10-14 — Creación (feature nueva) — RF: RF-001…RF-025 — Estado: pendiente de clarificar
