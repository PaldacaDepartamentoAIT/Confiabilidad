# Spec: inicio-cierre-sesion
Estado: aprobada
Aprobación: ligera
Validación: ligera

## Objetivo (por qué)
La autenticación base para web y escritorio ya existe como prueba (`auth-headless`), junto con el
modelo de cuenta (`usuario-personalizado`), los términos legales (`consentimientos`), la auditoría
(`auditoria-eventos-seguridad`) y el flujo de registro (`registro-flujo`), pero ninguna persona
puede aún iniciar ni cerrar sesión desde la aplicación, ni están activos los límites contra fuerza
bruta ni el inventario de sesiones abiertas (`UserSession` del [diagrama ER](../procesos-pendientes/diagramas/er.png)).
Esta feature completa el acceso y la salida en ambos clientes y en el servidor: permite entrar con
correo y contraseña solo a cuentas activas distinguiendo el aviso específico cuando una cuenta está
deshabilitada y coinciden correo y contraseña (RF-008 de `deshabilitar-cuenta`), exige
aceptar los términos vigentes pendientes antes de pasar al área privada, registra las sesiones
abiertas permitiendo cerrar la actual, otra concreta o todas las demás, e invalida de forma efectiva
la sesión tanto en el cliente como en el servidor.

## Secuencia
1. La persona abre la pantalla de inicio de sesión (`/login`) e introduce su correo y su contraseña
   (RF-013, pantalla de inicio de sesión y enlaces con el registro; RF-014, validación en el cliente
   y mensajes de error al iniciar sesión).
2. Si las credenciales corresponden a una cuenta activa y no se ha superado ningún límite, el
   servidor abre la sesión, la registra en el inventario de sesiones activas y responde al cliente
   (RF-001, acceso con correo y contraseña; RF-007, registro de sesiones activas). Si el correo no
   existe o la contraseña no coincide, responde con el mismo mensaje neutro y suma al contador de
   intentos fallidos; si correo y contraseña coinciden con una cuenta deshabilitada, suma igualmente
   al contador e informa del estado según el plazo de 12 meses (RF-002, rechazo de credenciales
   inválidas o cuenta deshabilitada; RF-004, bloqueo temporal por intentos fallidos).
3. Si la cuenta no tiene aceptada la versión vigente obligatoria de los términos (o no hay ninguna
   vigente), se muestra la pantalla de términos pendientes (`/terms`), donde solo puede aceptarlos o
   cerrar sesión (RF-011, bloqueo del área privada mientras falten los términos vigentes; RF-012,
   aceptación de los términos vigentes con sesión iniciada; RF-015, pantalla de aceptación de
   términos pendientes).
4. Con los términos vigentes aceptados, la persona accede al área privada (`/`), donde puede ver sus
   sesiones activas, cerrar cualquiera de las otras o todas las demás, o cerrar su sesión actual
   (RF-006, cierre de la sesión actual; RF-008, consulta de sesiones activas; RF-009, cierre de otra
   sesión o de todas las demás; RF-016, área privada y gestión de sesiones en pantalla).

En este documento, las menciones a `RF-0xx` o `S-0x` de otras features remiten a sus respectivas
specs (`auth-headless`, `usuario-personalizado`, `consentimientos`, `auditoria-eventos-seguridad`,
`cambio-contrasena`, `registro-api`, `registro-flujo` y `componentes-base-accesibles`).

## Requisitos funcionales

### Inicio de sesión y estado de la cuenta

### RF-001 Acceso con correo y contraseña
Cuando una persona envíe su correo y su contraseña desde el cliente web o el de escritorio sin una
sesión activa ya iniciada en esa petición y las credenciales correspondan a una cuenta activa, el
sistema deberá autenticarla sin distinguir mayúsculas ni espacios al principio o al final en el
correo (RF-001 de `usuario-personalizado`, correo normalizado), establecer la sesión para ese
cliente (RF-002 de `auth-headless`, inicio de sesión del cliente web por cookie, y RF-003 de
`auth-headless`, inicio de sesión del cliente de aplicación por token), actualizar la fecha de su
último inicio de sesión (RF-008 de `usuario-personalizado`, atributos de administración y alta) y
registrar el evento de inicio de sesión exitoso (RF-003 de `auditoria-eventos-seguridad`, inicio de
sesión exitoso). Si la petición de inicio de sesión ya incluye una sesión activa válida, entonces el
sistema deberá rechazarla indicando que ya existe una sesión iniciada, sin alterar la sesión en
curso ni crear otra fila en `UserSession` (RF-007, registro de sesiones activas).

