# Spec: procesos-pendientes (registro pendiente)
Estado: aprobada
Aprobación: ligera

## Objetivo (por qué)
El registro exige demostrar acceso al correo con un código antes de crear la cuenta. Esta feature
guarda los registros pendientes, aplica sus reglas y permite completar el registro desde consola.
El cambio de contraseña, que usa el mismo mecanismo, se especificará en una feature aparte (S-11).
Los diagramas aportados por el usuario son la referencia:
[ER](diagramas/er.png), [flujo de registro](diagramas/flujo-registro.png) y
[flujo de cambio de contraseña](diagramas/flujo-cambio-contrasena.png).

## Secuencia del registro
1. La persona rellena el formulario y lo envía.
2. Si los datos son válidos, la persona recibe al momento un identificador público. Fuera de la
   respuesta, sus datos se guardan en un registro pendiente con ese identificador y se emite un
   código, que le llega por correo (RF-001, RF-002, RF-007, RF-008, RF-024).
3. La persona introduce el código, que queda validado (RF-009).
4. La persona introduce su contraseña.
5. Se crea la cuenta con los datos del registro pendiente y la contraseña, y se borra el registro
   pendiente (RF-020).

## Requisitos funcionales
### RF-001 Registro pendiente
El sistema deberá guardar, para cada registro pendiente, el correo, el nombre completo, la fecha de
nacimiento, el país, un identificador público, la huella del código vigente, su caducidad, el
número de intentos fallidos, si el código ya se validó (y cuándo), la fecha de alta y, si se
indicaron al empezarlo, el documento de términos aceptado y el documento de marketing aceptado (cada
uno con su versión y su idioma).

### RF-002 Datos del registro pendiente válidos
Cuando se guarde un registro pendiente, el sistema deberá normalizar y validar correo, nombre,
fecha de nacimiento y país con las mismas reglas que la cuenta de usuario (RF-001 y RF-003…RF-005
de `usuario-personalizado`) y rechazar el guardado si alguno no es válido.

### RF-003 Un registro pendiente por correo
Si se intenta guardar un registro pendiente cuyo correo coincide, sin distinguir mayúsculas, con
el de otro registro pendiente, entonces el sistema deberá rechazarlo, también en cargas masivas y
escrituras directas a la base de datos.

### RF-004 Correo con cuenta
Si el correo de un registro pendiente coincide, sin distinguir mayúsculas, con el de una cuenta
existente (activa o no), entonces el sistema no deberá guardar el registro pendiente.

### RF-005 Registro repetido
Cuando se solicite un registro para un correo que ya tiene un registro pendiente vigente, el
sistema deberá conservar los datos existentes, incluidos los documentos de términos y de marketing
aceptados (o la ausencia de este último), descartar los nuevos, asignar un identificador
público nuevo, emitir un código nuevo, poner los intentos a 0 y anular la validación del código
(S-06).

### RF-006 OBSOLETO — Solicitud de cambio de contraseña
Movido a la feature de cambio de contraseña (S-11).

### RF-007 Identificador público
El sistema deberá asignar a cada proceso un identificador público aleatorio, imposible de deducir
del correo o de la cuenta, y único entre los procesos de su tipo.

### RF-008 Código
Cuando se emita un código, el sistema deberá generar uno de 6 dígitos, vigente 15 minutos por
defecto (RF-019), entregarlo una sola vez para su envío y guardar solo una huella que no permita
recuperarlo sin un secreto del servidor, aunque se disponga de la base de datos. Mientras su
correo esté pendiente de entrega, el código podrá guardarse además cifrado con una clave propia,
que se borra al entregarse, descartarse o fallar de forma definitiva el correo (RF-018 de
`correo-asincrono-plantillas`).

### RF-009 Verificación del código
Cuando se presente un código para un proceso, el sistema deberá aceptarlo solo si coincide, no ha
caducado y no se han agotado los intentos, y al aceptarlo deberá marcar el código del proceso como
validado. Si el código no coincide, entonces el sistema deberá sumar un intento fallido. Si el
proceso ya tiene el código validado, entonces el sistema deberá rechazar cualquier código que se
presente, salvo en un registro pendiente. Ahí, si el código coincide y no se han agotado los
intentos, el sistema deberá aceptarlo de nuevo sin cambiar nada mientras el proceso no haya caducado
(RF-011), aunque el código sí haya caducado; si no coincide, deberá tratarlo igual que en un
proceso sin validar: sumar un intento fallido mientras el código esté vigente, o rechazarlo por
código caducado si ya no lo está (S-12).

