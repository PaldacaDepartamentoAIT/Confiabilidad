# Spec: perfil-y-cambio-contrasena
Estado: aprobada
Aprobación: ligera
Validación: estricta

## Objetivo (por qué)
Una vez que la persona inicia sesión y accede al área privada (`inicio-cierre-sesion`), todavía no puede consultar ni actualizar sus datos personales ni cambiar su contraseña desde su cuenta sin pasar por el flujo de contraseña olvidada. Esta feature completa la autogestión de la cuenta autenticada en los clientes web y de escritorio: permite visualizar la información básica del perfil, modificar nombre completo, fecha de nacimiento y país manteniendo inmutable el correo electrónico, y cambiar la contraseña verificando la actual mientras se cierran de inmediato todas las demás sesiones abiertas.

## Secuencia
1. La persona autenticada con los términos vigentes aceptados accede a `/profile` desde el menú lateral del área privada y visualiza su correo electrónico (solo lectura), su nombre completo, su fecha de nacimiento y su país de residencia (RF-001, RF-012).
2. Si modifica alguno de sus datos personales (nombre completo, fecha de nacimiento o país), el sistema valida los valores, guarda los cambios reales en la cuenta y deja constancia en el historial y la auditoría (RF-002…RF-005).
3. Si decide cambiar su contraseña, elige «Cambiar contraseña» en el menú de acciones de la tarjeta e introduce su contraseña actual y una nueva contraseña en el formulario correspondiente (RF-012).
4. Si la contraseña actual coincide, no está bloqueada por intentos fallidos y la nueva cumple la política vigente, el sistema actualiza la contraseña, conserva abierta la sesión actual, cierra de inmediato todas las demás sesiones activas, registra la auditoría y encola los avisos de seguridad correspondientes (RF-006…RF-010).

En este documento, las menciones a `RF-0xx` o `S-0x` de otras features remiten a sus respectivas specs (`usuario-personalizado`, `procesos-pendientes`, `correo-asincrono-plantillas`, `auditoria-eventos-seguridad`, `registro-api`, `registro-flujo`, `cambio-contrasena` e `inicio-cierre-sesion`).

## Requisitos funcionales

### Visualización y edición del perfil

### RF-001 Consulta del perfil autenticado
El sistema deberá permitir a la persona autenticada que tenga aceptados los términos vigentes (RF-011) visualizar su correo electrónico, nombre completo, fecha de nacimiento y país de residencia en la pantalla de perfil (`/profile`) y consultarlos mediante la API desde los clientes web y de escritorio. Ningún otro atributo de la cuenta (como idioma guardado o consentimientos) se expone ni se edita en esta pantalla.

### RF-002 Modificación de datos personales
Cuando la persona autenticada con los términos vigentes aceptados envíe una actualización de sus datos personales (con al menos uno de los campos nombre completo, fecha de nacimiento o país de residencia, admitiendo actualización parcial en la API y sin requerir su contraseña actual), el sistema deberá validar cada campo enviado con las reglas de `usuario-personalizado` (RF-003 nombre completo, RF-004 fecha de nacimiento y RF-005 país de residencia, conservando la excepción del relleno `"ZZ"` mientras el país no se modifique), guardar los valores normalizados, registrar la versión en el historial de cambios (RF-009 de `usuario-personalizado`) y devolver los datos actualizados del perfil.

### RF-003 Inmutabilidad del correo electrónico
El sistema deberá mostrar el correo electrónico como campo de solo lectura en la pantalla de perfil. Si una petición de modificación de datos personales incluye el campo de correo electrónico o intenta modificarlo, entonces el sistema deberá rechazar la petición con un error de validación en ese campo sin modificar ningún dato de la cuenta.

### RF-004 Errores de validación en el perfil
Si la petición de modificación del perfil no incluye ninguno de los tres campos editables, incluye campos desconocidos distintos de `email` (RF-003), falta algún dato obligatorio en la pantalla o algún valor incumple sus reglas de validación, entonces el sistema deberá rechazar la petición sin modificar la cuenta ni registrar eventos de auditoría, devolviendo los errores con un código estable y un mensaje descriptivo por cada campo o error general.