### RF-002 Rechazo neutro de credenciales inválidas o aviso en cuenta deshabilitada
Si el correo no pertenece a ninguna cuenta o la contraseña no coincide (incluida una cuenta
inactiva con contraseña incorrecta), entonces el sistema deberá rechazar el inicio de sesión sin
establecer sesión ni emitir credencial de sesión, sumar el intento al contador de intentos fallidos
(RF-004, bloqueo temporal por intentos fallidos) y devolver el mismo código de estado, la misma
estructura y el mismo mensaje neutro de credenciales incorrectas en los tres casos. Si el correo y la
contraseña coinciden con una cuenta inactiva y no se ha alcanzado el bloqueo de RF-004, el sistema
deberá rechazar igualmente el acceso sin abrir sesión, sumar al contador de intentos fallidos,
registrar en auditoría el motivo `inactive_account` (RF-004 de `auditoria-eventos-seguridad`) y
devolver el aviso específico de cuenta deshabilitada indicando la reactivación vía soporte dentro de
12 meses o que el plazo ya venció (`RF-008` de `deshabilitar-cuenta`).

### RF-003 Invalidación inmediata al desactivar o borrar una cuenta
Mientras una cuenta esté inactiva (RF-007 de `usuario-personalizado`), el sistema deberá rechazar
como no autenticada cualquier petición que presente una sesión o credencial de esa cuenta, tanto en
la web como en el escritorio. Cuando una cuenta pase a estar inactiva o se borre físicamente, el
sistema deberá invalidar en el servidor todas sus sesiones abiertas y borrar sus filas del registro
de sesiones activas (RF-007).

### Límites contra fuerza bruta

### RF-004 Bloqueo temporal por intentos fallidos
Si se alcanza el número máximo configurado de intentos fallidos de inicio de sesión para un mismo
correo o desde una misma dirección IP dentro de la ventana configurada (5 intentos en 5 minutos por
defecto; RF-020, valores configurables), incluidos los intentos sobre cuentas inactivas con
contraseña correcta o incorrecta (RF-002), entonces el sistema deberá rechazar los intentos
siguientes durante ese periodo sin evaluar la contraseña, informar de que se ha superado el límite
de intentos y registrar el fallo y el bloqueo con el motivo `too_many_login_attempts` según RF-004 y
RF-005 (bloqueo por límite de intentos) de `auditoria-eventos-seguridad`.

### RF-005 Límite de frecuencia por IP en el inicio de sesión
Si una dirección IP (la IP real del cliente; RF-010 de `auth-headless`, IP real del cliente tras el
proxy) supera el número máximo configurado de solicitudes de inicio de sesión en un minuto (30 por
defecto, RF-020), sean válidas o no, entonces el sistema deberá rechazar las siguientes sin
evaluarlas, con una respuesta de límite superado que indique cuántos segundos esperar y sin generar
evento de auditoría (RF-004 de `auditoria-eventos-seguridad`).

### Cierre de sesión e inventario de sesiones activas

### RF-006 Cierre de la sesión actual
Cuando una persona autenticada solicite cerrar su sesión actual desde el cliente web o el de
escritorio, el sistema deberá invalidar esa sesión en el servidor para que ni la sesión web ni la
credencial de escritorio puedan volver a autenticar, borrar su fila del registro de sesiones activas
(RF-007), registrar el evento de cierre de sesión (RF-009 de `auditoria-eventos-seguridad`, cierre
de sesión) y eliminar la sesión o credencial almacenada en el cliente. Si la petición de cierre
llega al servidor sin una sesión válida (porque ya no existe, fue cerrada o caducó), entonces el
servidor deberá responder como no autenticado sin registrar ningún evento de cierre de sesión, y el
cliente deberá eliminar igualmente su sesión o credencial local y llevar a `/login`. Si la
comunicación con el servidor falla al cerrar sesión, entonces el cliente deberá eliminar igualmente
su sesión o credencial local y llevar a `/login`.

