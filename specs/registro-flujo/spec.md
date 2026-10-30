# Spec: registro-flujo
Estado: aprobada
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
   la URL; le llega un código por correo, cuyo enlace abre esa misma pantalla (RF-005).
3. La persona introduce el código. Si el servidor lo acepta, se muestra la pantalla de contraseña
   (RF-006…RF-010).
4. La persona define su contraseña. El cliente la envía junto con el código y el servidor vuelve a
   comprobarlo (RF-011…RF-013).
5. Se crea la cuenta con sus consentimientos, se borra el registro pendiente y se muestra la
   pantalla de cuenta creada (RF-014, RF-015).

En este documento, «RF-0xx de `procesos-pendientes`» y «RF-0xx de `registro-api`» remiten a esas
specs. «Plaza» es el identificador sin registro detrás de RF-025 de `procesos-pendientes`.
«Proceso» es un registro pendiente o una plaza.

## Requisitos funcionales

### Pantalla del formulario

### RF-001 Formulario de registro
El sistema deberá ofrecer una pantalla de registro con los campos nombre completo, fecha de
nacimiento, correo, país, la aceptación de los términos (obligatoria, con acceso al texto de la
versión vigente) y el consentimiento de marketing (opcional, sin marcar por defecto, con acceso a su
texto vigente), en el idioma de la interfaz. Si no hay ningún documento de marketing vigente,
entonces el sistema no deberá mostrar la casilla de marketing.

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
servidor es de límite superado, entonces el sistema deberá actuar según RF-024. Si es un fallo de
red u otro error que no es de campo, entonces el sistema deberá mostrar un mensaje general y
conservar los datos escritos.

### RF-004 Formulario correcto
Cuando el servidor acepte el formulario, el sistema deberá abrir la pantalla de verificación con la
URL que contiene el identificador público devuelto (RF-001 de `registro-api`).

### Pantalla de verificación

### RF-005 Contenido de la pantalla de verificación
Cuando se abra la URL de verificación con un identificador público, el sistema deberá mostrar un
texto fijo que no afirme que el correo existe ni que llegó un código, el campo del código de 6
dígitos, el tiempo que le queda al código vigente y el botón de reenvío con su cuenta atrás. La
misma pantalla deberá abrirse tanto desde la redirección del formulario (RF-004) como desde el enlace
del correo del código (S-12 de `correo-asincrono-plantillas`). Ninguna pantalla del registro
posterior al formulario deberá mostrar el correo electrónico.

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
60 segundos o posterior al quinto, venga de la pantalla o no. Si el código ya está validado, entonces
el servidor deberá rechazar el reenvío (RF-016 de `procesos-pendientes`) con la misma respuesta y el
mismo mensaje que cualquier otro reenvío rechazado.

### Pantalla de contraseña

### RF-011 Acceso a la pantalla de contraseña
El sistema deberá mostrar el formulario de contraseña solo después de que el servidor haya aceptado
el código en esa misma página (RF-007, RF-008). Mientras la pantalla esté abierta, el navegador
conservará el código solo en la memoria de la página. Si se abre o se recarga la pantalla de
contraseña sin un código aceptado en memoria, entonces el sistema deberá mostrar la pantalla de
verificación del mismo identificador. Si el servidor rechaza el código al enviar la contraseña (no
coincide, caducó, se bloqueó o se sustituyó), entonces el sistema deberá descartar el código de la
memoria y mostrar la pantalla de verificación del mismo identificador con el mensaje que
corresponda.

### RF-012 Completar con código y contraseña
Cuando se envíe la contraseña, el sistema deberá enviar al servidor el identificador público, el
código y la contraseña, y el servidor deberá comprobar de nuevo el código en cada petición: que
coincide con el vigente, que está validado, que el proceso no ha caducado (RF-011 de
`procesos-pendientes`) y que no se han agotado los intentos. Si el código no coincide, entonces el
sistema deberá sumar un intento fallido y rechazar la petición sin evaluar la contraseña. Si el código
coincide pero no se validó antes (RF-007), entonces el sistema deberá rechazar la petición, sumar un
intento fallido y responder igual que con un código incorrecto. El servidor deberá tomar todos los
datos de la cuenta del registro pendiente y ningún otro del cliente.

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
sesión. Volver a la pantalla de verificación o de contraseña de ese identificador deberá dar
«no encontrado» (RF-016).