### RF-005 Edición sin cambios reales y auditoría de perfil
Cuando una modificación de datos personales altere efectivamente al menos uno de los campos guardados (nombre completo, fecha de nacimiento o país, comparados tras su normalización), el sistema deberá registrar un evento de auditoría de edición de perfil (`RF-010` de `auditoria-eventos-seguridad`). Si los valores enviados coinciden exactamente con los ya guardados tras normalizarlos, entonces el sistema deberá responder con éxito y los datos vigentes del perfil sin registrar ningún evento de auditoría.

### Cambio de contraseña y cierre de otras sesiones

### RF-006 Cambio de contraseña con contraseña actual
Cuando la persona autenticada con los términos vigentes aceptados envíe su contraseña actual y una nueva contraseña, la operación no esté bloqueada por intentos fallidos (RF-008), la contraseña actual coincida con la de la cuenta y la nueva contraseña cumpla la política vigente del sistema (RF-022 de `procesos-pendientes`, evaluada con el correo y el nombre vigentes de la cuenta), el sistema deberá actualizar la contraseña de la cuenta y confirmar el éxito del cambio. Una nueva contraseña igual a la actual deberá aceptarse si cumple la política de contraseñas.

### RF-007 Rechazo por contraseña actual incorrecta o nueva contraseña inválida
Si la contraseña actual no coincide con la de la cuenta o la nueva contraseña incumple la política de contraseñas (o falta alguno de los campos), entonces el sistema deberá rechazar el cambio de contraseña sin modificar la cuenta ni cerrar ninguna sesión, devolver los errores asociados a cada campo con un código estable y un mensaje descriptivo, y no registrar ningún evento de auditoría de fallo (`RF-010` de `auditoria-eventos-seguridad`) ni enviar correos. Cuando la contraseña actual sea incorrecta, el intento fallido se contabilizará en RF-008 aunque la nueva contraseña falte o también incumpla su política.

### RF-008 Límite de intentos fallidos en el cambio de contraseña
Cuando una petición de cambio de contraseña falle porque la contraseña actual es incorrecta, el sistema deberá sumar el intento al contador de fallos de la cuenta (compartido entre todas sus sesiones) dentro de la ventana configurada (5 intentos en 5 minutos por defecto, RF-014). Si se alcanza el número máximo configurado de intentos fallidos dentro de esa ventana, entonces el sistema deberá rechazar temporalmente las siguientes peticiones de cambio de contraseña de la cuenta durante el periodo de bloqueo configurado (5 minutos por defecto) sin evaluar las contraseñas, manteniendo abierta la sesión actual e indicando los segundos restantes de espera. Cuando un cambio de contraseña tenga éxito, el sistema deberá reiniciar dicho contador.

### RF-009 Conservación de la sesión actual y cierre de las demás sesiones
Cuando se complete un cambio de contraseña (RF-006), el sistema deberá mantener activa de forma transparente la sesión desde la que se realizó la operación —tanto en el cliente web como en el de escritorio, sin exigir volver a iniciar sesión ni perder las credenciales de la sesión en curso— e invalidar de inmediato en el servidor todas las demás sesiones abiertas de esa cuenta, borrando sus filas del inventario de sesiones activas (`UserSession`) para que ninguna otra sesión web ni credencial de escritorio pueda volver a autenticar.

### RF-010 Auditoría y avisos por correo al cambiar la contraseña
Cuando se complete un cambio de contraseña, el sistema deberá, respecto de la operación confirmada:
1. Registrar un evento de auditoría de cambio de contraseña (`RF-010` de `auditoria-eventos-seguridad`).
2. Registrar un evento de auditoría de cierre de sesión (`RF-009` de `auditoria-eventos-seguridad`) por cada otra sesión activa que se haya cerrado efectivamente.
3. Encolar en la bandeja de salida (`correo-asincrono-plantillas`) el aviso de «contraseña cambiada» en el idioma guardado de la cuenta.
4. Encolar también el aviso de «cierre remoto de sesiones» en el idioma guardado de la cuenta únicamente si existía al menos otra sesión activa que se cerró al cambiar la contraseña.

