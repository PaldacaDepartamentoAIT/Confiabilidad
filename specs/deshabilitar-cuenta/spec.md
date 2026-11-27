# Spec: deshabilitar-cuenta
Estado: aprobada
Aprobación: ligera
Validación: estricta

## Objetivo (por qué)
Una persona autenticada puede consultar y editar su perfil y cambiar su contraseña (`perfil-y-cambio-contrasena`), pero aún no puede deshabilitar su propia cuenta de forma segura ni el sistema cuenta todavía con una referencia mínima a las empresas para impedir que un propietario abandone una empresa sin transferirla o eliminarla antes. Esta feature habilita la autodeshabilitación de la cuenta con reautenticación previa, introduce un modelo preliminar de empresas para bloquear la baja mientras el usuario sea propietario de alguna, revoca de inmediato todos sus accesos, permite a soporte reactivar la cuenta dentro de un plazo de 12 meses y purga definitivamente las cuentas deshabilitadas una vez vencido ese plazo.

## Secuencia
1. La persona autenticada accede a `/profile` desde el área privada y elige la opción de deshabilitar cuenta en el menú de acciones del perfil (RF-001, RF-014).
2. Si es propietaria de al menos una empresa (modelo preliminar, RF-002), la interfaz de deshabilitación le advierte de entrada que debe transferir o eliminar primero su empresa y mantiene inhabilitada la confirmación de baja; cualquier intento directo en la API también se rechaza antes de evaluar la contraseña (RF-003).
3. Si no es propietaria de ninguna empresa (ni es el último superusuario activo, RF-016), en el segundo paso de confirmación introduce su contraseña actual para reautenticarse y confirma la deshabilitación (RF-004, RF-014). Si falla repetidamente, se aplica un bloqueo temporal por intentos sin cerrar la sesión en curso, visible incluso si recarga `/profile` y vuelve a abrir la confirmación (RF-005, RF-014).
4. Al confirmarse la baja, el sistema deshabilita la cuenta registrando la fecha de deshabilitación, revoca de inmediato todas sus sesiones activas y credenciales en web y escritorio, invalida restablecimientos pendientes, registra el evento de auditoría y encola el aviso de cuenta deshabilitada; el cliente limpia la sesión local y redirige a `/login` con la confirmación y la información de reactivación vía soporte durante 12 meses (RF-006, RF-007, RF-014).
5. Mientras la cuenta esté deshabilitada, los intentos de acceso con correo y contraseña correctos suman al contador de fuerza bruta e informan si la cuenta está deshabilitada dentro del plazo de 12 meses (con contacto a soporte) o si ese plazo ya venció; los intentos con contraseña incorrecta o correo inexistente mantienen la respuesta neutra habitual (RF-008).
6. Si el titular contacta a soporte antes de que transcurran 12 meses desde la deshabilitación, soporte técnico o un superusuario puede reactivar la cuenta desde el panel de administración o desde consola (RF-009, RF-010). Una vez transcurridos 12 meses, la reactivación queda bloqueada y la cuarta tarea periódica integrada en `tareas-purga-y-alertas` elimina físicamente la cuenta conservando su historial y los registros de auditoría (RF-011, RF-012).

En este documento, las menciones a `RF-0xx` o `S-0x` de otras features remiten a sus respectivas specs (`usuario-personalizado`, `procesos-pendientes`, `cambio-contrasena`, `consentimientos`, `correo-asincrono-plantillas`, `auditoria-eventos-seguridad`, `inicio-cierre-sesion`, `perfil-y-cambio-contrasena` y `tareas-purga-y-alertas`).

## Requisitos funcionales

### Bloqueo por propiedad de empresa (modelo preliminar)

### RF-001 Deshabilitación de la propia cuenta desde perfil, API y consola
El sistema deberá permitir al titular autenticado (incluido personal `staff` o superusuario, salvo la protección del último superusuario activo de RF-016) deshabilitar su propia cuenta desde la opción de deshabilitación del menú de acciones en `/profile` (en los clientes web y de escritorio), mediante la API y desde consola de administración o pruebas (`P-03`), siempre que no sea propietario actual de ninguna empresa y supere la reautenticación (RF-003, RF-004).

### RF-002 Modelo preliminar de empresas
El sistema deberá incorporar un modelo preliminar de empresa compuesto por un nombre (sin exigir unicidad) y un único usuario propietario actual asociado (pudiendo un mismo usuario ser propietario de varias empresas), gestionable desde el panel de administración interno y desde consola para crear empresas de prueba y verificar la propiedad, dejando la creación, transferencia y eliminación de empresas por parte de los usuarios finales para una feature posterior (Módulo II).

