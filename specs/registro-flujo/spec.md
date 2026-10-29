# Spec: registro-flujo
Estado: borrador
Aprobación: ligera

## Objetivo (por qué)
El registro existe en el servidor (`procesos-pendientes`) y su primer paso, el formulario, ya tiene
API (`registro-api`), pero nadie puede registrarse desde la web ni desde el escritorio. Esta feature
completa el recorrido de extremo a extremo: la pantalla del formulario, la de verificación del
código, la de contraseña y la de cuenta creada, junto con lo que falta en el servidor para
verificar, reenviar y completar desde los clientes. Debe hacerlo sin que ninguna pantalla ni
respuesta permita averiguar si un correo tiene cuenta, y sin que el identificador público de la URL
dé acceso a nada por sí mismo: la contraseña solo se acepta junto con el código, que el servidor
comprueba de nuevo en cada petición.

## Secuencia
1. La persona rellena el formulario. El navegador revisa lo básico y el servidor, el resto; los
   errores salen bajo cada campo (RF-001…RF-004).
2. Con el formulario correcto, se abre la pantalla de verificación con el identificador público en
   la URL; le llega un código por correo (RF-005).
3. La persona introduce el código. Si el servidor lo acepta, se muestra la pantalla de contraseña
   (RF-006…RF-010).
4. La persona define su contraseña. El cliente la envía junto con el código y el servidor vuelve a
   comprobarlo (RF-011…RF-013).
5. Se crea la cuenta con sus consentimientos, se borra el registro pendiente y se muestra la
   pantalla de cuenta creada (RF-014, RF-015).

En este documento, «RF-0xx de `procesos-pendientes`» y «RF-0xx de `registro-api`» remiten a esas
specs. «Proceso» es un registro pendiente, el identificador sin registro detrás de RF-025 de
`procesos-pendientes` o un identificador desconocido tratado según RF-016.

## Requisitos funcionales

### Pantalla del formulario

### RF-001 Formulario de registro
El sistema deberá ofrecer una pantalla de registro con los campos nombre completo, fecha de
nacimiento, correo, país, la aceptación de los términos (obligatoria, con acceso al texto de la
versión vigente) y el consentimiento de marketing (opcional, sin marcar por defecto, con acceso a su
texto vigente), en el idioma de la interfaz.

### RF-002 Validación básica en el navegador
Cuando la persona salga de un campo o envíe el formulario, el sistema deberá comprobar en el
navegador que los campos obligatorios no están vacíos, que el correo tiene forma de dirección, que
la fecha de nacimiento es una fecha válida y que la casilla de términos está marcada. Si alguna
comprobación falla al enviar, entonces el sistema no deberá enviar el formulario al servidor. Las
demás reglas (edad mínima, país y formato estricto del correo) las decide el servidor (RF-002 de
`registro-api`).

### RF-003 Errores bajo cada campo
Si el navegador o el servidor detectan errores en el formulario, entonces el sistema deberá mostrar
cada error debajo de su campo, todos a la vez, desplazar la pantalla hasta el primer campo con
error, en el orden en que aparecen en el formulario, y llevar el foco a él. Si la respuesta del
servidor no es un error de campo (límite superado o fallo de red), entonces el sistema deberá
mostrar un mensaje general y conservar los datos escritos.

### RF-004 Formulario correcto
Cuando el servidor acepte el formulario, el sistema deberá abrir la pantalla de verificación con la
URL que contiene el identificador público devuelto (RF-001 de `registro-api`).

### Pantalla de verificación

### RF-005 Contenido de la pantalla de verificación
Cuando se abra la URL de verificación con un identificador público, el sistema deberá mostrar un
texto fijo que no afirme que el correo existe ni que llegó un código, el campo del código de 6
dígitos, el tiempo que le queda al código vigente y el botón de reenvío con su cuenta atrás. Ninguna
pantalla del registro posterior al formulario deberá mostrar el correo electrónico.