### Acceso, pantallas y clientes

### RF-011 Bloqueo por términos pendientes o cuenta inactiva
Mientras la persona autenticada no tenga aceptada la versión vigente obligatoria de los términos (o no exista ninguna versión vigente publicada), el sistema deberá rechazar en la API las operaciones de consulta de perfil, edición de datos personales y cambio de contraseña, y redirigir a `/terms` en la pantalla `/profile`, conforme a `RF-011` y `RF-017` de `inicio-cierre-sesion`. Mientras la cuenta esté inactiva, deberá rechazar cualquier petición como no autenticada y cerrar las sesiones abiertas conforme a `RF-003` de `inicio-cierre-sesion`.

### RF-012 Pantalla de perfil y cambio de contraseña
El sistema deberá ofrecer en la ruta `/profile`, accesible desde el menú lateral del área privada (y redirigiendo a `/login` si no hay sesión válida), una pantalla privada conforme a [identidad-visual.md](../../docs/identidad-visual.md) con una tarjeta principal a ancho completo en modo de solo lectura por defecto (con el correo electrónico siempre deshabilitado y nombre completo, país y fecha de nacimiento en una fila horizontal) y un menú vertical de acciones en la cabecera («Editar», «Cambiar contraseña», y «Deshabilitar» deshabilitada hasta su propia feature):
1. **Información personal** (solo lectura por defecto, editable al elegir «Editar»): muestra el correo electrónico deshabilitado y permite editar nombre completo, fecha de nacimiento y país de residencia sin pedir la contraseña actual, con acciones «Cancelar» y «Guardar cambios». Si la cuenta conserva el país relleno `"ZZ"`, el selector mostrará un estado sin país seleccionado («Sin país asignado») y permitirá guardar cambios en nombre o fecha de nacimiento manteniendo `"ZZ"` si no se elige un país nuevo.
2. **Cambio de contraseña** (al elegir «Cambiar contraseña» en el menú): conmuta la tarjeta al formulario de contraseña actual y nueva contraseña una sola vez (con botón para mostrar u ocultar cada contraseña, lista de requisitos en vivo de la nueva contraseña coherente con `registro-flujo`, «Cancelar» y envío), sin campo de confirmación adicional.

Cuando la persona salga de un campo o envíe cualquiera de los dos formularios, el cliente deberá validar en local los campos obligatorios y reglas básicas del cliente, no enviar la petición si hay errores locales, mostrar cada error debajo de su campo (o un mensaje general ante bloqueos, errores de red o servidor), llevar el foco al primer campo con error al enviar, regresar al modo de solo lectura tras guardar con éxito y mostrar la confirmación mediante notificación flotante (*toast*). En el formulario de cambio de contraseña: tras un cambio exitoso se vaciarán ambos campos antes de volver a solo lectura; si falla la contraseña actual, se vaciará solo el campo de contraseña actual conservando la nueva; si el rechazo es solo por política de la nueva contraseña o por error de red o servidor, se conservarán ambos campos; si se pulsa «Cancelar» o cambia de modo, se descartan los valores escritos y errores; y si la respuesta indica bloqueo temporal (RF-008), se mostrará la cuenta atrás con el tiempo restante y se deshabilitará el envío hasta llegar a cero.

### RF-013 Clientes web, escritorio e idiomas
El sistema deberá admitir todas las operaciones de esta feature desde el cliente web (mediante sesión por cookie y protección CSRF en las peticiones que cambian estado) y desde el cliente de escritorio (mediante credencial de sesión en cabecera, exento de CSRF), mostrando todas las pantallas y devolviendo los mensajes de validación y error en español (`es`), portugués de Brasil (`pt-BR`) e inglés (`en`) según las reglas de idioma del proyecto.