### RF-010 Bloqueo por intentos
Si un proceso acumula el máximo de intentos fallidos (5 por defecto, RF-019), entonces el sistema
deberá rechazar cualquier código posterior, incluso el correcto, hasta que se emita uno nuevo, que
reinicia los intentos.

### RF-011 Caducidad del proceso
Un proceso caduca al cumplirse lo primero de: 15 minutos después de que caduque su código vigente,
o 1 hora desde su alta (valores por defecto, RF-019). Mientras un proceso esté caducado, el
sistema deberá rechazar sus códigos, impedir que se complete y no tenerlo en cuenta para RF-005.

### RF-012 Fin del proceso
Cuando se complete un proceso con el código validado, el sistema deberá borrarlo. Si se intenta
completar un proceso sin el código validado o caducado, entonces el sistema deberá rechazarlo. Si
al completar un registro pendiente su correo ya pertenece a una cuenta, entonces el sistema deberá
rechazarlo y borrar el registro pendiente.

### RF-013 Limpieza
El sistema deberá permitir borrar desde consola todos los procesos caducados, informando de
cuántos borró.

### RF-014 OBSOLETO — Borrado de cuenta
Movido a la feature de cambio de contraseña (S-11).

### RF-015 Rotación del secreto de los códigos
Cuando se cambie el secreto que protege las huellas de los códigos, el sistema deberá seguir
aceptando, durante un periodo de transición configurable (RF-019), los códigos emitidos con el
secreto anterior.

### RF-016 Reenvío del código
Cuando se reenvíe el código de un proceso vigente sin el código validado, el sistema deberá
conservar su identificador público, poner los intentos a 0 y responder de inmediato, y emitir el
código nuevo, con su correo, fuera de la respuesta. Si el proceso ya tiene el código validado,
entonces el sistema deberá rechazar el reenvío.

### RF-017 Registros pendientes caducados del mismo correo
Cuando se cree un registro pendiente, el sistema deberá borrar antes cualquier registro pendiente
caducado con el mismo correo.

### RF-018 OBSOLETO — Cuenta inactiva
Movido a la feature de cambio de contraseña (S-11).

### RF-019 Límites configurables
El sistema deberá permitir ajustar por configuración, sin cambiar el código, el máximo de
intentos fallidos, la vigencia del código, la gracia tras caducar el código, la vida máxima del
proceso, el periodo de transición del secreto (RF-015), el tiempo máximo de espera del servicio de
contraseñas filtradas (RF-022) y el tiempo durante el que se reintenta el trabajo de empezar el
registro (RF-024; 5 minutos por defecto).

### RF-020 Completar el registro
Cuando se complete un registro pendiente con el código validado y una contraseña, el sistema
deberá, en una sola operación, crear la cuenta con el correo, el nombre, la fecha de nacimiento y
el país guardados, la contraseña indicada y el correo marcado como verificado, y borrar el
registro pendiente. Si el registro pendiente tiene un documento de términos aceptado que pertenece
a la versión vigente, entonces el sistema deberá registrar en esa misma operación su aceptación
(RF-006 de `consentimientos`), con la fecha de compleción; si no lo tiene o ya no es de la versión
vigente, deberá crear la cuenta sin registrar ninguna aceptación. Si el registro pendiente tiene un
documento de marketing aceptado que pertenece a la versión vigente, entonces el sistema deberá
registrar en esa misma operación la concesión de marketing (RF-008 de `consentimientos`), con la
fecha de compleción; si no lo tiene, ya no es de la versión vigente o `consentimientos` rechaza la
concesión por cualquier otro motivo, deberá crear la cuenta sin registrar ninguna concesión. Si
la contraseña no cumple la política de RF-022, entonces deberá rechazarlo
indicando cada regla incumplida y conservar el registro pendiente.

### RF-021 OBSOLETO — Completar el cambio de contraseña
Movido a la feature de cambio de contraseña (S-11).

### RF-022 Política de contraseñas
El sistema deberá rechazar una contraseña si:
- tiene menos de 12 caracteres;
- se parece demasiado al correo o al nombre guardados en el registro pendiente;
- está en una lista de contraseñas comunes;
- consta como filtrada en el servicio público de contraseñas filtradas, consultado sin enviar la
  contraseña ni su huella completa.

Si el servicio de contraseñas filtradas no responde en el tiempo configurado (RF-019), entonces el
sistema deberá omitir solo esa comprobación y dejar constancia del fallo en el registro de eventos
del servidor.

