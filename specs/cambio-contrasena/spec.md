# Spec: cambio-contrasena
Estado: aprobada
Aprobación: ligera

## Objetivo (por qué)
Quien ha olvidado su contraseña debe poder fijar una nueva demostrando acceso al correo de su
cuenta con un código. Esta feature guarda las solicitudes de cambio de contraseña (la tabla
`PasswordResetRequest` del diagrama ER), les aplica las mismas reglas de código que al registro
pendiente y permite recorrer el proceso desde consola. Se separó de `procesos-pendientes` el
2026-10-01 y reutiliza su mecanismo (S-11 de esa feature). Los diagramas del usuario son la
referencia: [flujo de cambio de contraseña](../procesos-pendientes/diagramas/flujo-cambio-contrasena.png)
y [ER](../procesos-pendientes/diagramas/er.png), con las desviaciones de S-02.

## Secuencia del cambio de contraseña
1. La persona indica su correo.
2. La persona recibe al momento un identificador público. Fuera de la respuesta, si el correo
   tiene una cuenta activa, se crea o se reemplaza su solicitud con ese identificador y se emite un
   código, que le llega por correo (RF-002, RF-003, RF-016). Si no, el identificador no tiene
   solicitud detrás y no se envía ningún correo (RF-004, RF-017).
3. La persona introduce el código, que queda validado (RF-005).
4. La persona introduce su nueva contraseña.
5. Se fija la contraseña, se marca su correo como verificado, se borran sus contadores de inicios
   de sesión fallidos y se borra la solicitud (RF-009).

En este documento, "RF-0xx de `procesos-pendientes`" remite a
[su spec](../procesos-pendientes/spec.md); los RF sin esa mención son de esta feature.

## Requisitos funcionales
### RF-001 Solicitud de cambio de contraseña
El sistema deberá guardar, para cada solicitud de cambio de contraseña, la cuenta a la que
pertenece, un identificador público, la huella del código vigente, su caducidad, el número de
intentos fallidos, si el código ya se validó (y cuándo), la fecha de alta y lo necesario para
saber si el correo o la contraseña de la cuenta han cambiado desde que se pidió (RF-014, RF-015),
con un máximo de una solicitud por cuenta, garantizado también en cargas masivas y escrituras
directas a la base de datos.

### RF-002 Pedir el cambio
Cuando se pida el cambio de contraseña con un correo que coincide, sin distinguir mayúsculas ni
espacios al principio o al final, con el de una cuenta activa sin solicitud, el sistema deberá
crear, fuera de la respuesta (RF-016), una solicitud para esa cuenta con el identificador público
devuelto, aleatorio, imposible de deducir del correo o de la cuenta, y único entre las solicitudes
(RF-007 de `procesos-pendientes`), y emitir un código (RF-005).

### RF-003 Solicitud repetida
Cuando se pida el cambio de contraseña para una cuenta activa que ya tiene una solicitud, vigente
o caducada, el sistema deberá reemplazarla: identificador público nuevo, código nuevo, intentos a
0, código sin validar, vida contada de nuevo desde ese momento y, como referencia para RF-014 y
RF-015, el correo y la contraseña que la cuenta tiene en ese momento.

### RF-004 Sin cuenta elegible
Si se pide el cambio de contraseña con un correo que no corresponde a ninguna cuenta, o cuya
cuenta está inactiva, entonces el sistema deberá devolver un identificador sin solicitud detrás
(RF-017), sin crear, modificar ni borrar ninguna solicitud y sin enviar ningún correo. La respuesta
no deberá distinguir este caso del de una cuenta elegible.

### RF-005 Código y verificación
El sistema deberá aplicar a cada solicitud las reglas del código de `procesos-pendientes`:
6 dígitos vigentes 15 minutos por defecto, entregados una sola vez y guardados solo como huella
(RF-008); verificación con suma de intentos fallidos y rechazo de cualquier código una vez
validado (RF-009); bloqueo al alcanzar el máximo de intentos fallidos, 5 por defecto, hasta que se
emita un código nuevo (RF-010); y aceptación durante el periodo de transición de los códigos
emitidos con el secreto anterior (RF-015). Un identificador público de un registro pendiente,
tenga o no registro detrás, no deberá servir como identificador de una solicitud, ni a la inversa.