### RF-006 Temporizador de caducidad
Mientras la pantalla de verificación esté abierta, el sistema deberá mostrar el tiempo restante del
código vigente según el servidor, también tras recargar la página. Cuando llegue a cero, el sistema
deberá indicar que el código ha caducado y que puede pedirse otro.

### RF-007 Verificación del código
Cuando se envíe un código desde la pantalla de verificación, el sistema deberá comprobarlo en el
servidor con las reglas de RF-009 y RF-010 de `procesos-pendientes`. Si el servidor lo acepta,
entonces el sistema deberá mostrar la pantalla de contraseña. Si no coincide, entonces el sistema
deberá mostrar bajo el campo un único mensaje de código incorrecto y sumar un intento fallido.

### RF-008 Código ya validado
Si se presenta en la pantalla de verificación el código correcto de un proceso cuyo código ya está
validado, sin caducar ni agotar los intentos, entonces el sistema deberá aceptarlo de nuevo, sin
sumar ni restar intentos, y mostrar la pantalla de contraseña.

### RF-009 Bloqueo tras cinco intentos
Si un proceso acumula 5 intentos fallidos (RF-010 de `procesos-pendientes`), entre la pantalla de
verificación y la de contraseña, entonces el sistema deberá mostrar un mensaje de bloqueo,
desactivar el envío de códigos y ofrecer solo el reenvío, hasta que se emita un código nuevo.

### RF-010 Reenvío del código
Cuando la persona pulse el botón de reenvío, el sistema deberá emitir un código nuevo según RF-016
de `procesos-pendientes` e invalidar el anterior. El botón deberá estar disponible solo pasados 60
segundos desde la última emisión, con una cuenta atrás visible, y como mucho 5 veces por proceso.
Agotados los reenvíos, el sistema deberá desactivar el botón e indicar que hay que volver a empezar
el registro, con acceso al formulario. El servidor deberá rechazar cualquier reenvío anterior a los
60 segundos o posterior al quinto, venga de la pantalla o no.

### Pantalla de contraseña

### RF-011 Acceso a la pantalla de contraseña
El sistema deberá mostrar el formulario de contraseña solo después de que el servidor haya aceptado
el código en esa misma página (RF-007, RF-008). Mientras la pantalla esté abierta, el navegador
conservará el código solo en la memoria de la página. Si se abre o se recarga la pantalla de
contraseña sin un código aceptado en memoria, entonces el sistema deberá mostrar la pantalla de
verificación del mismo identificador.

### RF-012 Completar con código y contraseña
Cuando se envíe la contraseña, el sistema deberá enviar al servidor el identificador público, el
código y la contraseña, y el servidor deberá comprobar de nuevo el código en cada petición: que
coincide con el vigente, que está validado, que el proceso no ha caducado (RF-011 de
`procesos-pendientes`) y que no se han agotado los intentos. Si el código no coincide, entonces el
sistema deberá sumar un intento fallido y rechazar la petición sin evaluar la contraseña. El servidor
deberá tomar todos los datos de la cuenta del registro pendiente y ningún otro del cliente.

### RF-013 Política de contraseña
Cuando la persona salga del campo de contraseña o la envíe, el sistema deberá comprobar en el
navegador que tiene al menos 12 caracteres y que no consta solo de números. Si alguna de esas
comprobaciones falla al enviar, entonces el sistema no deberá enviar la contraseña al servidor. Si
la contraseña no cumple la política del servidor (RF-022 de `procesos-pendientes`: al menos 12
caracteres, no parecida al correo ni al nombre, no común y no filtrada; y la regla de no constar
solo de números, que el servidor ya aplica), entonces el sistema deberá mostrar bajo el campo cada
regla incumplida y conservar el código válido, sin sumar ningún intento, para que la persona pruebe
otra contraseña.