### RF-007 Registro de sesiones activas
Cuando se inicie una sesión en cualquiera de los dos clientes, el sistema deberá crear una fila en
el registro de sesiones activas (`UserSession`) asociada a la cuenta con una huella de la clave de
sesión calculada con un secreto del servidor (nunca la clave ni el token en claro), la dirección IP
real del cliente (RF-010 de `auth-headless`), el agente de usuario completo sin recortar (o el texto
por defecto `"unknown"` si la cabecera `User-Agent` falta o está en blanco), la fecha de inicio y la
fecha de última actividad. Cuando esa sesión realice peticiones autenticadas posteriores y haya
transcurrido al menos el intervalo configurado desde su última actualización (RF-020), el sistema
deberá actualizar su fecha de última actividad, su dirección IP y su agente de usuario (con la misma
regla de valor por defecto si falta). Una sesión se considera caducada cuando ha transcurrido la
duración de sesión configurada (14 días por defecto, RF-020) desde su última actividad o cuando ya
no existe en el almacén de sesiones del servidor. Cuando una sesión se cierre, se invalide o
caduque, el sistema deberá borrar su fila (RF-008, RF-021).

### RF-008 Consulta de sesiones activas
El sistema deberá permitir a la persona autenticada que tenga los términos vigentes aceptados
(RF-011) consultar la lista de sus sesiones activas vigentes. En cada consulta, el sistema deberá
descartar y borrar de `UserSession` las filas de esa cuenta que hayan caducado o cuya sesión ya no
exista en el almacén de sesiones (RF-007), y devolver las vigentes ordenadas de la actividad más
reciente a la más antigua con su identificador, la dirección IP, el agente de usuario, la fecha de
inicio, la fecha de última actividad y una marca que indique si es la sesión actual, sin exponer
nunca la clave de sesión ni su huella.

### RF-009 Cierre de otra sesión o de todas las demás
Cuando una persona autenticada con los términos vigentes aceptados (RF-011) solicite cerrar otra de
sus sesiones activas indicando su identificador, o solicite cerrar todas las demás sesiones
distintas de la actual, el sistema deberá invalidar en el servidor las sesiones afectadas para que
dejen de autenticar de inmediato en web y escritorio, borrar sus filas del registro de sesiones
activas (RF-007), registrar un evento de cierre de sesión por cada sesión efectivamente cerrada
(RF-009 de `auditoria-eventos-seguridad`) y mantener activa la sesión desde la que se hizo la
solicitud. Si se solicita cerrar todas las demás sesiones y no existe ninguna otra sesión activa
aparte de la actual, entonces el sistema deberá responder con éxito sin cerrar ninguna sesión ni
registrar eventos de cierre de sesión. Si se solicita cerrar por identificador la propia sesión
actual, una sesión inexistente o una sesión de otra cuenta, entonces el sistema deberá rechazar la
operación sin cerrar ninguna sesión.

### RF-010 Invalidación de sesiones al cambiar o restablecer la contraseña
Cuando cambie la contraseña de una cuenta por cualquier vía (al completarse un restablecimiento de
RF-009 de `cambio-contrasena`, completar el cambio de contraseña; desde el panel de administración;
o al guardarse el modelo de usuario con una contraseña distinta), el sistema deberá invalidar en el
servidor todas sus sesiones abiertas y borrar todas sus filas del registro de sesiones activas
(RF-007).

### Términos vigentes pendientes al iniciar sesión

