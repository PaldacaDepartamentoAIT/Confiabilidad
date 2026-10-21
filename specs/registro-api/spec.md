# Spec: registro-api
Estado: aprobada
Aprobación: ligera

## Objetivo (por qué)
El registro ya existe como operación de consola (`procesos-pendientes`) y sus correos los envía
`correo-asincrono-plantillas`, pero ningún cliente puede usarlo. Esta feature abre el primer paso
del registro a la web y al escritorio: un endpoint que recibe el formulario (nombre completo, fecha
de nacimiento, correo, país y aceptación de los términos), indica cada error bajo su campo y, si
todo es válido, empieza el registro y devuelve el identificador público con el que el cliente
lleva a la pantalla de verificación. La respuesta es la misma tanto si el correo es nuevo como si
tiene un registro pendiente o una cuenta, para que el formulario no sirva para averiguar quién está
registrado.

## Requisitos funcionales
### RF-001 Solicitud de registro
Cuando se envíe una solicitud de registro con nombre completo, fecha de nacimiento, correo, país,
el documento de términos aceptado (su versión y su idioma) y la marca de aceptación, y opcionalmente
el idioma (RF-013), y todos los campos sean válidos, el sistema deberá empezar el registro (RF-024
de `procesos-pendientes`) y responder con el identificador público que este devuelve y el mensaje
neutro (RF-005).

### RF-002 Errores por campo
Si falta algún campo o alguno no es válido, entonces el sistema deberá rechazar la solicitud sin
empezar el registro ni enviar ningún correo, y devolver, para cada campo incorrecto, todos sus
errores a la vez, cada uno con un código estable y un texto descriptivo (RF-013). Las reglas de
cada campo son: nombre, RF-003 de `usuario-personalizado`; fecha de nacimiento, RF-004 de
`usuario-personalizado` (18 años más 5 días, S-02); país, RF-005 de `usuario-personalizado`;
correo, RF-003 de esta spec; términos, RF-004 de esta spec.

### RF-003 Formato del correo
El sistema deberá aceptar un correo solo si tiene el formato de una dirección válida y su dominio
contiene al menos un punto. Si el dominio no tiene punto (por ejemplo, `ana@localhost`) o es una
dirección IP (por ejemplo, `ana@[192.0.2.1]`), entonces el sistema deberá rechazarlo con un error
en el campo de correo. Los dominios con caracteres no ASCII y los sufijos `+etiqueta` se aceptan.

### RF-004 Términos obligatorios
Si la solicitud no lleva la marca de aceptación con valor verdadero, no indica el documento de
términos aceptado, o el indicado no existe, no es de términos o no pertenece a la versión vigente
(RF-003 de `consentimientos`), o no hay ninguna versión de términos vigente, entonces el sistema
deberá rechazar la solicitud con un error en el campo de términos, con un código propio para cada
uno de esos motivos, sin empezar el registro. Vale el documento de la versión vigente en cualquiera
de sus idiomas, coincida o no con el idioma de la solicitud.

### RF-005 Respuesta neutra
Cuando una solicitud válida empiece el registro, el sistema deberá responder con el mismo código de
estado, el mismo mensaje, la misma estructura y un identificador público del mismo formato, tanto si
el correo es nuevo como si tiene un registro pendiente vigente o pertenece a una cuenta, activa o
inactiva. Ninguna cabecera, campo ni cookie de la respuesta deberá distinguir el caso.

### RF-006 Correo nuevo
Cuando una solicitud válida llegue con un correo sin cuenta ni registro pendiente vigente, el sistema
deberá crear el registro pendiente con los datos y el documento de términos de la solicitud (RF-009)
y enviar el código de registro (RF-004 de `correo-asincrono-plantillas`).

### RF-007 Correo con registro pendiente
Cuando una solicitud válida llegue con un correo que tiene un registro pendiente vigente, el sistema
deberá conservar el registro existente, con sus datos y su documento de términos, descartar los de la
solicitud y emitir y enviar un código nuevo con un identificador público nuevo (RF-005 de
`procesos-pendientes`), con el límite de frecuencia de RF-010.

### RF-008 Correo con cuenta
Cuando una solicitud válida llegue con un correo que pertenece a una cuenta, el sistema deberá
responder igual que en los otros casos (RF-005) con un identificador público sin registro pendiente
detrás (RF-025 de `procesos-pendientes`), y enviar al titular el aviso "ya tienes cuenta" con su
tope (RF-006 y RF-007 de `correo-asincrono-plantillas`; si la cuenta está inactiva, no se envía).