### RF-003 Bloqueo preventivo y prioritario por propiedad de empresa
Mientras el usuario autenticado figure como propietario de al menos una empresa, el sistema deberá impedir que deshabilite su cuenta:
1. En la interfaz de deshabilitación abierta desde el menú de `/profile`, deberá mostrarse de forma visible desde el primer momento que el usuario es propietario de al menos una empresa y que debe transferirla o eliminarla primero, manteniendo inhabilitada la confirmación de baja.
2. En la API y en la operación de negocio, la comprobación de propiedad de empresa deberá ejecutarse antes de validar la contraseña actual (RF-004) y rechazar la solicitud indicando que debe transferir o eliminar su empresa primero, sin contabilizar intentos fallidos de contraseña ni cerrar ninguna sesión.

### Reautenticación y ejecución de la baja

### RF-004 Reautenticación con contraseña actual
Cuando un usuario que no posee empresas solicite deshabilitar su cuenta y la operación no esté bloqueada temporalmente (RF-005), el sistema deberá exigirle su contraseña actual en el momento de confirmar la baja. Si la contraseña actual falta o no coincide con la de la cuenta, entonces el sistema deberá rechazar la deshabilitación con un error de validación asociado al campo sin modificar la cuenta ni cerrar sesiones, y contabilizar el intento fallido cuando la contraseña sea incorrecta.

### RF-005 Límite de intentos fallidos en la reautenticación
Cuando una petición de deshabilitación falle por contraseña actual incorrecta, el sistema deberá sumar el intento a un contador propio de deshabilitación de cuenta, independiente del contador de cambio de contraseña (`RF-008` de `perfil-y-cambio-contrasena`), dentro de la ventana configurada (5 intentos en 5 minutos por defecto, configurable sin modificar el código). Si se alcanza el máximo configurado de intentos fallidos dentro de esa ventana, entonces el sistema deberá rechazar temporalmente las siguientes peticiones de deshabilitación durante el periodo de bloqueo configurado (5 minutos por defecto, configurable) sin evaluar la contraseña, manteniendo abierta la sesión actual e indicando los segundos restantes de espera. El estado de bloqueo vigente y sus segundos restantes deberán ser consultables al cargar `/profile` para mantener la cuenta atrás tras recargar la página.

### RF-006 Deshabilitación de la cuenta y revocación inmediata de accesos
Cuando la reautenticación sea válida y el usuario no sea propietario de ninguna empresa, el sistema deberá, en una misma operación atómica:
1. Marcar la cuenta como inactiva conservando todos sus datos (incluido su correo, contraseña y consentimientos) y registrar la fecha y hora exacta en UTC en que se deshabilitó.
2. Invalidar de inmediato todas las sesiones activas y credenciales de esa cuenta tanto en web como en escritorio (`RF-003` de `inicio-cierre-sesion`), de modo que ninguna petición posterior con ellas pueda volver a autenticar.
3. Invalidar cualquier proceso de restablecimiento de contraseña pendiente que perteneciera a esa cuenta.

### RF-007 Auditoría y aviso por correo al deshabilitar la cuenta
Cuando se complete la deshabilitación de la cuenta (RF-006), el sistema deberá registrar un evento de auditoría de deshabilitación de cuenta (`RF-010` de `auditoria-eventos-seguridad`) y encolar en la bandeja de salida (`RF-001` y `RF-009` de `correo-asincrono-plantillas`) el aviso de cuenta deshabilitada en el idioma guardado de la cuenta, que incluye la vía de contacto con soporte. Si la deshabilitación se rechaza por cualquier motivo, el sistema no deberá registrar evento de auditoría de fallo ni encolar ningún correo.

### Inicio de sesión tras la deshabilitación

### RF-008 Rechazo en el inicio de sesión para cuentas deshabilitadas
Si una persona intenta iniciar sesión con un correo y una contraseña válidos que corresponden a una cuenta deshabilitada (y la petición no está bloqueada por límites de frecuencia o intentos fallidos), entonces el sistema deberá rechazar el inicio de sesión sin abrir sesión ni emitir credencial, sumar el intento al contador de intentos fallidos (`RF-004` de `inicio-cierre-sesion`), registrar el evento de inicio de sesión fallido por cuenta inactiva (`RF-004` de `auditoria-eventos-seguridad`) y devolver un mensaje específico:
1. Si no ha vencido el plazo de 12 meses (RF-010), indicará que la cuenta está deshabilitada y que puede solicitar su reactivación contactando a soporte dentro de los 12 meses posteriores a la baja.
2. Si el plazo de 12 meses ya venció (y la cuenta aún no ha sido purgada), indicará que la cuenta está deshabilitada y que el plazo de 12 meses para reactivarla ya ha vencido.