### RF-011 Bloqueo del área privada mientras falten los términos vigentes
Mientras una persona tenga una sesión iniciada pero no tenga aceptados los términos vigentes
(RF-015 de `consentimientos`, estado de consentimiento de un usuario), o no exista ninguna versión
de términos vigente publicada (RF-003 de `consentimientos`, versión vigente), el sistema deberá
comprobar esa condición en cada petición al área privada y rechazar el acceso a la consulta y cierre
de otras sesiones (RF-008, RF-009) y a cualquier otra operación o pantalla del área privada,
también si la nueva versión obligatoria de términos entró en vigor cuando la sesión ya estaba
abierta, permitiendo únicamente consultar el estado de su sesión y de los términos vigentes, aceptar
la versión vigente de términos (RF-012) o cerrar su sesión actual (RF-006).

### RF-012 Aceptación de los términos vigentes con sesión iniciada
Cuando una persona con sesión iniciada y términos pendientes envíe la aceptación del documento de
términos vigente, indicando su versión, su idioma y la marca de aceptación con las mismas reglas de
validación que RF-004 de `registro-api` (términos obligatorios), el sistema deberá registrar la
aceptación para su cuenta (RF-006 de `consentimientos`, aceptar términos) y permitirle el paso
inmediato al área privada sin volver a pedir sus credenciales.

### Pantallas y navegación en los clientes

### RF-013 Pantalla de inicio de sesión y enlaces con el registro
El sistema deberá ofrecer en la ruta `/login` una pantalla de inicio de sesión con los campos de
correo y contraseña, la acción para iniciar sesión y un enlace a la pantalla de registro
(`/register`). Asimismo, la pantalla del formulario de registro (RF-001 de `registro-flujo`,
formulario de registro) y la pantalla de cuenta creada (RF-015 de `registro-flujo`, cuenta creada)
deberán incluir un enlace a `/login`. La página de muestra de componentes (RF-020 de
`componentes-base-accesibles`, página de muestra) pasará a servirse en la ruta `/showcase`.

### RF-014 Validación en el cliente y mensajes de error al iniciar sesión
Cuando la persona salga de un campo o envíe el formulario de inicio de sesión, el sistema deberá
comprobar en el cliente que el correo y la contraseña no están vacíos y que el correo tiene forma de
dirección. Si alguna comprobación falla al enviar, entonces el sistema no deberá enviar la petición
al servidor, mostrará cada error debajo de su campo y llevará el foco al primer campo con error. Si
el servidor rechaza el inicio de sesión por credenciales inválidas o cuenta inactiva (RF-002), por
bloqueo o límite superado (RF-004, RF-005) o por un error de red o del servidor, entonces el sistema
deberá mostrar un mensaje general con el motivo devuelto, conservar el correo escrito y, cuando el
rechazo sea por credenciales, vaciar el campo de contraseña. Si la respuesta indica un tiempo de
espera por límite superado (RF-005), la pantalla deberá mostrar la cuenta atrás y desactivar el
envío hasta que llegue a cero.

### RF-015 Pantalla de aceptación de términos pendientes
Mientras la persona tenga una sesión iniciada con los términos vigentes pendientes (RF-011), el
sistema deberá mostrar en la ruta `/terms` una pantalla con acceso al texto de la versión vigente de
los términos en el idioma de la interfaz, la casilla obligatoria de aceptación, la acción para
confirmar la aceptación (RF-012) y la acción para cerrar la sesión actual (RF-006). Si no existe
ninguna versión de términos vigente publicada, entonces la pantalla deberá informar de que no es
posible continuar en este momento, ocultar el formulario de aceptación y ofrecer la acción para
cerrar la sesión actual.

### RF-016 Área privada y gestión de sesiones en pantalla
El sistema deberá ofrecer en la ruta `/`, para la persona autenticada con los términos vigentes
aceptados, una pantalla privada que muestre su nombre y su correo, la acción para cerrar la sesión
actual (RF-006) y la lista de sus sesiones activas (RF-008), señalando cuál es la sesión actual, con
una acción en cada una de las demás para cerrarla individualmente y una acción para cerrar todas las
demás sesiones a la vez (RF-009). Cuando no exista ninguna otra sesión activa aparte de la actual,
la acción para cerrar todas las demás sesiones deberá mostrarse desactivada u ocultarse.