### RF-006 Caducidad de la solicitud
Una solicitud caduca al cumplirse lo primero de: 15 minutos después de que caduque su código
vigente, o 1 hora desde su alta (valores por defecto, RF-012). Mientras una solicitud esté
caducada, el sistema deberá rechazar sus códigos, impedir que se complete y rechazar su reenvío.

### RF-007 Reenvío del código
Cuando se reenvíe el código de una solicitud vigente sin el código validado, el sistema deberá
conservar su identificador público, poner los intentos a 0 y responder de inmediato, y emitir el
código nuevo, con su correo, fuera de la respuesta. Si la solicitud ya tiene el código validado,
entonces el sistema deberá rechazar el reenvío.

### RF-008 Cuenta inactiva con una solicitud en curso
Mientras la cuenta de una solicitud esté inactiva, el sistema deberá responder a la verificación
de su código, su reenvío y su compleción como si la solicitud hubiera caducado (RF-006), sin
modificarla; la solicitud se conserva hasta caducar.
Si la cuenta se reactiva antes de que la solicitud caduque, la solicitud vuelve a admitir esas
operaciones.

### RF-009 Completar el cambio de contraseña
Cuando se complete una solicitud vigente con el código validado y una contraseña, el sistema
deberá, en una sola operación, fijar esa contraseña en la cuenta, marcar como verificada la
dirección de correo de la cuenta (creándola si no existe, como principal si la cuenta no tiene
otra principal), borrar el contador de inicios de sesión fallidos por correo que lleva allauth
para el correo de la cuenta (el contador por IP no cambia), borrar la solicitud y dejar en la
bandeja de salida el aviso de contraseña restablecida (RF-008 de `correo-asincrono-plantillas`).
Una contraseña
igual a la actual se acepta si cumple la política. Si la contraseña no cumple la política de
RF-022 de `procesos-pendientes`, evaluada con el correo y el nombre de la cuenta, entonces el
sistema deberá rechazarlo indicando cada regla incumplida y conservar la solicitud. Si la
solicitud no tiene el código validado o está caducada, entonces el sistema deberá rechazarlo sin
cambiar la contraseña.

### RF-010 Borrado de la cuenta
Cuando se borre físicamente una cuenta, el sistema deberá borrar su solicitud de cambio de
contraseña, y su identificador deberá responder como el de una solicitud caducada (RF-006) hasta el
momento en que la solicitud habría caducado.

### RF-011 Limpieza
El sistema deberá permitir borrar desde consola todas las solicitudes caducadas, informando de
cuántas borró, con una orden propia de esta feature que no borra registros pendientes.

### RF-012 Límites compartidos con el registro
El sistema deberá aplicar a las solicitudes los mismos valores configurables que al registro
pendiente (RF-019 de `procesos-pendientes`): máximo de intentos fallidos, vigencia del código,
gracia tras caducar el código, vida máxima del proceso, periodo de transición del secreto y tiempo
de reintento del trabajo de fuera de la respuesta.
Cambiar uno de esos valores afecta a ambos procesos.

### RF-013 Ejecución desde consola
El sistema deberá permitir recorrer desde consola cada paso del cambio de contraseña, sin
frontend ni API: pedirlo con un correo, presentar el código, reenviarlo, completarlo con una
contraseña (que se pide sin mostrarla en pantalla si no se indica) y purgar las caducadas
(RF-011). Cada paso deberá mostrar el identificador público y el resultado de la operación, igual
haya o no cuenta elegible (RF-004, RF-017); nunca el código.