### Indistinguibilidad

### RF-016 Identificador no encontrado
Si un identificador público no corresponde a ningún registro pendiente ni a ninguna plaza, tenga el
formato que tenga, entonces el sistema deberá responder «no encontrado» al consultarlo, verificarlo,
reenviarlo y completarlo, sin guardar nada, y la pantalla de verificación deberá indicar que el
enlace no es válido o ha caducado, con acceso al formulario de registro.

### RF-017 Plaza y registro real indistinguibles
El sistema deberá mostrar las mismas pantallas, textos y temporizadores, y responder con los mismos
códigos de estado, estructura, cabeceras y cookies, haciendo las mismas consultas a la base de datos,
al consultar, verificar, reenviar y completar, para un registro pendiente real cuyo código no se
acierta y para una plaza, desde que el formulario devuelve el identificador hasta su borrado. Ambos
deberán pasar a «no encontrado» (RF-016) en el mismo momento ante los mismos sucesos: al sustituirse
por un registro repetido (RF-005 de `procesos-pendientes`) y al borrarse por RF-020 o por la orden de
consola (RF-013 de `procesos-pendientes`).

### Servidor

### RF-018 Marketing en el registro
Cuando el formulario llegue con el consentimiento de marketing marcado, el sistema deberá guardar en
el registro pendiente el documento de marketing vigente aceptado. Cuando se repita el registro con un
correo que tiene un registro pendiente vigente, el sistema deberá conservar la elección de marketing
del primero, igual que el resto de sus datos (RF-005 de `procesos-pendientes`). Cuando se complete el
registro, el sistema deberá registrar la concesión de marketing en la misma operación que crea la
cuenta, con la fecha de compleción. Si el documento guardado ya no pertenece a la versión vigente,
entonces deberá crear la cuenta sin registrar la concesión. Si el formulario llega con el marketing
marcado y no hay documento de marketing vigente, o el indicado no pertenece a la versión vigente,
entonces el sistema deberá seguir con el registro sin marketing y sin ningún error.

### RF-019 Límite de frecuencia por IP
Si una IP (la IP real del cliente, RF-010 de `auth-headless`) supera el número configurado de
peticiones de verificar, reenviar o completar en una hora (60 por defecto, sumadas las tres),
entonces el sistema deberá rechazar las siguientes sin evaluarlas, con una respuesta de límite
superado que indique cuántos segundos esperar, igual sea cual sea el identificador. Consultar la
pantalla de verificación no cuenta para este límite.

### RF-020 Limpieza programada
El sistema deberá borrar de forma automática, sin intervención manual, cada registro pendiente no
completado y cada plaza entre 24 y 25 horas después de que caduque su último código, con el mismo
criterio y en la misma operación para ambos (RF-017).

### RF-021 Clientes
El sistema deberá admitir verificar, reenviar y completar desde el cliente web, con protección CSRF,
y desde el cliente de aplicación, sin ella, con las mismas reglas que RF-014 de `registro-api`.

### RF-022 Idioma
El sistema deberá mostrar las pantallas y devolver los mensajes del servidor de esta feature en
`es`, `pt-BR` y `en`, con el idioma de la interfaz (RF-013 de `registro-api`).

### RF-023 Valores configurables
El sistema deberá permitir ajustar por configuración, sin cambiar el código, la espera entre
reenvíos (60 s), el máximo de reenvíos por proceso (5), el límite por IP de RF-019 (60 por hora) y
el plazo de borrado de RF-020 (24 horas).

### RF-024 Límite superado en pantalla
Cuando el servidor rechace por límite superado una acción de cualquier pantalla del registro
(enviar el formulario, verificar, reenviar o completar), el sistema deberá mostrar un mensaje general
con la cuenta atrás del tiempo de espera que indica el servidor, conservar lo escrito y volver a
permitir la acción al llegar a cero.