### RF-017 Redirecciones según el estado de la sesión
Cuando se abra `/` o `/terms` sin una sesión válida, el sistema deberá redirigir a `/login`. Cuando
se abra `/login` o `/register` teniendo una sesión válida, el sistema deberá redirigir a `/` si la
cuenta tiene los términos vigentes aceptados, o a `/terms` (RF-015) en caso contrario. Cuando se
abra `/` teniendo sesión válida pero términos pendientes, o cuando una petición desde `/` reciba un
rechazo del servidor por términos pendientes (RF-011), el sistema deberá redirigir a `/terms`; y
cuando se abra `/terms` teniéndolos ya aceptados, deberá redirigir a `/`.

### Clientes, idioma y configuración

### RF-018 Clientes web y de escritorio
El sistema deberá admitir todas las operaciones de esta feature desde el cliente web, mediante
sesión por cookie y exigiendo protección CSRF en las peticiones que cambian estado (RF-002 y RF-006
de `auth-headless`, protección CSRF del cliente web), y desde el cliente de escritorio, mediante
credencial de sesión en cabecera y exento de CSRF (RF-003 y RF-006 de `auth-headless`).

### RF-019 Idioma de pantallas y mensajes
El sistema deberá mostrar todas las pantallas y devolver los mensajes del servidor de esta feature
en español (`es`), portugués de Brasil (`pt-BR`) e inglés (`en`), determinando el idioma con las
mismas reglas de RF-013 de `registro-api` (idioma de los mensajes).

### RF-020 Valores configurables
El sistema deberá permitir ajustar por configuración, sin cambiar el código, el número máximo de
intentos fallidos de inicio de sesión y la duración de su bloqueo (5 intentos y 5 minutos por
defecto, RF-004), el límite de solicitudes de inicio de sesión por IP (30 por minuto por defecto,
RF-005), el intervalo mínimo entre actualizaciones de la última actividad de una sesión (60
segundos por defecto, RF-007) y la duración de vida de una sesión tras su última actividad (14 días
por defecto, RF-007).

### RF-021 Limpieza de sesiones caducadas
El sistema deberá permitir borrar desde consola todas las filas de `UserSession` correspondientes a
sesiones caducadas o que ya no existan en el almacén de sesiones (RF-007), informando de cuántas
borró, y deberá ejecutar esa misma limpieza de forma automática y periódica sin intervención manual.

## Supuestos
- S-01 Alcance completo de extremo a extremo (pregunta 1): incluye las reglas del servidor y las
  pantallas en los clientes web y de escritorio.
- S-02 El inventario de sesiones abiertas (`UserSession` del diagrama ER) y la posibilidad de ver y
  cerrar otra sesión o todas las demás entran en esta feature (pregunta 2). Al cerrarse, invalidarse
  o caducar una sesión, su fila se borra de `UserSession` (pregunta 4): se limpian las vencidas al
  consultar las sesiones de la cuenta, con una orden de consola y mediante una tarea periódica
  (C-01, RF-008, RF-021). La trazabilidad histórica de los inicios y cierres de sesión ya la
  conserva `SecurityEvent` (`auditoria-eventos-seguridad`).
- S-03 La neutralidad estricta aplica frente a correos inexistentes o contraseñas incorrectas
  (también cuando la cuenta está inactiva pero la contraseña falla). Cuando tanto el correo como la
  contraseña coinciden con una cuenta deshabilitada (`S-06` y `RF-008` de `deshabilitar-cuenta`), el
  sistema sigue sumando al contador de intentos fallidos (RF-004) y registrando `inactive_account`
  antes del bloqueo (`too_many_login_attempts` al superarlo), pero informa al titular si puede
  reactivarla con soporte dentro de los 12 meses o si ese plazo ya venció.
- S-04 Si una cuenta se desactiva o se borra mientras tiene sesiones abiertas, todas sus sesiones se
  invalidan en el servidor y dejan de autenticar de inmediato (pregunta 3).
- S-05 Se reactivan los límites contra fuerza bruta en el inicio de sesión que S-09 de
  `auth-headless` (desactivación provisional del bloqueo por intentos fallidos) dejó pendientes,
  junto con el límite por IP de la vista de inicio de sesión previsto en RF-004 de
  `auditoria-eventos-seguridad` (pregunta 5).