### RF-014 Correo cambiado tras la solicitud
Si el correo de la cuenta ya no coincide, sin distinguir mayúsculas, con aquel al que se envió el
código de su solicitud, entonces el sistema deberá responder a la verificación del código, su
reenvío y la compleción como si la solicitud hubiera caducado (RF-006), sin modificarla; la
solicitud se conserva hasta caducar o hasta reemplazarse (RF-003).

### RF-015 Contraseña cambiada tras la solicitud
Si la contraseña de la cuenta ha cambiado por cualquier otra vía desde que se pidió la solicitud o
desde su último reemplazo (RF-003), entonces el sistema deberá responder a la verificación del
código, su reenvío y la compleción como si la solicitud hubiera caducado (RF-006), sin modificarla;
la solicitud se conserva hasta caducar o hasta reemplazarse.

### RF-016 Pedir el cambio sin revelar la cuenta
Cuando se pida el cambio de contraseña, el sistema deberá devolver de inmediato un identificador
público nuevo, con el mismo formato haya o no cuenta elegible, y hacer fuera de la respuesta todo
el trabajo que depende de ello: buscar la cuenta, crear o reemplazar la solicitud con ese
identificador y emitir el código. Si el formato del correo no es válido, entonces el sistema deberá
rechazarlo en la propia respuesta. Si el trabajo de fuera de la respuesta falla, entonces el
sistema deberá reintentarlo solo durante el tiempo configurado (RF-012). Si sigue fallando, el
identificador se comportará como uno sin solicitud detrás (RF-017), sin enviar correo, y el fallo
quedará en el registro de eventos del servidor.

### RF-017 Identificador sin solicitud detrás
Verificar, reenviar, completar y dejar caducar un identificador sin solicitud detrás deberá dar los
mismos resultados, en el mismo orden y con los mismos plazos, que una solicitud real cuyo código
nunca se acierta, incluido el bloqueo por intentos. El trabajo que distinga uno de otro (emitir el
código y enviar el correo) se hará fuera de la respuesta. Una petición nueva con el mismo correo
anula el identificador sin solicitud anterior, igual que RF-003 con una solicitud real.

## Supuestos
- S-01 Esta feature no incluye API, pantallas, el mensaje neutro "Si existe una cuenta, recibirás
  un código", el límite de frecuencia (S-05) ni el cierre de sesiones (S-03). Los correos, incluido
  el aviso del cambio, los envía `correo-asincrono-plantillas`. El resultado y el tiempo de
  respuesta ya no distinguen si hay cuenta elegible (RF-016, RF-017, cambio del 2026-10-14). La API
  será otra feature, reutilizará las mismas operaciones que los comandos de RF-013 y solo le faltará
  el mensaje neutro.
- S-02 Desviaciones respecto al diagrama ER: la solicitud no tiene `used_at` porque se borra al
  completarse (S-11 de `procesos-pendientes` prevalece sobre el diagrama; pregunta 1); hay como
  máximo una solicitud por cuenta, aunque el diagrama dibuja "cero o muchas" (S-11); y se añaden la
  marca de código validado y su fecha, que exigen RF-005 y RF-007, y la referencia al correo y a la
  contraseña de la cuenta que exigen RF-014 y RF-015; el diagrama no tiene ninguna de las dos.
- S-03 Hallazgo comprobado el 2026-10-09 con un test exploratorio: tras fijar la contraseña y
  guardar la cuenta, la siguiente petición con la cookie de sesión del navegador o con el
  `X-Session-Token` de allauth headless recibe 401. La sesión guarda una huella derivada del hash
  de la contraseña y deja de valer al cambiarla. Las sesiones **no se borran**: siguen almacenadas
  hasta caducar, inservibles. Un test lo dejará fijado (CF-3). Borrarlas, y avisar del cambio por
  correo, es del flujo.
- S-04 Decisiones heredadas de S-11 de `procesos-pendientes`, no reabiertas: una solicitud por
  cuenta que se reemplaza al pedir otra (RF-001, RF-003; antes RF-006); borrado al completar o
  caducar (RF-009, RF-011); borrado al borrar la cuenta (RF-010; antes RF-014); una cuenta inactiva
  no puede pedirla y la que tenga en curso muere al caducar (RF-004, RF-008; C-05, antes RF-018);
  completar fija la contraseña con la política de RF-022 y borra la solicitud (RF-009; antes
  RF-021).