### RF-014 Creación de la cuenta
Cuando el código y la contraseña sean válidos, el sistema deberá, en una sola operación, crear la
cuenta con los datos del registro pendiente, la contraseña indicada y el correo verificado, registrar
la aceptación de los términos (RF-020 de `procesos-pendientes`) y, si se marcó, la concesión de
marketing (RF-017), marcar el código como usado y borrar el registro pendiente. El código solo se da
por usado al crear la cuenta, nunca al validarlo. Si la operación falla, entonces no deberá quedar
nada de ella.

### RF-015 Cuenta creada
Cuando se cree la cuenta, el sistema deberá mostrar una pantalla de cuenta creada, sin iniciar
sesión. Volver a la pantalla de verificación o de contraseña de ese identificador se comportará
como con un identificador desconocido (RF-016).

### Indistinguibilidad

### RF-016 Identificador desconocido
Si un identificador público no corresponde a ningún registro pendiente ni a ningún identificador sin
registro detrás, tenga o no un formato válido, entonces el sistema deberá tratarlo como un proceso
real cuyo código nunca se acierta, a partir del primer momento en que lo recibe: mismo texto, mismo
temporizador de caducidad, misma cuenta atrás y tope de reenvío, mismo mensaje de código incorrecto,
mismo bloqueo tras 5 intentos y misma caducidad. El estado que guarde para ello deberá borrarse solo
cuando ese proceso imitado habría caducado.

### RF-017 Respuestas idénticas
El sistema deberá mostrar las mismas pantallas, textos y temporizadores, y responder con los mismos
códigos de estado, estructura, cabeceras y cookies, en verificar, reenviar y completar, tanto para un
registro pendiente real cuyo código no se acierta como para un identificador sin registro detrás
(RF-025 de `procesos-pendientes`) o un identificador desconocido (RF-016).

### Servidor

### RF-018 Marketing en el registro
Cuando el formulario llegue con el consentimiento de marketing marcado, el sistema deberá guardar en
el registro pendiente el documento de marketing vigente aceptado. Cuando se repita el registro con un
correo que tiene un registro pendiente vigente, el sistema deberá conservar la elección de marketing
del primero, igual que el resto de sus datos (RF-005 de `procesos-pendientes`). Cuando se complete el
registro, el sistema deberá registrar la concesión de marketing en la misma operación que crea la
cuenta, con la fecha de compleción. Si el documento guardado ya no pertenece a la versión vigente,
entonces deberá crear la cuenta sin registrar la concesión.

### RF-019 Límite de frecuencia por IP
Si una IP (la IP real del cliente, RF-010 de `auth-headless`) supera el número configurado de
peticiones de verificar, reenviar o completar en una hora, entonces el sistema deberá rechazar las
siguientes sin evaluarlas, con una respuesta de límite superado que indique cuántos segundos
esperar, igual sea cual sea el identificador.

### RF-020 Limpieza programada
El sistema deberá borrar de forma automática, sin intervención manual, cada registro pendiente que no
se haya completado 24 horas después de caducar su último código, y el estado de los identificadores
imitados (RF-016) en cuanto habrían caducado.

### RF-021 Clientes
El sistema deberá admitir verificar, reenviar y completar desde el cliente web, con protección CSRF,
y desde el cliente de aplicación, sin ella, con las mismas reglas que RF-014 de `registro-api`.

### RF-022 Idioma
El sistema deberá mostrar las pantallas y devolver los mensajes del servidor de esta feature en
`es`, `pt-BR` y `en`, con el idioma de la interfaz (RF-013 de `registro-api`).

### RF-023 Valores configurables
El sistema deberá permitir ajustar por configuración, sin cambiar el código, la espera entre
reenvíos (60 s), el máximo de reenvíos por proceso (5), el límite por IP de RF-019 y el plazo de
borrado de RF-020 (24 horas).