Si el correo no existe o la contraseña no coincide, el sistema deberá mantener el rechazo neutro de credenciales incorrectas sin revelar el estado de la cuenta (`RF-002` de `inicio-cierre-sesion`).

### Reactivación por soporte y ventana de 12 meses

### RF-009 Reactivación de cuentas deshabilitadas por soporte técnico
Toda desactivación de cuenta (incluida la desactivación manual desde el panel de administración interno) deberá registrar la fecha y hora exacta en UTC en que quedó deshabilitada. Cuando no haya transcurrido el plazo configurable de 12 meses calendario en UTC desde esa fecha (RF-010), el sistema deberá permitir que un operador autorizado (miembro del grupo «Soporte técnico» o superusuario) desde el panel de administración interno, o un administrador desde consola (`P-03`), reactive la cuenta dejándola nuevamente activa, limpiando su fecha de deshabilitación y conservando su contraseña y consentimientos previos. El cambio deberá quedar registrado en el historial de cambios del usuario (`RF-009` de `usuario-personalizado`) con el autor cuando se conozca. Si un miembro del staff que no pertenece al grupo «Soporte técnico» ni es superusuario intenta reactivarla desde el panel, el sistema deberá impedirlo.

### RF-010 Bloqueo de reactivación transcurridos 12 meses
Si ha transcurrido el plazo configurable de 12 meses calendario en UTC o más desde la fecha de deshabilitación de una cuenta (en cuentas deshabilitadas un 29 de febrero, el vencimiento en un año no bisiesto se cumple el 28 de febrero a la misma hora UTC), entonces el sistema deberá rechazar cualquier intento de reactivación (tanto desde el panel de administración interno como desde consola) indicando que el plazo de 12 meses para reactivar la cuenta ha vencido. El plazo deberá ser configurable sin modificar el código (12 meses calendario por defecto) para facilitar pruebas y operación.

### RF-011 Purga periódica de cuentas deshabilitadas tras 12 meses
El sistema deberá incorporar la purga de cuentas deshabilitadas vencidas como una cuarta tarea periódica integrada en el mecanismo de ejecución, estado y alertas de `tareas-purga-y-alertas` (con frecuencia diaria por defecto, configurable sin modificar el código, y comando equivalente en consola). Cuando una cuenta deshabilitada alcance o supere el plazo de RF-010 sin haber sido reactivada, la tarea deberá eliminarla físicamente conservando su historial de usuario (`RF-010` de `usuario-personalizado`) y los registros de auditoría (`RF-012` de `auditoria-eventos-seguridad`), liberando el correo electrónico para posibles registros futuros. Si por una anomalía administrativa alguna cuenta vencida figurara aún como propietaria actual de una empresa, la tarea deberá omitir el borrado de esa cuenta, continuar purgando el resto de cuentas vencidas válidas, dejar constancia del error en los registros del servidor y registrar la ejecución con la alerta operativa correspondiente conforme a `tareas-purga-y-alertas`.

### RF-012 Reserva de correo e impedimento de registro mientras esté deshabilitada
Mientras una cuenta deshabilitada no haya sido eliminada físicamente por la purga de RF-011, el sistema deberá seguir impidiendo el registro de una nueva cuenta con el mismo correo sin distinguir mayúsculas (`RF-002` de `usuario-personalizado` y `RF-004` de `procesos-pendientes`) y sin enviar el aviso «ya tienes cuenta» (`RF-006` de `correo-asincrono-plantillas`).

### Pantalla, clientes, configuración y consola

### RF-013 Bloqueo por términos pendientes o cuenta inactiva
Mientras el usuario autenticado no tenga aceptada la versión vigente obligatoria de los términos (incluida la publicación de una nueva versión obligatoria, o si no existe ninguna vigente publicada), el sistema deberá rechazar en la API la petición de deshabilitación de cuenta y redirigir a `/terms` en `/profile`, conforme a `RF-011` de `inicio-cierre-sesion` y `RF-011` de `perfil-y-cambio-contrasena`. Mientras la cuenta esté inactiva, rechazará cualquier petición de sesión como no autenticada.

