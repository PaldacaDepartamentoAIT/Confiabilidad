# Spec: registro-api
Estado: borrador
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
Cuando se envíe una solicitud de registro con nombre completo, fecha de nacimiento, correo, país y
el documento de términos aceptado (su versión y su idioma), y todos los campos sean válidos, el
sistema deberá empezar el registro (RF-024 de `procesos-pendientes`) y responder con el
identificador público que este devuelve y el mensaje neutro (RF-005).

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
Si la solicitud no indica el documento de términos aceptado, o el indicado no existe, no es de
términos o no pertenece a la versión vigente (RF-003 de `consentimientos`), o no hay ninguna versión
de términos vigente, entonces el sistema deberá rechazar la solicitud con un error en el campo de
términos con su propio código, sin empezar el registro.

### RF-005 Respuesta neutra
Cuando una solicitud válida empiece el registro, el sistema deberá responder con el mismo código de
estado, el mismo mensaje, la misma estructura y un identificador público del mismo formato, tanto si
el correo es nuevo como si tiene un registro pendiente vigente o pertenece a una cuenta, activa o
inactiva. Ninguna cabecera, campo ni cookie de la respuesta deberá distinguir el caso, y el tiempo
de respuesta no deberá depender de él (el trabajo que depende del caso se hace fuera de la
respuesta, RF-024 de `procesos-pendientes`).

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
completarse, no deberá existir ninguna aceptación de términos para ese correo.

### RF-010 Límite de frecuencia por correo
Si una solicitud válida llega con un correo, normalizado, que ya recibió una solicitud válida en los
últimos 60 segundos, o 5 en la última hora (valores por defecto, RF-012), entonces el sistema deberá
rechazarla sin empezar el registro ni enviar ningún correo, con una respuesta de límite superado que
indique cuántos segundos esperar. El recuento y la respuesta deberán ser los mismos tanto si el
correo es nuevo como si tiene un registro pendiente o una cuenta.

### RF-011 Límite de frecuencia por IP
Si una IP (la IP real del cliente, RF-010 de `auth-headless`) ya envió 20 solicitudes de registro en
la última hora (valor por defecto, RF-012), válidas o no, entonces el sistema deberá rechazar las
siguientes sin validarlas, sin empezar el registro ni enviar ningún correo, con la misma respuesta de
límite superado de RF-010.

### RF-012 Límites configurables
El sistema deberá permitir ajustar por configuración, sin cambiar el código, los tres límites de
RF-010 y RF-011.

### RF-013 Idioma de los mensajes
El sistema deberá devolver el texto de cada error de campo, del mensaje neutro y de la respuesta de
límite superado en el idioma de la solicitud (`es`, `pt-BR` o `en`). Si la solicitud no indica uno de
esos tres, deberá usar el español. El código de cada error es el mismo en todos los idiomas. El
registro pendiente guarda ese mismo idioma (RF-012 de `correo-asincrono-plantillas`).

### RF-014 Clientes
El sistema deberá aceptar solicitudes de registro del cliente web, que deberán llevar protección
CSRF (RF-006 de `auth-headless`), y del cliente de aplicación, exento de CSRF y limitado a los
orígenes configurados (RF-007 de `auth-headless`). Si una solicitud del cliente web llega sin
protección CSRF válida, entonces el sistema deberá rechazarla sin validarla, sin empezar el registro
ni enviar ningún correo.

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
- S-05 El límite de frecuencia cuenta las solicitudes por correo, sea cual sea el caso, y por IP
  (pregunta 4). *Por qué:* si solo se limitara al registro pendiente, que salga o no el límite
  revelaría que el correo está en curso; y sin el límite por IP, una sola máquina podría mandar
  códigos a miles de correos ajenos desde el dominio del proyecto y agotar el cupo del proveedor
  (S-15 y S-16 de `correo-asincrono-plantillas`). *Coste:* quien se equivoca de correo y lo corrige
  enseguida no espera, pero quien repite el mismo correo sí.
- S-06 Solo las solicitudes válidas cuentan para el límite por correo; para el de IP cuentan todas.
  Una solicitud con errores no empieza nada, pero repetirla sin freno serviría para probar
  combinaciones contra el servidor.
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
- S-12 *Suposición, a confirmar en `sdd-clarificar`:* si entre empezar y completar el registro entra
  en vigor una versión nueva de términos, al completar se registra la aceptación del documento
  guardado aunque ya no sea el vigente, porque es el que la persona aceptó. RF-006 de
  `consentimientos` hoy lo rechazaría, y la cuenta quedaría con los términos sin aceptar (RF-015 de
  `consentimientos`) hasta que acepte los nuevos.
- S-13 El texto del mensaje neutro no puede afirmar que llegó un código, porque en el caso de cuenta
  llega un aviso, y con una cuenta inactiva o con el tope del aviso no llega nada. Propuesta: «Si
  puedes registrarte con este correo, recibirás un código en unos minutos. Revisa también la carpeta
  de spam.» El texto final se revisa en el PR.
- S-14 Una solicitud enviada con una sesión iniciada se trata igual que sin sesión: el registro no
  depende de quién envía el formulario.
- S-15 El límite de frecuencia de esta feature cubre solo el formulario de registro. El de reenviar el
  código, el de verificarlo y el del restablecimiento de contraseña (S-05 de `cambio-contrasena`)
  siguen pendientes, cada uno con su API.

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