## Supuestos
- S-01 El paso de contraseña exige el código junto con la contraseña (pregunta 1). *Por qué:* si
  bastara el identificador con el código validado, quien viera la URL o el correo podría fijar la
  contraseña durante la gracia. Aceptar de nuevo un código ya validado (RF-008, RF-012) contradice la
  última frase de RF-009 de `procesos-pendientes`. El plan buscará antes una solución dentro de esta
  feature con las funciones públicas existentes; si no la hay, se pasa `sdd-cambio` por
  `procesos-pendientes` antes de implementar (CF-6).
- S-02 Un identificador desconocido imita un proceso real en la pantalla y en la API (pregunta 2).
  *Por qué:* es tu criterio de finalización. *Coste:* el servidor guarda estado temporal por cada
  identificador desconocido que recibe; el límite por IP (RF-019) y el borrado al caducar (RF-020)
  lo acotan. *Matiz:* saber si un correo tiene cuenta ya lo impide RF-025 de `procesos-pendientes`;
  un identificador inventado no está ligado a ningún correo, así que esta regla es defensa en
  profundidad.
- S-03 Las 24 horas son un borrado físico; el registro deja de poder usarse a los 15 minutos de
  caducar su código (RF-011 de `procesos-pendientes`, sin cambios) (pregunta 3). Cuenta para el
  borrado todo registro no completado, con el código validado o sin validar. *Coste:* los datos de
  quien no termina el registro se guardan un día más. La orden de consola de RF-013 de
  `procesos-pendientes` sigue pudiendo borrar antes los caducados.
- S-04 60 segundos entre reenvíos y como mucho 5 reenvíos por proceso (pregunta 4). *Por qué:* cada
  reenvío pone los intentos a 0 (RF-016 de `procesos-pendientes`), así que el tope limita un proceso
  a 30 intentos de código. Pasado el tope, hay que repetir el formulario, que emite un identificador
  nuevo (RF-005 de `procesos-pendientes`) con sus propios límites.
- S-05 El navegador revisa lo básico y el servidor decide el resto (pregunta 5). La regla de edad,
  la lista de países y el formato estricto del correo no se replican en el navegador.
- S-06 El formulario incluye el consentimiento de marketing opcional (pregunta 6). Esto cambia lo
  aprobado en `registro-api` («Marketing: el consentimiento de marketing no se pide en el
  formulario») y en `procesos-pendientes` (qué guarda el registro pendiente, cómo se repite y cómo se
  completa): antes de implementar, se pasa `sdd-cambio` por ambas (CF-6). La concesión usa las
  operaciones de `consentimientos`.
- S-07 Tras crear la cuenta se muestra una pantalla de éxito sin iniciar sesión (pregunta 7). El
  enlace al inicio de sesión se añadirá cuando exista esa pantalla.
- S-08 El código validado vive solo en la memoria de la página (pregunta 8). *Por qué:* es la
  credencial del paso de contraseña, y guardarlo en el almacenamiento del navegador lo expondría a
  un script inyectado. *Coste:* recargar obliga a reescribir el código, sin gastar intentos (RF-008).
- S-09 El plazo para enviar la contraseña es el de completar de RF-011 de `procesos-pendientes`:
  hasta 15 minutos después de caducar el código, y nunca más de 1 hora desde el alta.
- S-10 La pantalla de verificación no muestra cuántos intentos quedan: solo el mensaje de código
  incorrecto y, al quinto, el de bloqueo. *Por qué:* menos superficie que mantener idéntica entre
  casos; si se quiere mostrar, se decide en la clarificación.
- S-11 El temporizador lo da el servidor (RF-006), para que recargar no lo reinicie. Para un
  identificador desconocido cuenta desde la primera vez que el servidor lo recibe (RF-016).
- S-12 Un identificador sustituido por un registro repetido (RF-005 de `procesos-pendientes`) pasa a
  comportarse como desconocido (RF-016): su temporizador empieza de nuevo. Solo lo nota quien repitió
  el registro, que recibe un enlace nuevo.