### RF-009 Aceptación de los términos
Cuando se cree un registro pendiente, el sistema deberá guardar en él el documento de términos
aceptado en la solicitud. Cuando se complete ese registro (RF-020 de `procesos-pendientes`), el
sistema deberá registrar, en la misma operación que crea la cuenta, la aceptación de ese documento
(RF-006 de `consentimientos`), con la fecha de compleción como fecha de aceptación. Antes de
completarse, el sistema no deberá registrar ninguna aceptación nueva de términos para ese correo;
las que ya existan de cuentas borradas (RF-013 de `consentimientos`) no cambian. Si al completar el
documento guardado ya no pertenece a la versión vigente, o el registro pendiente no tiene documento
guardado (creado antes de esta feature), entonces el sistema deberá crear la cuenta sin registrar
ninguna aceptación.

### RF-010 Límite de frecuencia por correo e IP
Si una solicitud válida llega desde una IP (la IP real del cliente, RF-010 de `auth-headless`) que ya
envió una solicitud válida atendida con el mismo correo, normalizado, en los últimos 60 segundos, o 5
en la última hora (valores por defecto, RF-012), entonces el sistema deberá rechazarla sin empezar el
registro ni enviar ningún correo, con una respuesta de límite superado que indique cuántos segundos
esperar. Las solicitudes rechazadas por un límite no cuentan para ningún límite. El recuento y la
respuesta deberán ser los mismos tanto si el correo es nuevo como si tiene un registro pendiente o
una cuenta.

### RF-011 Límite de frecuencia por IP
Si una IP (la IP real del cliente, RF-010 de `auth-headless`) ya envió 20 solicitudes de registro
atendidas en la última hora (valor por defecto, RF-012), válidas o no, entonces el sistema deberá
rechazar las siguientes sin validarlas, sin empezar el registro ni enviar ningún correo, con la misma
respuesta de límite superado de RF-010.

### RF-012 Límites configurables
El sistema deberá permitir ajustar por configuración, sin cambiar el código, los tres límites de
RF-010 y RF-011.

### RF-013 Idioma de los mensajes
El sistema deberá devolver el texto de cada error de campo, del mensaje neutro y de la respuesta de
límite superado en el idioma de la solicitud (`es`, `pt-BR` o `en`), que se determina así: el campo
de idioma de la solicitud, si es uno de los tres (con las variantes de escritura que admite D-10 de
`correo-asincrono-plantillas`, como `pt-br` o `pt_BR`); si no, la cabecera `Accept-Language` por
idioma base (`es-*` → `es`, `pt-*` → `pt-BR`, `en-*` → `en`, en su orden de preferencia); y si
tampoco, el español. El código de cada error es el mismo en todos los idiomas. El registro pendiente
guarda ese mismo idioma (RF-012 de `correo-asincrono-plantillas`).

### RF-014 Clientes
El sistema deberá aceptar solicitudes de registro del cliente web, que deberán llevar protección
CSRF (RF-006 de `auth-headless`), y del cliente de aplicación, exento de CSRF. Si una solicitud del
cliente web llega sin protección CSRF válida, entonces el sistema deberá rechazarla sin validarla,
sin empezar el registro ni enviar ningún correo. La variante del cliente de aplicación admite
cualquier cliente que no sea un navegador; los orígenes configurados (RF-007 de `auth-headless`)
solo limitan a los navegadores, y sus únicas defensas son los límites de RF-010 y RF-011 (S-19).

## Supuestos
- S-01 Solo API (pregunta 1). Los criterios de pantalla del usuario («mostrar mensajes debajo de cada
  campo», «la pantalla no revela el caso», «redirige con un `public_id` en la URL») se cumplen aquí
  en su parte de servidor: un error por campo con su código (RF-002), una respuesta idéntica en los
  tres casos (RF-005) y el identificador que el cliente pone en la URL (RF-001). El formulario, la
  redirección y la pantalla de verificación serán una feature de frontend.
- S-02 La edad mínima es la de RF-004 de `usuario-personalizado`, 18 años más 5 días (pregunta 2). El
  criterio del usuario («18 años cumplidos») se sustituye por esa regla: la API no puede ser más
  permisiva que la cuenta, que rechazaría el guardado.
- S-03 La aceptación de los términos se guarda en el registro pendiente y su fila solo se crea al
  completar el registro con la contraseña (pregunta 3). Esto cambia lo aprobado en
  `procesos-pendientes` (RF-001, qué guarda el registro pendiente, y RF-020, completar el registro):
  antes de implementar, se pasa `sdd-cambio` por esa feature (CF-6).