- S-06 El inicio de sesión comprueba si la cuenta tiene aceptada la versión vigente obligatoria de
  los términos (RF-015 de `consentimientos`, S-08 de `consentimientos` —cuándo exigir nueva
  aceptación— y S-12 de `registro-api` —cuenta creada sin términos vigentes tras cambio de versión—)
  y, si falta, bloquea el paso al área privada hasta que la acepte (pregunta 6). Si no hay ninguna
  versión de términos vigente publicada, falla cerrado (pregunta 7), igual que S-10 de
  `registro-api` (fallo cerrado sin términos vigentes): solo permite cerrar la sesión hasta que se
  publique una versión vigente.
- S-07 Al pulsar cerrar sesión, el cliente borra siempre su sesión o credencial local y lleva al
  inicio de sesión aunque la sesión ya hubiera caducado en el servidor o falle la red (pregunta 8).
  *Por qué:* en un equipo compartido, un fallo de red no debe impedir a la persona retirar sus
  credenciales locales del dispositivo. *Riesgo aceptado:* si el cierre se hace sin conexión a red,
  la sesión en el servidor seguirá existiendo hasta que caduque o la persona la cierre desde otro
  dispositivo con conexión.
- S-08 Se completa el enlace al inicio de sesión desde la pantalla de cuenta creada que S-07 de
  `registro-flujo` (pantalla de éxito sin sesión) dejó pendiente para cuando existiera esta pantalla
  (pregunta 8).
- S-09 En `UserSession`, `session_key` guarda una huella HMAC de la clave de sesión y no el valor en
  claro, siguiendo el mismo principio que RF-011 de `auditoria-eventos-seguridad` (sin datos
  sensibles), para que una lectura de la tabla no permita suplantar sesiones activas, junto con lo
  necesario para revocar la sesión en el almacén de sesiones sin exponer nunca el secreto al cliente
  (RF-008); el plan técnico decidirá el mecanismo exacto.
- S-10 Las pantallas siguen [identidad-visual.md](../../docs/identidad-visual.md) y reutilizan los
  componentes de `componentes-base-accesibles`. La ruta `/` pasa a ser el área privada y la página
  de muestra se mueve a `/showcase`, como preveía S-06 de `componentes-base-accesibles` (página de
  muestra como inicio provisional) sin requerir cambios en esa spec (C-07).
- S-11 La invalidación y borrado de sesiones de RF-010 se activa en esta feature ante cualquier
  cambio de contraseña de la cuenta (restablecimiento por consola de `cambio-contrasena`, panel de
  administración o guardado del modelo), sin esperar a las futuras pantallas de contraseña (C-03).
- S-12 Si una petición de inicio de sesión llega con una sesión ya activa, el servidor la rechaza
  sin tocar la sesión existente (C-04); si una petición de cierre llega sin sesión válida, responde
  como no autenticado sin registrar evento de auditoría (C-05).
- S-13 Cuando la cabecera `User-Agent` falta o está vacía, `UserSession` guarda `"unknown"`, y
  cuando viene informada conserva su longitud completa sin recortar (C-08).

## Fuera de alcance
- Pantallas y API del restablecimiento de contraseña (el servicio de consola ya existe en
  `cambio-contrasena`, pero su exposición a los clientes es otra feature).
- Cambio de contraseña iniciado por el usuario dentro del área privada y edición de datos del
  perfil.
- Deshabilitación de la cuenta por su propio titular (S-04 de `usuario-personalizado`, acción de
  desactivar la cuenta por su titular).
- Gestión del consentimiento de marketing dentro del área privada (conceder o revocar tras el alta).
- Proveedores de acceso social o de terceros (S-04 de `auth-headless`, solo cuenta local).
- Segundo factor de autenticación (2FA / MFA) y CAPTCHA.
- Conservación de un historial de sesiones cerradas en `UserSession` (pregunta 4).