- S-13 El límite por IP de RF-019 tiene por defecto 60 peticiones por hora, sumadas verificar,
  reenviar y completar; el valor se confirma en la clarificación.
- S-14 Las pantallas siguen `docs/identidad-visual.md` y usan los componentes de
  `componentes-base-accesibles`; los textos son provisionales hasta revisarse en el PR.
- S-15 El navegador comprueba en la pantalla de contraseña la longitud mínima y que no conste solo
  de números (petición del usuario tras la entrevista). La similitud, las comunes y las filtradas
  las comprueba solo el servidor. *Por qué:* la similitud exigiría enviar al navegador el nombre y
  el correo del registro pendiente, lo que rompería RF-005 y RF-016; las comunes y las filtradas
  exigirían copiar una lista de unas 20 000 contraseñas o consultar un servicio externo desde el
  navegador. *Riesgo aceptado por el usuario:* las dos reglas están copiadas a mano en el navegador
  y en el servidor. Si cambian, hay que actualizarlas en ambos lados; mientras no coincidan, el
  navegador bloqueará o dejará pasar contraseñas de forma distinta al servidor, que es quien decide.

## Fuera de alcance
- Inicio de sesión, pantalla de inicio de sesión y área privada (S-07).
- Restablecimiento de contraseña y sus pantallas.
- CAPTCHA u otras defensas contra bots, aparte de los límites de frecuencia.
- Cambiar las reglas de los campos del formulario, la edad mínima o la política de contraseñas.
- Revocar el marketing o aceptar términos nuevos tras el alta.
- Mostrar el número de intentos restantes (S-10).

## Criterios de finalización
- CF-1 Hay tests para cada RF, en backend y frontend. `pytest` y `pnpm --filter frontend test` están
  en verde con una cobertura ≥ 80 %, y `mypy`, `ruff`, `black`, `tsc`, ESLint y Prettier están
  limpios.
- CF-2 Un test demuestra que verificar, reenviar, completar y dejar caducar dan las mismas respuestas
  (código de estado, cuerpo, cabeceras y cookies), con los mismos plazos, para un registro real cuyo
  código no se acierta, un identificador sin registro detrás y uno desconocido, incluido el bloqueo
  tras 5 intentos y el tope de reenvíos (RF-016, RF-017).
- CF-3 Un test demuestra que completar sin el código, con un código incorrecto o con el identificador
  solo nunca crea la cuenta, y que un error de contraseña no invalida el código ni suma intentos
  (RF-012, RF-013).
- CF-4 Un test demuestra que la cuenta, el correo verificado, la aceptación de términos y la concesión
  de marketing se crean juntos o no se crea nada, y que el registro pendiente desaparece (RF-014).
- CF-5 Tests del frontend demuestran que los errores salen bajo su campo con desplazamiento y foco al
  primero, que ninguna pantalla muestra el correo y que recargar la pantalla de contraseña vuelve a la
  de verificación (RF-003, RF-005, RF-011).
- CF-6 Antes de implementar, están aprobados los `sdd-cambio` de `registro-api` y
  `procesos-pendientes` para el marketing (S-06) y, si el plan lo necesita, el de RF-009 de
  `procesos-pendientes` (S-01).
- CF-7 `resumen.md` explica cómo recorrer el registro en la web y con `curl`, leyendo el código del
  correo que muestra el proveedor local, y cómo comprobar la limpieza programada.

## Historial de cambios
- 2026-10-29 — Creación (feature nueva) — RF: RF-001…RF-023 — Estado: pendiente de clarificar
- 2026-10-29 — Ajuste del borrador a petición del usuario: la pantalla de contraseña comprueba en
  el navegador la longitud y que no sea solo números — RF: RF-013 — S-15 añadido — Estado:
  pendiente de clarificar