### RF-023 Ejecución desde consola
El sistema deberá permitir recorrer desde consola cada paso del registro, sin frontend ni API:
iniciarlo con sus datos, presentar el código, reenviarlo y completarlo con una contraseña. Cada
paso deberá mostrar el identificador público y el resultado de la operación, igual para un correo
con cuenta que sin ella (RF-024, RF-025); nunca el código.

### RF-024 Empezar el registro
Cuando se solicite un registro con datos válidos (RF-002) y, opcionalmente, el documento de
términos aceptado y el documento de marketing aceptado, el sistema deberá devolver de inmediato
un identificador público nuevo, con el mismo formato tenga o no cuenta el correo, y hacer fuera de
la respuesta todo el trabajo que depende de ello: comprobar cuentas y registros pendientes (RF-004,
RF-005, RF-017), crear o reemplazar el registro pendiente con ese identificador y emitir el código.
Si el documento de marketing indicado no existe o no pertenece a la versión vigente, entonces el
sistema deberá descartarlo, sin error, y guardar el registro pendiente sin marketing.
Si el nombre, la fecha de nacimiento, el país o el formato del correo no son válidos, entonces el
sistema deberá rechazarlos en la propia respuesta, indicando cada error. Que el correo pertenezca a
una cuenta o tenga un registro pendiente nunca se indicará en la respuesta. Si el trabajo de fuera
de la respuesta falla, entonces el sistema deberá reintentarlo solo durante el tiempo configurado
(RF-019). Si sigue fallando, el identificador se comportará como uno sin registro detrás (RF-025),
sin enviar correo, y el fallo quedará en el registro de eventos del servidor.

### RF-025 Identificador sin registro detrás
Si el correo de una solicitud de registro pertenece a una cuenta (RF-004), entonces el
identificador devuelto no tendrá registro pendiente detrás. Verificarlo, reenviarlo, completarlo y
dejarlo caducar deberá dar los mismos resultados, en el mismo orden y con los mismos plazos, que un
registro pendiente real cuyo código nunca se acierta, incluido el bloqueo por intentos (RF-010). El
trabajo que distinga uno de otro (emitir el código y enviar el correo) se hará fuera de la
respuesta. Una solicitud nueva con el mismo correo anula el identificador sin registro anterior,
igual que RF-005 con un registro real.

## Supuestos
- S-01 Esta feature no incluye API, pantallas, mensajes neutros, redirecciones, el límite de
  frecuencia del reenvío ni el cierre de sesiones. El envío de correos, incluido el aviso "ya tienes
  cuenta", es de `correo-asincrono-plantillas`; el identificador sin registro detrás se añadió el
  2026-10-14 (RF-025). La API será la feature siguiente y
  reutilizará las mismas operaciones que usan los comandos de RF-023, para que el frontend las
  consuma sin rehacer reglas.
- S-02 Los diagramas del usuario (ER, flujo de registro y flujo de cambio de contraseña, recibidos
  el 2026-10-01) son la referencia y se guardan en `specs/procesos-pendientes/diagramas/`.
- S-03 Términos y marketing se gestionan en la feature de consentimientos. El registro pendiente
  guarda el documento de términos aceptado en el formulario y su aceptación se registra al
  completar el registro (cambio del 2026-10-21, pedido por `registro-api`, S-03 y RF-009). Los
  registros empezados desde consola o antes de este cambio no tienen documento y se completan sin
  aceptación (S-12 y C-13 de `registro-api`). Del mismo modo, guarda el documento de marketing si
  se marcó en el formulario, y su concesión se registra al completar el registro (cambio del
  2026-10-30, pedido por `registro-flujo`, S-06 y RF-018); sin documento, o si ya no es de la
  versión vigente, la cuenta se crea sin concesión, sin error. Un documento de marketing que no
  existe o no es vigente al empezar se descarta (C-03), y la consola no indica el de marketing,
  igual que el de términos (C-02). *Riesgo aceptado (C-01):* si `consentimientos` rechaza la
  concesión al completar por cualquier motivo, la cuenta se crea sin ella y sin dejar rastro, como
  hoy con los términos; un consentimiento que la persona dio puede perderse sin que nadie lo note.
- S-04 La gracia de 15 minutos tras caducar el código (diagrama de registro) permite completar el
  registro tras validar el código y cerrar la ventana.
- S-05 Crear la cuenta se hace aquí (RF-020). Los correos de código y el aviso "ya tienes cuenta"
  los envía `correo-asincrono-plantillas`.