- S-05 Un código de 6 dígitos con 5 intentos por código no frena la fuerza bruta: pedir de nuevo
  (RF-003) y reenviar (RF-007) ponen los intentos a 0. Aquí el riesgo es mayor que en el registro,
  porque cualquiera puede pedir el cambio para el correo de otra persona: sin límite de frecuencia,
  unas 200.000 rondas de 5 intentos bastan de media para acertar y tomar la cuenta. Queda fuera de
  alcance (pregunta 4) y se anota en `HUMAN_TODO.md` como bloqueante para publicar la API.
- S-06 Los comandos de RF-013 ya no muestran el código (cambio del 2026-10-14), por el mismo motivo
  que S-10 de `procesos-pendientes`: la API reutilizará las mismas operaciones. En desarrollo, el
  código se lee en el correo que muestra el proveedor local en la salida del worker.
- S-07 Cualquier cuenta activa puede pedir el cambio, también una con el correo sin verificar, una
  sin contraseña utilizable o una de staff o superusuario (confirmado en C-03); al completarlo
  queda con la contraseña indicada y el correo verificado.
- S-08 Marcar el correo como verificado al completar (RF-009) se decidió en la pregunta 6:
  completar demuestra el acceso al correo, igual que en el cambio de contraseña por código de
  allauth. Hoy no afecta al inicio de sesión (`ACCOUNT_EMAIL_VERIFICATION = "none"`).
- S-09 Fijar una contraseña igual a la actual se permite (pregunta 7): la política de RF-022 es la
  misma en todo el proyecto.
- S-10 Los límites son los del registro (pregunta 8). Si algún día hacen falta valores propios, se
  separan con `sdd-cambio`.
- S-11 Una solicitud deja de servir si, después de pedirla, cambia el correo de la cuenta (RF-014,
  C-01) o su contraseña (RF-015, C-02). *Por qué:* el código demostró el acceso a un correo
  concreto; si la cuenta ya tiene otro, completar verificaría un correo que nunca lo recibió, y un
  administrador que cambia el correo o la contraseña para cortar un acceso no debe ver su cambio
  pisado por una solicitud anterior. *Coste:* quien tenga una solicitud en curso cuando eso ocurra
  debe pedir otra.
- S-12 Borrar al completar el contador de inicios de sesión fallidos por correo (RF-009, C-04) evita
  que quien acaba de cambiar su contraseña siga bloqueado hasta 5 minutos por los fallos previos;
  allauth hace lo mismo en su propio cambio de contraseña. El contador por IP no se toca: no es de
  la cuenta.
- S-13 Responder como caducada cuando la cuenta se deshabilita, se borra o cambia de correo o
  contraseña (RF-008, RF-010, RF-014, RF-015) evita revelar qué pasó (C-01 del cambio del
  2026-10-14). *Riesgo aceptado:* quien tenga el identificador puede notar que caducó antes de
  tiempo, o que revive al reactivarse la cuenta, y deducir así que el correo tenía cuenta. Solo
  ocurre si el titular o soporte actúan sobre la cuenta durante la vida de la solicitud.

## Fuera de alcance
- API, pantallas y mensaje neutro (S-01). El envío de correos es de `correo-asincrono-plantillas`.
- Límite de frecuencia de pedir y reenviar (S-05).
- Cierre o borrado de las sesiones abiertas (S-03). El aviso del cambio por correo es de
  `correo-asincrono-plantillas`.
- Cambiar la contraseña conociendo la actual, con la sesión iniciada.
- Auditoría de los cambios de contraseña: las solicitudes terminadas o caducadas no se conservan;
  el registro de eventos (`SecurityEvent` del diagrama) será otra feature.