- S-04 Esta feature depende de `correo-asincrono-plantillas`, que todavía no está en `main`: su rama
  (`claude/happy-franklin-nucn23`) cambia `procesos-pendientes` (RF-024 y RF-025: empezar el
  registro siempre devuelve un identificador y el caso con cuenta no tiene registro detrás) y añade
  el aviso "ya tienes cuenta". La spec, la clarificación, el plan y las tareas pueden hacerse ya; el
  código se escribe sobre esa feature fusionada (CF-6), no sobre el `main` actual, cuyo `start` tiene
  otra firma.
- S-05 El límite de frecuencia cuenta las solicitudes por correo e IP, sea cual sea el caso, y por
  IP (pregunta 4, C-01). *Por qué:* si solo se limitara al registro pendiente, que salga o no el
  límite revelaría que el correo está en curso; y sin el límite por IP, una sola máquina podría
  mandar códigos a miles de correos ajenos desde el dominio del proyecto y agotar el cupo del
  proveedor (S-15 y S-16 de `correo-asincrono-plantillas`). Contar por la pareja correo e IP, y no
  solo por correo, impide que un tercero bloquee el registro de otra persona agotando el límite de
  su correo (C-01), y hace que el tiempo de espera del límite solo refleje las solicitudes del propio
  solicitante, no las de otra persona (C-05). *Riesgo aceptado:* quien disponga de muchas IP puede
  seguir enviando correos a una misma dirección, uno por IP y minuto; en el caso con cuenta, el tope
  del aviso (RF-007 de `correo-asincrono-plantillas`) lo frena.
- S-06 Solo las solicitudes válidas cuentan para el límite por correo e IP; para el de IP cuentan
  todas. Una solicitud con errores no empieza nada, pero repetirla sin freno serviría para probar
  combinaciones contra el servidor. Las rechazadas por un límite no cuentan para ninguno (C-06): la
  ventana se libera sola aunque el cliente reintente.
- S-07 Los errores llevan un código estable y un texto traducido (pregunta 5). Los mensajes del
  backend siguen escritos en inglés y marcados para traducción (`AGENTS.md`); esta feature añade sus
  traducciones a español y portugués de Brasil.
- S-08 El formato del correo es más estricto en la API que en la cuenta (pregunta 6): las cuentas
  creadas por consola o por el panel siguen con la regla actual. *Por qué:* un correo sin dominio
  real nunca recibirá el código y solo gasta cupo.
- S-09 Ambos clientes, con CSRF en la web (pregunta 7). *Por qué:* sin CSRF, cualquier web podría
  hacer que el navegador de su visitante enviara registros a terceros desde su IP.
- S-10 Si el documento de términos no es el vigente o no hay ninguno vigente, el registro se rechaza
  con un error en ese campo (pregunta 8): falla cerrado. Nadie puede registrarse mientras no haya
  términos vigentes publicados.
- S-11 Repetir el registro con un correo que tiene un registro pendiente descarta también el
  documento de términos nuevo: se conserva el aceptado la primera vez (RF-007), igual que el resto
  de los datos.
- S-12 Si entre empezar y completar el registro entra en vigor una versión nueva de términos, la
  cuenta se crea sin aceptación (C-02), y RF-015 de `consentimientos` la da por no aceptada. Lo mismo
  ocurre con los registros pendientes creados antes de esta feature, que no tienen documento guardado
  (C-13). *Por qué:* no cambia `consentimientos`, que solo admite aceptar la versión vigente.
  *Riesgo aceptado:* no queda constancia del documento que la persona sí aceptó, y hasta que exista
  la feature que pide aceptar los términos nuevos al iniciar sesión, esa cuenta funciona sin
  términos aceptados.
- S-13 El texto del mensaje neutro no puede afirmar que llegó un código, porque en el caso de cuenta
  llega un aviso, y con una cuenta inactiva o con el tope del aviso no llega nada. Propuesta: «Si
  puedes registrarte con este correo, recibirás un código en unos minutos. Revisa también la carpeta
  de spam.» El texto final se revisa en el PR.
- S-14 Una solicitud enviada con una sesión iniciada se trata igual que sin sesión: el registro no
  depende de quién envía el formulario.
- S-15 El límite de frecuencia de esta feature cubre solo el formulario de registro. El de reenviar el
  código, el de verificarlo y el del restablecimiento de contraseña (S-05 de `cambio-contrasena`)
  siguen pendientes, cada uno con su API.
- S-16 El tiempo de respuesta no se exige en esta spec (C-03): lo cubre RF-024 de
  `procesos-pendientes`, que saca de la respuesta todo el trabajo que depende del caso.