- S-06 Repetir el registro con un correo que tiene un registro pendiente cambia su identificador
  público y anula la validación del código (RF-005; confirmado por el usuario en C-01). *Por qué:*
  si el identificador existente se entregara a quien repite el formulario, un tercero podría fijar
  la contraseña de un registro con el código validado o agotar sus intentos. *Coste:* el enlace
  anterior deja de valer y hay que usar el último correo.
- S-07 Un código de 6 dígitos con 5 intentos por código: el freno real a la fuerza bruta es el
  límite de frecuencia del reenvío (S-01), que fija la feature de flujo.
- S-08 El periodo de transición del secreto (RF-015) vale por defecto lo mismo que la vida máxima
  del proceso (1 hora): pasado ese tiempo, ningún proceso con un código anterior sigue vigente.
- S-09 El usuario aprobó (2026-10-01) usar el servicio público Have I Been Pwned para RF-022. Es
  una dependencia externa, y si no responde se acepta la contraseña (fallo abierto). *Riesgo:*
  mientras el servicio no esté disponible, pueden pasar contraseñas filtradas.
- S-10 Los comandos de RF-023 ya no muestran el código (cambio del 2026-10-14). *Por qué:* la API
  reutilizará las mismas operaciones (S-01), y una operación que devolviera el código, o si el
  correo tiene cuenta, lo filtraría a la API. En desarrollo, el código se lee en el correo que
  muestra el proveedor local en la salida del worker.
- S-11 El cambio de contraseña será una feature aparte que reutilizará las reglas de esta
  (RF-007…RF-011, RF-015, RF-016, RF-019, RF-022) con estas decisiones ya tomadas: una solicitud
  por cuenta, que se reemplaza al pedir otra (pregunta 4 y C-08); borrado al completar o caducar;
  borrado al borrar la cuenta (antes RF-014); una cuenta inactiva no puede pedirla y la que tenga
  en curso muere al caducar (C-05, antes RF-018); completar fija la contraseña y borra la
  solicitud (antes RF-021); cerrar sesiones y avisar por correo, en su flujo.
- S-12 En el registro, un código ya validado se puede presentar de nuevo (cambio del 2026-10-30,
  pedido por `registro-flujo`, S-01, RF-008 y RF-012). *Por qué:* el paso de contraseña vuelve a
  enviar el código, y recargar la pantalla obliga a escribirlo otra vez. Además, rechazar sin
  comparar delataría que el registro es real, porque un identificador sin registro detrás (RF-025)
  nunca está validado y siempre suma un intento. El cambio de contraseña conserva la regla anterior.
  Se acepta de nuevo hasta que caduca el proceso, no el código (C-01), para que recargar la pantalla
  durante la gracia de S-04 no deje a la persona sin forma de continuar. Si un registro validado se
  bloquea por intentos, el reenvío sigue prohibido (RF-016) y la salida es repetir el formulario
  (RF-005), que anula la validación y da un identificador y un código nuevos (C-02). *Riesgo
  aceptado:* quien tenga el enlace puede bloquear un registro ya validado con 5 códigos incorrectos y
  obligar a su dueño a repetir el formulario.

## Fuera de alcance
- API y pantallas (ver S-01). El envío de correos es de `correo-asincrono-plantillas`.
- Cambio de contraseña (ver S-11).
- Términos, marketing y el resto de tablas del diagrama ER (MarketingConsent, Terms, UserTerms,
  UserSession, SecurityEvent).
- Programar la limpieza periódica (RF-013 solo ofrece la orden).
- Histórico de procesos: los terminados o caducados no se conservan.

## Criterios de finalización
- CF-1 Las migraciones se aplican sobre la base de `usuario-personalizado`, con unicidad
  garantizada por la base de datos en el identificador público y en el correo del registro
  pendiente (sin distinguir mayúsculas).
- CF-2 Hay tests para cada RF; la suite `pytest` está en verde con cobertura ≥ 80 % y
  `mypy`/`ruff`/`black` están limpios.
- CF-3 Los diagramas están guardados en `specs/procesos-pendientes/diagramas/` y enlazados desde
  la spec.
- CF-4 El registro se puede recorrer de principio a fin con los comandos de RF-023 y el código
  leído del correo que muestra el proveedor local, y los pasos están documentados en `resumen.md`.
- CF-5 Un test demuestra que, para un correo con cuenta, verificar, reenviar, completar y dejar
  caducar el identificador devuelto da los mismos resultados que un registro pendiente real cuyo
  código nunca se acierta (RF-025).