### RF-014 Interfaz de deshabilitación desde el menú de /profile (web y escritorio)
El sistema deberá habilitar la opción de deshabilitación en el menú de acciones de `/profile`, conforme a [identidad-visual.md](../../docs/identidad-visual.md) y en los idiomas español (`es`), portugués de Brasil (`pt-BR`) e inglés (`en`), abriendo una interfaz de confirmación en dos pasos dentro de `/profile` que:
1. Informe con claridad de las consecuencias de deshabilitar la cuenta (revocación inmediata de accesos y posibilidad de reactivación vía soporte durante 12 meses).
2. Si el usuario es propietario de al menos una empresa, muestre el aviso de bloqueo indicando que debe transferir o eliminar su empresa primero y mantenga inhabilitada la acción de baja (RF-003). Si es el último superusuario activo, informe del impedimento y mantenga inhabilitada la acción (RF-016).
3. Si puede iniciar la baja, solicite confirmación explícita introduciendo su contraseña actual (con control para mostrar u ocultar la contraseña), valide en local que el campo no esté vacío al salir o enviar, muestre errores debajo del campo o errores generales ante bloqueo temporal o fallo de servidor, y muestre la cuenta atrás del bloqueo vigente de RF-005 tanto al recibir el rechazo como al abrir o recargar `/profile`.
4. Tras confirmarse la deshabilitación, limpie de inmediato la sesión o credencial local del cliente (web y escritorio) y redirija a `/login` mostrando un mensaje claro de que la cuenta ha sido deshabilitada y puede reactivarse contactando a soporte en un plazo máximo de 12 meses.

### RF-015 Clientes web, escritorio y verificación desde consola
El sistema deberá admitir la operación de deshabilitación de cuenta desde el cliente web (sesión por cookie y protección CSRF) y desde el cliente de escritorio (credencial en cabecera, exento de CSRF), y permitir ejercitar y verificar desde consola (`P-03`) la creación de empresas preliminares de prueba, la deshabilitación de cuentas (incluyendo el rechazo si posee empresa), la reactivación dentro de los 12 meses, el rechazo tras vencer los 12 meses y la ejecución manual de la purga periódica.

### RF-016 Protección del último superusuario activo
Si el usuario autenticado es el único superusuario activo restante del sistema e intenta deshabilitar su propia cuenta, entonces el sistema deberá rechazar la operación (en la interfaz de `/profile` de forma preventiva y en la API y la operación de negocio antes de evaluar la contraseña actual) indicando que debe existir al menos otro superusuario activo, sin contabilizar intentos fallidos de contraseña ni cerrar ninguna sesión.

## Supuestos
- S-01 La deshabilitación de cuenta se abre desde la opción correspondiente ya prevista en el menú de acciones de `/profile`, sin crear una ruta separada para solicitar la baja (pregunta 1 y ajuste de UI sobre `/profile`).
- S-02 La reautenticación para deshabilitar la cuenta utiliza la contraseña actual introducida en la confirmación en dos pasos abierta desde dicho menú, protegida por un límite configurable e independiente por cuenta (5 intentos fallidos en 5 minutos con bloqueo de 5 minutos por defecto) que no cierra la sesión en curso y mantiene visible la cuenta atrás al recargar `/profile` (pregunta 2, C-04, C-07).
- S-03 El modelo preliminar de empresas solo cubre nombre y propietario actual en el backend, su administración en el panel interno y comandos/helpers de consola y pruebas; los flujos de usuario final para crear, transferir o eliminar empresas pertenecen a una feature posterior del Módulo II (pregunta 3, C-06).
- S-04 La comprobación de propiedad de empresa (y la protección del último superusuario activo) se evalúan de forma proactiva al abrir la confirmación en `/profile` y con prioridad sobre la contraseña actual en la API, para evitar que el usuario consuma intentos de contraseña cuando no puede deshabilitar la cuenta (pregunta 4, C-06).
- S-05 El plazo de 12 meses se calcula como 12 meses calendario desde la fecha y hora de deshabilitación en UTC (con 29 de febrero venciendo el 28 de febrero en años no bisiestos), y es configurable sin modificar el código para pruebas y operación (pregunta 5, C-03).
- S-06 El requisito RF-008 modifica la regla de neutralidad estricta de `RF-002` de `inicio-cierre-sesion` cuando la persona introduce tanto el correo como la contraseña correctos de una cuenta deshabilitada (sumando al contador de intentos fallidos y distinguiendo si sigue dentro de los 12 meses o si vencieron); se formalizará en `inicio-cierre-sesion` mediante `sdd-cambio` (pregunta 6, C-01).
- S-07 La tarea periódica de purga elimina físicamente la cuenta vencida tras 12 meses deshabilitada (liberando el correo y conservando historial y auditoría), en lugar de anonimizarla, ejecutándose en modo parcial si alguna cuenta vencida tuviera aún una empresa (pregunta 7, C-05).
- S-08 Al deshabilitar la cuenta, el cliente web o de escritorio redirige a `/login` con el aviso de confirmación y, al reactivarla soporte dentro del plazo de 12 meses, se conservan la contraseña y los consentimientos previos y la trazabilidad recae en el historial del usuario sin añadir nuevos tipos de correo ni de evento de auditoría (pregunta 8).
- S-09 Toda desactivación registrada a partir de esta feature (incluida la desactivación manual desde el panel de administración interno) fija la fecha de deshabilitación en UTC; si existiera algún registro heredado inactivo sin fecha de deshabilitación previa, no se purgará automáticamente hasta contar con dicha fecha (C-03).
- S-10 La integración de la purga de cuentas vencidas como cuarta tarea monitorizada en `tareas-purga-y-alertas` requerirá ampliar su registro de tareas monitorizadas (o coordinarlo con `sdd-cambio` si modifica requisitos previos de esa spec) (C-05).