## Criterios de finalización
- CF-1 Hay tests para cada RF en backend y frontend. `pytest` y `pnpm --filter frontend test` están
  en verde con cobertura ≥ 80 %, y `mypy`, `ruff`, `black`, `tsc`, ESLint y Prettier están limpios.
- CF-2 Un test demuestra que iniciar sesión con un correo sin cuenta, con contraseña incorrecta y
  con una cuenta inactiva con contraseña incorrecta devuelve al cliente la misma respuesta neutra,
  mientras que una cuenta deshabilitada con contraseña correcta suma al mismo límite de intentos,
  registra `inactive_account` antes del bloqueo y devuelve el mensaje específico según siga dentro o
  fuera del plazo de 12 meses (RF-002, RF-004).
- CF-3 Un test demuestra que al cerrar la sesión actual (en web por cookie y en escritorio por
  token), y también al desactivar una cuenta con sesiones abiertas, la cookie y el token dejan de
  autenticar de inmediato en el servidor y desaparece su fila de `UserSession` (RF-003, RF-006,
  RF-007).
- CF-4 Un test demuestra que una cuenta con varias sesiones abiertas puede listarlas viendo cuál es
  la actual, cerrar otra sesión concreta o cerrar todas las demás sin perder la suya, y que las
  sesiones cerradas dejan de autenticar al instante en el servidor (RF-008, RF-009).
- CF-5 Un test demuestra que una cuenta autenticada sin los términos vigentes aceptados (al iniciar
  sesión o cuando entra en vigor una nueva versión obligatoria con la sesión ya abierta, o cuando no
  hay términos vigentes publicados) no puede listar ni cerrar otras sesiones y solo puede consultar
  su estado, aceptar los términos vigentes o cerrar su sesión actual; y que tras aceptarlos accede
  al área privada en la misma sesión (RF-011, RF-012, RF-015, RF-017).
- CF-6 Un test demuestra que superar los intentos fallidos de inicio de sesión y superar el límite
  de peticiones por IP rechazan los intentos siguientes según RF-004 y RF-005.
- CF-7 Tests del frontend demuestran la validación del formulario de inicio de sesión, el vaciado de
  la contraseña tras un fallo de credenciales, el paso por la pantalla de términos pendientes, el
  cierre de la sesión actual (incluso si falla la red o ya caducó), el cierre de otras sesiones, las
  redirecciones entre rutas públicas y privadas (`/`, `/login`, `/terms`, `/register`, `/showcase`)
  y el enlace desde la pantalla de cuenta creada (RF-006, RF-013…RF-017).
- CF-8 `resumen.md` explica cómo probar el inicio y cierre de sesión, la cuenta inactiva, los
  términos pendientes, la gestión de sesiones y la orden de limpieza tanto en la aplicación como
  desde consola con `curl` y `manage.py`.

## Historial de cambios
- 2026-11-18 — Creación (feature nueva) — RF: RF-001…RF-020 — Estado: pendiente de clarificar
- 2026-11-18 — Clarificación (C-01…C-08) — RF: RF-001, RF-002, RF-004, RF-006…RF-011, RF-013,
  RF-015…RF-017 y RF-020 ajustados; RF-021 añadido; S-02, S-03 y S-10 ajustados; S-11…S-13 añadidos;
  CF-2, CF-5, CF-7 y CF-8 ajustados — Estado: clarificado
- 2026-11-18 — Aprobación por el usuario — Estado: aprobada
- 2026-11-24 — Validación: cerrada con riesgo residual aceptado — Riesgos: (1) `apps/emails/tests/test_rendering.py::test_template_syntax_is_checked_quickly[closed-blocks]` superó el umbral de 1 s de CPU (`1.408 s`) bajo `--cov=.` y carga paralela de Vitest (fuera de `inicio-cierre-sesion`); (2) `pnpm --filter frontend test:visual` no se ejecutó en `confiabilidad-dev-frontend-1` por ausencia de Chromium en ese contenedor.
- 2026-11-27 — Clarificación del cambio (`S-06`, sin hallazgos; `Validación: ligera`) y aprobación de la spec — RF: RF-002 — Estado: clarificado