## Historial de cambios
- 2026-10-01 — Creación (feature nueva) — RF: RF-001…RF-014 — Estado: pendiente de clarificar
- 2026-10-01 — Clarificación (C-01…C-09) — RF: RF-001, RF-005, RF-006, RF-008…RF-012 ajustados;
  RF-015…RF-023 y la secuencia del registro añadidos; S-01, S-05, S-06 ajustados; S-08…S-10
  añadidos — Estado: clarificado
- 2026-10-01 — División: el cambio de contraseña pasa a una feature aparte — RF: RF-006, RF-014,
  RF-018, RF-021 OBSOLETO; RF-017, RF-022, RF-023 ajustados; S-11 añadido — Estado: clarificado
- 2026-10-07 — Validación: NO CUMPLIDA (1.ª) — RF-011, RF-012, RF-017, RF-019 (tests) y RF-023
  (código: `public_id` que empezaban por "-"); corregido con T-022…T-025.
- 2026-10-07 — Validación: NO CUMPLIDA (2.ª) — RF-017 (test con espacios); corregido con T-026,
  más T-027 (rango del código) y T-028 (respuesta cortada de Have I Been Pwned).
- 2026-10-07 — Validación: cerrada con riesgo residual aceptado — Riesgos: (1) concurrencia
  protegida con bloqueos de fila pero sin probar con transacciones reales; (2) si otra vía crea la
  cuenta entre la comprobación y el alta en `complete`, sale un `IntegrityError` sin traducir y el
  registro pendiente se conserva en vez de borrarse (RF-012) hasta el siguiente intento; (3) Have I
  Been Pwned nunca probado contra el servicio real; (4) `makemessages` no ejecutado.
- 2026-10-14 — Cambio por `correo-asincrono-plantillas` (S-07, S-08): empezar el registro devuelve
  siempre un identificador y la consola deja de mostrar el código — RF: RF-008 y RF-023
  modificados; RF-024 y RF-025 añadidos; secuencia, S-01, S-05, S-10, fuera de alcance y CF-4
  ajustados; CF-5 añadido. Clarificado (C-01…C-04): RF-016, RF-019, RF-024 y RF-025 ajustados —
  Estado: impacto analizado
- 2026-10-15 — Modo de aprobación: pasa de fuerte (sin línea `Aprobación:`) a ligero, a petición
  explícita del usuario — RF: ninguno
- 2026-10-18 — Validación del cambio del 2026-10-14: cerrada con riesgo residual aceptado (cuatro
  validaciones independientes de la equivalencia entre plaza y registro real; correcciones hasta
  T-047). Riesgos aceptados: una cuenta creada por otra vía mientras hay un registro pendiente
  vigente, o borrada entre dos peticiones, puede distinguir la plaza del registro real — RF:
  ninguno modificado
- 2026-10-21 — Cambio por `registro-api` (S-03, RF-009): el registro pendiente guarda el documento
  de términos aceptado y completar el registro registra su aceptación — RF: RF-001, RF-005, RF-020
  y RF-024 modificados; S-03 ajustado. Clarificado sin hallazgos; impacto: sin cambios en el plan,
  lo implementan T-009…T-011 y T-016 de `registro-api` — Estado: impacto analizado
- 2026-10-22 — Validación del cambio del 2026-10-21: CUMPLIDA, dentro de la 6.ª validación de
  `registro-api` (RF-001, RF-005, RF-020 y RF-024 cumplidos con la suite en verde) — RF: ninguno
  modificado
- 2026-10-30 — Cambio por `registro-flujo` (S-06, RF-018): el registro pendiente guarda el
  documento de marketing aceptado, lo conserva al repetirse el registro y completar el registro
  registra su concesión — RF: RF-001, RF-005, RF-020 y RF-024 modificados; S-03 ajustado.
  Clarificado (C-01…C-03): RF-020 y RF-024 ajustados; S-03 ajustado. Impacto: sin cambios en el
  plan; lo implementan el plan y las tareas de `registro-flujo`, que actualizan también
  `resumen.md` — Estado: impacto analizado
- 2026-10-30 — Cambio por `registro-flujo` (S-01, RF-008, RF-012): en un registro pendiente, un
  código ya validado se compara de nuevo; si coincide se acepta sin cambios y si no, suma un intento
  — RF: RF-009 modificado; S-12 añadido. Clarificado (C-01, C-02): RF-009 y S-12 ajustados.
  Impacto: sin cambios en este plan; cambian M-01, D-01 y D-02 del plan de `registro-flujo`, que lo
  implementa, y los tests del código validado del servicio y de la auditoría — Estado: impacto
  analizado