## Supuestos
- S-01 El paso de contraseña exige el código junto con la contraseña (pregunta 1). *Por qué:* si
  bastara el identificador con el código validado, quien viera la URL o el correo podría fijar la
  contraseña durante la gracia. Aceptar de nuevo un código ya validado (RF-008, RF-012) contradice la
  última frase de RF-009 de `procesos-pendientes`. El plan buscará antes una solución dentro de esta
  feature con las funciones públicas existentes; si no la hay, se pasa `sdd-cambio` por
  `procesos-pendientes` antes de implementar (CF-6).
- S-02 Un identificador desconocido responde «no encontrado» y no se imita (cambio de decisión del
  usuario del 2026-10-30, que sustituye la respuesta a la pregunta 2). *Por qué:* un identificador
  inventado no está ligado a ningún correo; lo que impide saber si un correo tiene cuenta es la plaza
  (RF-025 de `procesos-pendientes`), y para eso basta con que plaza y registro real sean
  indistinguibles durante toda su vida (RF-017). *Coste:* la garantía depende por completo de que
  ambos sigan el mismo ciclo de vida. El 2026-10-30 se comprobó en el plan (D-11…D-18) y el código
  de `procesos-pendientes` que hoy coinciden: nacen en la respuesta del formulario, se resuelven
  igual, desaparecen a la vez al resolverse un registro repetido y la orden de consola los borra con
  el mismo criterio. Todo código nuevo que borre o sustituya uno debe tratar al otro igual. Siguen
  vigentes los riesgos aceptados en `procesos-pendientes` el 2026-10-18 (una cuenta creada o
  borrada por otra vía durante el proceso).
- S-03 Las 24 horas son un borrado físico; el registro deja de poder usarse a los 15 minutos de
  caducar su código (RF-011 de `procesos-pendientes`, sin cambios) (pregunta 3). Cuenta para el
  borrado todo registro no completado, con el código validado o sin validar, y toda plaza (RF-017),
  con un margen de hasta 1 hora (C-08). *Coste:* los datos de
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
  operaciones de `consentimientos`. Sin documento de marketing vigente no se muestra la casilla, y
  uno no vigente se ignora sin error (C-07). *Por qué:* el marketing es opcional y no debe impedir
  el registro, a diferencia de los términos.
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
- S-11 El temporizador lo da el servidor (RF-006), para que recargar no lo reinicie. Mientras la
  plaza no se ha resuelto, cuenta desde la caducidad que fija el formulario, y al resolverse se
  reajusta a la del código emitido (D-16 de `procesos-pendientes`): puede saltar unos segundos, igual
  en un registro real que en una plaza (C-05).
- S-12 Un identificador sustituido por un registro repetido (RF-005 de `procesos-pendientes`) pasa a
  «no encontrado» (RF-016) cuando se resuelve la petición nueva, igual sea registro real o plaza.
  Solo lo nota quien repitió el registro, que recibe un enlace nuevo.
- S-13 El límite por IP de RF-019 es de 60 peticiones por hora, sumadas verificar, reenviar y
  completar (C-01). Consultar la pantalla no cuenta: solo lee, y un identificador desconocido no
  guarda nada (RF-016).
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
  La divergencia la vigilan los casos compartidos de CF-8 (C-12).
- S-16 Se exige que una plaza y un registro real hagan el mismo trabajo, fijado por las consultas a la
  base de datos, no que su tiempo de respuesta medido sea igual (C-06). *Riesgo aceptado:* una
  diferencia de tiempo que no venga de las consultas (por ejemplo, de una caché) no se mide.
- S-17 Los casos compartidos de contraseña (CF-8) llevan el resultado que da el servidor, que es quien
  decide. Hoy el navegador ya diverge en uno: el servidor rechaza `²²²²²²²²²²²²` por ser solo
  números (`str.isdigit()`) y el navegador lo acepta (solo cuenta la categoría `Nd`). Que el test del
  frontend pase obliga a corregir `frontend/src/forms/passwordRules.ts`, de
  `componentes-base-accesibles`: el plan decide cómo hacerlo dentro de las reglas de `AGENTS.md`.