## Fuera de alcance
- Pantallas o endpoints de usuario final para crear, editar, transferir o eliminar empresas (Módulo II).
- Autoreactivación de cuentas deshabilitadas sin intervención de soporte técnico.
- Solicitud de baja para cuentas cuyo acceso dependa únicamente de un proveedor externo sin contraseña local (no existen en el sistema actual).
- Nuevos tipos de evento de auditoría o nuevas plantillas de correo electrónico específicos para la reactivación o la purga de cuentas.
- Descarga o exportación de datos personales previa a la deshabilitación.

## Criterios de finalización
- CF-1 Existen tests automatizados en backend y frontend que cubren cada RF (`RF-001`…`RF-016`). `pytest` y `pnpm --filter frontend test` pasan en verde con cobertura ≥ 80 %, y `mypy`, `ruff`, `black`, `tsc`, ESLint y Prettier están limpios.
- CF-2 Tests de backend demuestran que una cuenta sin empresas (incluido `staff`/superusuario cuando existe otro superusuario activo) puede deshabilitarse con su contraseña actual, que las contraseñas incorrectas suman a su límite configurable independiente y bloquean temporalmente sin cerrar la sesión actual, que el último superusuario activo queda protegido, y que tras deshabilitarse todas las sesiones web, credenciales de escritorio y restablecimientos pendientes quedan revocados al instante y se registran el evento de auditoría y el aviso en la bandeja de salida.
- CF-3 Tests de backend y frontend demuestran que un usuario propietario de una empresa preliminar ve el aviso proactivo al abrir la deshabilitación desde el menú de `/profile` con la acción inhabilitada y recibe rechazo prioritario en la API (sin evaluar ni consumir intentos de contraseña) indicando que debe transferir o eliminar su empresa primero.
- CF-4 Tests de backend demuestran que el inicio de sesión con correo y contraseña correctos de una cuenta deshabilitada suma al límite de intentos y muestra el mensaje específico correspondiente (en plazo de 12 meses con soporte o plazo vencido), mientras que una contraseña incorrecta mantiene la respuesta neutra.
- CF-5 Tests de backend demuestran que toda desactivación fija la fecha UTC, que soporte técnico (y consola) puede reactivar una cuenta antes de los 12 meses conservando contraseña y consentimientos, que tras 12 meses la reactivación se rechaza y que la cuarta tarea periódica integrada en `tareas-purga-y-alertas` elimina físicamente cuentas vencidas válidas conservando su historial y auditoría (y omitiendo con alerta si alguna tuviera empresa, sin detener el resto del lote).
- CF-6 Todas las operaciones (empresa preliminar, deshabilitación, reactivación y purga) pueden ejecutarse y verificarse desde consola (`P-03`), y la UI en `/profile` y `/login` cumple [identidad-visual.md](../../docs/identidad-visual.md) en `es`, `pt-BR` y `en`.

## Historial de cambios
- 2026-11-27 — Creación inicial de la spec tras entrevista — RF: RF-001…RF-015 — Estado: pendiente de clarificar
- 2026-11-27 — Clarificación (C-01 a C-07): ajuste a login de cuentas deshabilitadas con impacto en `inicio-cierre-sesion`, bloqueo por términos vigentes, fecha obligatoria al desactivar en admin y 12 meses calendario configurables (29 feb → 28 feb), contador de fallos independiente, cuarta tarea en `tareas-purga-y-alertas` con purga parcial, modelo preliminar nombre+propietario con protección del último superusuario, y confirmación en dos pasos desde el menú de `/profile` con cuenta atrás persistente — RF: RF-001, RF-002, RF-005, RF-008…RF-011, RF-013, RF-014, RF-016 — Estado: clarificado