### RF-014 Valores configurables del límite de intentos
El sistema deberá permitir ajustar por configuración, sin modificar el código, el número máximo de intentos fallidos de contraseña actual en el cambio de contraseña (5 por defecto), su ventana de recuento (5 minutos por defecto) y la duración del bloqueo temporal (5 minutos por defecto) (RF-008).

### RF-015 Verificación desde consola
El sistema deberá permitir ejercitar y verificar la consulta y modificación de perfil y el cambio de contraseña (incluido el cierre de las demás sesiones y la conservación de la actual) desde consola o llamadas documentadas sin depender del frontend, conforme a `P-03`.

## Supuestos
- S-01 La pantalla de perfil y cambio de contraseña vive en una ruta dedicada (`/profile`) enlazada desde el menú lateral del área privada, manteniendo `/` enfocada en el resumen inicial y la gestión de sesiones activas (pregunta 1).
- S-02 La pantalla muestra y gestiona únicamente correo electrónico (solo lectura), nombre completo, fecha de nacimiento, país de residencia y cambio de contraseña; editar el idioma guardado de la cuenta, gestionar consentimientos de marketing o mostrar metadatos adicionales (como fecha de alta o último acceso) queda fuera de alcance (pregunta 2).
- S-03 Una nueva contraseña igual a la vigente se acepta si cumple la política de contraseñas del proyecto, manteniendo la misma regla que S-09 de `cambio-contrasena` (pregunta 3).
- S-04 Si se introduce mal la contraseña actual, se aplica un límite por cuenta configurable (5 intentos en 5 minutos con bloqueo de 5 minutos por defecto) sin cerrar la sesión actual, contabilizando cualquier fallo de la contraseña actual aunque la nueva contraseña falte o también sea inválida (pregunta 4 y C-01).
- S-05 Al cambiar la contraseña con éxito se encola siempre el aviso de «contraseña cambiada» y, si había al menos otra sesión abierta que se cerró, también el aviso de «cierre remoto de sesiones» (`RF-001` y `RF-009` de `correo-asincrono-plantillas`), además de registrar auditoría del cambio de contraseña y del cierre de cada sesión afectada (pregunta 5). *Nota:* enviar ambos avisos prioriza informar por separado tanto del cambio de clave como del cierre de otras sesiones abiertas; si en el futuro se quisiera unificar en un solo correo, requerirá cambio en la spec.
- S-06 En la API de edición de perfil, enviar el campo `email` (aunque coincida con el actual) se rechaza explícitamente con un error de validación para reforzar el contrato de inmutabilidad (pregunta 6).
- S-07 El formulario de cambio de contraseña pide la contraseña actual y la nueva contraseña una sola vez, con control de visibilidad y lista de requisitos en vivo igual que en el registro, sin segundo campo de repetición (pregunta 7).
- S-08 La edición de perfil admite actualización parcial en la API siempre que se envíe al menos uno de los tres campos editables y ningún campo desconocido; cuando los datos enviados tras normalizarse son idénticos a los actuales, la operación responde con éxito sin registrar `profile_edited` ni generar ruido en auditoría (pregunta 8 y C-03).
- S-09 En `inicio-cierre-sesion` (`RF-010`), cualquier cambio de contraseña en la cuenta invalidaba todas las sesiones abiertas; en esta feature, cuando el cambio lo inicia el propio usuario autenticado conociendo su contraseña actual, la sesión en curso permanece abierta de forma transparente y solo se cierran las demás sesiones. Los cambios de contraseña por restablecimiento olvidado o administración siguen invalidando todas las sesiones.