## Casos compartidos de contraseña
Resultado de las dos reglas que comprueban el navegador y el servidor (S-15); no incluye la
similitud, las comunes ni las filtradas.

| Contraseña | Caracteres | Al menos 12 | Solo números |
|---|---|---|---|
| `abcdefghijk` | 11 | no | no |
| `abcdefghijkl` | 12 | sí | no |
| 11 veces `😀` | 11 | no | no |
| 12 veces `😀` | 12 | sí | no |
| `123456789012` | 12 | sí | sí |
| `١٢٣٤٥٦٧٨٩٠١٢` | 12 | sí | sí |
| `²²²²²²²²²²²²` | 12 | sí | sí |
| `12345678901a` | 12 | sí | no |

## Fuera de alcance
- Inicio de sesión, pantalla de inicio de sesión y área privada (S-07).
- Restablecimiento de contraseña y sus pantallas.
- CAPTCHA u otras defensas contra bots, aparte de los límites de frecuencia.
- Cambiar las reglas de los campos del formulario, la edad mínima o la política de contraseñas.
- Revocar el marketing o aceptar términos nuevos tras el alta.
- Mostrar el número de intentos restantes (S-10).
- Imitar identificadores desconocidos: responden «no encontrado» (S-02).

## Criterios de finalización
- CF-1 Hay tests para cada RF, en backend y frontend. `pytest` y `pnpm --filter frontend test` están
  en verde con una cobertura ≥ 80 %, y `mypy`, `ruff`, `black`, `tsc`, ESLint y Prettier están
  limpios.
- CF-2 Un test demuestra que consultar, verificar, reenviar, completar y dejar caducar dan las mismas
  respuestas (código de estado, cuerpo, cabeceras y cookies), con los mismos plazos y las mismas
  consultas a la base de datos, para un registro real cuyo código no se acierta y para una plaza,
  incluido el bloqueo tras 5 intentos y el tope de reenvíos, y que ambos pasan a «no encontrado» en
  el mismo momento al sustituirse por un registro repetido y al borrarse por RF-020 (RF-017). Otro
  test demuestra que un identificador desconocido, de cualquier formato, responde «no encontrado» sin
  guardar nada (RF-016).
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
- CF-8 Un test del backend y otro del frontend, cada uno en su carpeta y sin compartir código (P-08),
  recorren los casos compartidos de contraseña y obtienen el resultado de la tabla (S-15, S-17).

## Historial de cambios
- 2026-10-29 — Creación (feature nueva) — RF: RF-001…RF-023 — Estado: pendiente de clarificar
- 2026-10-29 — Ajuste del borrador a petición del usuario: la pantalla de contraseña comprueba en
  el navegador la longitud y que no sea solo números — RF: RF-013 — S-15 añadido — Estado:
  pendiente de clarificar
- 2026-10-30 — Cambio de decisión del usuario sobre la pregunta 2 de la entrevista: un identificador
  desconocido responde «no encontrado» y no se imita; plaza y registro real se comportan igual hasta
  su borrado y pasan a «no encontrado» a la vez — RF: RF-015, RF-016, RF-017 y RF-020 ajustados;
  S-02, S-11 y S-12 ajustados; CF-2 ajustado — Estado: pendiente de clarificar
- 2026-10-30 — Clarificación (C-01…C-13; C-05 y C-09 cerrados por el cambio de decisión) — RF:
  RF-001, RF-003, RF-005, RF-010, RF-011, RF-012, RF-018, RF-019, RF-020 y RF-023 ajustados; RF-024
  añadido; S-03, S-06, S-13 y S-15 ajustados; S-16 y S-17, los casos compartidos de contraseña y CF-8
  añadidos — Estado: clarificado
- 2026-10-30 — Aprobación por el usuario — Estado: aprobada