- Programar la limpieza periódica (RF-011 solo ofrece la orden).
- Límites propios del cambio de contraseña (S-10).

## Criterios de finalización
- CF-1 La migración se aplica sobre la última de `accounts` en `main`, con unicidad garantizada por
  la base de datos en el identificador público y en la cuenta de la solicitud.
- CF-2 Hay tests para cada RF; la suite `pytest` está en verde con cobertura ≥ 80 % y
  `mypy`/`ruff`/`black` están limpios.
- CF-3 Un test fija el comportamiento de S-03: tras completar el cambio, la sesión de navegador y
  el token de la app abiertos antes dejan de autenticar.
- CF-4 El cambio de contraseña se puede recorrer de principio a fin con los comandos de RF-013 y
  el código leído del correo que muestra el proveedor local, y los pasos están documentados en `resumen.md`.
- CF-5 `HUMAN_TODO.md` incluye, como requisitos previos a publicar la API de cambio de contraseña,
  el límite de frecuencia (S-05) y el mensaje neutro (S-01).
- CF-6 Un test demuestra que, para un correo sin cuenta o con la cuenta inactiva, verificar,
  reenviar, completar y dejar caducar el identificador devuelto da los mismos resultados que una
  solicitud real cuyo código nunca se acierta (RF-017).

## Historial de cambios
- 2026-10-09 — Creación (feature nueva, separada de `procesos-pendientes` el 2026-10-01) — RF:
  RF-001…RF-013 — Estado: pendiente de clarificar
- 2026-10-09 — Clarificación (C-01…C-04) — RF: RF-001, RF-003, RF-009 ajustados; RF-014 y RF-015
  añadidos; S-02 y S-07 ajustados; S-11 y S-12 añadidos;
  CF-5 ajustado — Estado: clarificado
- 2026-10-09 — Validación: NO CUMPLIDA (1.ª) — RF-005, RF-009, RF-012 (tests: identificadores en el
  sentido solicitud → registro, atomicidad de completar, contador por IP y transición del secreto);
  corregido con T-015…T-018.
- 2026-10-09 — Validación: NO CUMPLIDA (2.ª) — RF-008, RF-011 (tests: reenviar y completar tras
  reactivar, purga de la orden); corregido con T-019 y T-020.
- 2026-10-09 — Validación: NO CUMPLIDA (3.ª) — RF-006, RF-007 (tests: dos mutantes sobrevivían a la
  suite completa, reiniciar la vida al reenviar y rechazar el reenvío con el código caducado) y el
  riesgo R-1 de RF-009 (dirección secundaria); corregido con T-021…T-023, comprobadas matando esos
  mutantes, sin una validación independiente posterior.
- 2026-10-09 — Validación: cerrada con riesgo residual aceptado — Riesgos: (1) T-021…T-023 sin
  validación independiente; (2) concurrencia protegida con bloqueos de fila sin probar con
  transacciones reales; (3) una solicitud en curso deja de servir si Django vuelve a calcular el
  hash de la contraseña al iniciar sesión; (4) el borrado del contador de inicios fallidos usa
  funciones internas de allauth; (5) sin aserción directa: la búsqueda de la dirección de correo
  sin distinguir mayúsculas, todos los campos de la solicitud de una cuenta inactiva en RF-004 y el
  instante exacto de caducidad de la solicitud; (6) la imagen de Docker no se ha construido con el
  `Dockerfile` real.
- 2026-10-14 — Cambio por `correo-asincrono-plantillas` (S-07, S-08): pedir el cambio devuelve
  siempre un identificador y la consola deja de mostrar el código — RF: RF-002, RF-004, RF-007,
  RF-009, RF-012 y RF-013 modificados; RF-016 y RF-017 añadidos; secuencia, S-01, S-06, fuera de
  alcance, CF-4 y CF-5 ajustados; CF-6 añadido. Clarificado (C-01, C-02): RF-005, RF-008,
  RF-010, RF-014 y RF-015 ajustados; S-13 añadido — Estado: impacto analizado