- S-17 El código se escribe cuando `correo-asincrono-plantillas` esté fusionada en `main` (C-04,
  CF-6), no encima de su rama. *Por qué:* esa rama aún puede cambiar en su validación, y el trabajo
  hecho encima se rehace.
- S-18 El límite por IP se mantiene en 20 por hora aunque varias personas se registren desde la
  misma IP pública, como una planta detrás de un NAT (C-07). Si una planta lo necesita, se sube por
  configuración (RF-012).
- S-19 La variante del cliente de aplicación es pública para cualquier cliente que no sea un
  navegador (C-08). *Por qué:* CORS solo lo aplican los navegadores, y exigir una cabecera `Origin`
  no detiene a un script, que puede falsificarla. Quitar la variante dejaría sin registro al
  escritorio, que usa token (S-07 de `auth-headless`). *Riesgo aceptado:* un bot con muchas IP puede
  generar registros hasta el límite de cada una; si ocurre, la respuesta es un CAPTCHA (fuera de
  alcance).
- S-20 El idioma lo decide el campo del formulario antes que la cabecera (C-10). *Por qué:* se
  guarda en la cuenta y decide el idioma de sus avisos de seguridad, así que debe ser el que la
  persona eligió en la interfaz, no el que anuncia su navegador. La cabecera por idioma base se
  aparta de D-10 de `correo-asincrono-plantillas`, que convierte cualquier otra variante en `es`.
- S-21 Vale cualquier idioma del documento de términos de la versión vigente (C-11), como en RF-015
  de `consentimientos`.
- S-22 La marca de aceptación es obligatoria además del documento (C-09): la intención de aceptar
  queda explícita en la solicitud, y un cliente que siempre envía el documento no basta.

## Fuera de alcance
- Pantallas: formulario, redirección y pantalla de verificación (S-01).
- Los endpoints de verificar el código, reenviarlo y completar el registro con la contraseña.
- La API del restablecimiento de contraseña y sus límites (S-15).
- CAPTCHA u otras defensas contra bots aparte del límite de frecuencia.
- Cambiar la edad mínima de la cuenta (S-02).
- Marketing: el consentimiento de marketing no se pide en el formulario.

## Criterios de finalización
- CF-1 Hay tests para cada RF. La suite `pytest` está en verde con cobertura ≥ 80 %, y
  `mypy`/`ruff`/`black` están limpios.
- CF-2 Un test demuestra que, para un correo nuevo, uno con registro pendiente vigente y uno con
  cuenta activa e inactiva, la respuesta (código de estado, cuerpo, cabeceras y cookies) es idéntica
  salvo el valor del identificador público, y que lo mismo ocurre con la respuesta de límite superado
  (RF-005, RF-010).
- CF-3 Un test demuestra que el identificador devuelto para un correo con cuenta no corresponde a
  ningún registro pendiente (RF-008).
- CF-4 Un test demuestra que cada campo inválido devuelve su error con su código, y que una solicitud
  con varios campos inválidos devuelve todos los errores a la vez (RF-002).
- CF-5 `resumen.md` explica cómo probar con `curl` cada caso, el cliente web (con CSRF) y el de
  aplicación, los errores por campo y los límites, leyendo el código en el correo que muestra el
  proveedor local.
- CF-6 Antes de implementar, `correo-asincrono-plantillas` está fusionada en `main` y el `sdd-cambio`
  de `procesos-pendientes` para guardar los términos (S-03) está aprobado.
- CF-7 Los textos de los errores, del mensaje neutro y del límite superado existen en `es`, `pt-BR` y
  `en` (RF-013).

## Historial de cambios
- 2026-10-16 — Creación (feature nueva) — RF: RF-001…RF-014 — Estado: pendiente de clarificar
- 2026-10-16 — Clarificación (C-01…C-13) — RF: RF-001, RF-004, RF-005, RF-009, RF-010, RF-011,
  RF-013 y RF-014 ajustados; S-05, S-06 y S-12 ajustados; S-16…S-22 añadidos — Estado: clarificado
- 2026-10-16 — Aprobación por el usuario — Estado: aprobada
- 2026-10-21 — Validación: NO CUMPLIDA (1.ª) — RF-002 (500 con caracteres nulos o sustitutos y con
  correos de más de 254 caracteres), RF-003 (dominio IP sin corchetes aceptado; origen: plan,
  M-03/D-14 ajustados) y CF-5 (el resumen no prueba el límite por IP). Correcciones propuestas:
  T-018…T-021.