## Fuera de alcance
- Modificación del correo electrónico (requeriría un flujo propio de verificación del nuevo correo).
- Edición del idioma preferido guardado en la cuenta o gestión de consentimientos (términos o marketing) desde `/profile`.
- Deshabilitación o borrado de la cuenta por su titular (`S-04` de `usuario-personalizado`).
- Visualización del historial de cambios del perfil (`HistoricalRecords`) o del historial de auditoría (`SecurityEvent`) por el usuario final.
- Mostrar la fecha de alta o el último acceso en `/profile`.
- Restablecimiento de contraseña olvidada en pantalla (`cambio-contrasena` ya cubre la lógica en consola y su API/UI son otra feature).
- Segundo factor de autenticación (2FA / MFA) como confirmación adicional para editar datos o cambiar contraseña.

## Criterios de finalización
- CF-1 Hay tests para cada RF en backend y frontend. `pytest` y `pnpm --filter frontend test` están en verde con cobertura ≥ 80 %, y `mypy`, `ruff`, `black`, `tsc`, ESLint y Prettier están limpios.
- CF-2 Tests de backend demuestran que el usuario autenticado con términos aceptados puede consultar su perfil y modificar parcialmente o por completo nombre, fecha de nacimiento y país con las reglas de `usuario-personalizado` (conservando `"ZZ"` si no se cambia el país), que intentar enviar `email`, una petición vacía o campos desconocidos se rechaza explícitamente, y que guardar sin cambios reales no genera evento de auditoría `profile_edited` (RF-001…RF-005).
- CF-3 Tests de backend demuestran que cambiar la contraseña requiere la contraseña actual correcta y una nueva contraseña conforme a la política, que los intentos fallidos de contraseña actual (5 en 5 minutos por defecto por cuenta, incluso si la nueva contraseña también falla) activan el bloqueo temporal de 5 minutos por defecto sin cerrar la sesión actual, y que los rechazos no alteran la cuenta, no cierran sesiones, no envían correos ni registran eventos de auditoría de fallo (RF-006…RF-008).
- CF-4 Tests de backend demuestran que, tras cambiar la contraseña en web (cookie) o en escritorio (token), la sesión actual sigue autenticando sin interrupción mientras todas las demás sesiones abiertas quedan invalidadas de inmediato y desaparecen de `UserSession`, registrando auditoría de cambio de contraseña y de cierre de cada sesión cerrada, y encolando el aviso de contraseña cambiada (y el de cierre remoto de sesiones solo cuando había otras sesiones cerradas) (RF-009, RF-010).
- CF-5 Tests demuestran el bloqueo de todas las operaciones de la feature ante términos vigentes pendientes o cuenta inactiva, tanto en web como en escritorio (RF-011, RF-013).
- CF-6 Tests de frontend demuestran la ruta `/profile` en el menú lateral, la tarjeta única en solo lectura con el correo deshabilitado y el menú contextual de tres puntos, la preservación del estado sin país para `"ZZ"`, la validación en cliente y errores bajo cada campo, la confirmación mediante notificación flotante (*toast*) al guardar datos personales o cambiar la contraseña, el cambio de contraseña con vaciado selectivo de campos y cuenta atrás ante bloqueo, las redirecciones de sesión/términos y el soporte multiidioma (`es`, `pt-BR`, `en`) y de accesibilidad (RF-012, RF-013).
- CF-7 Se documenta cómo ejercitar y probar la feature desde consola/API y desde la aplicación (RF-015).

## Historial de cambios
- 2026-11-24 — Creación (feature nueva) — RF: RF-001…RF-015 — Estado: pendiente de clarificar
- 2026-11-25 — Clarificación (C-01…C-04) — RF: RF-002, RF-004, RF-007, RF-008, RF-012, RF-014 ajustados; S-04, S-08, CF-2, CF-3 y CF-6 ajustados — Estado: clarificado
- 2026-11-25 — Aprobación por el usuario — Estado: aprobada
- 2026-11-26 — Cambio en `RF-012`, `Secuencia` y `CF-6`: tarjeta única con menú contextual de tres puntos y confirmaciones por notificación flotante (*toast*) — Estado: aprobada
- 2026-11-27 — Validación: CUMPLIDA (RF-001…RF-015 y CF-1…CF-7 verificados sobre `feat/perfil-y-cambio-contrasena` tras `E-05`)
