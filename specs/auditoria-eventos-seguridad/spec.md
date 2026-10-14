# Spec: auditoria-eventos-seguridad
Estado: aprobada
Aprobación: ligera

## Objetivo (por qué)
Cuando ocurre algo sensible en la cuenta de una persona (entrar, fallar al entrar, bloquearse,
cerrar sesión, cambiar la contraseña, editar su perfil o deshabilitarse), el sistema debe dejar
un registro que sirva para investigar un incidente después. Los registros se conservan un tiempo,
no contienen secretos y no se pueden alterar desde la aplicación.

La fuente de los intentos fallidos y de los bloqueos es la librería de autenticación (allauth). Esta
feature los registra, pero no los cuenta ni los bloquea por su cuenta.

Depende de las features `usuario-personalizado`, `auth-headless`, `cambio-contrasena` y
`procesos-pendientes`.

## Requisitos funcionales

### RF-001 Contenido de cada evento
Cuando ocurra un evento de la lista de RF-002, el sistema deberá guardar un registro con: tipo de
evento, marca de tiempo en UTC, clave de sesión, dirección IP del cliente, user agent, huella del
correo, resultado (éxito o fallo) y metadatos. La clave de sesión puede estar vacía cuando no exista
sesión. El evento no tiene referencia directa a la cuenta del usuario; la relación con la cuenta se
hace solo mediante la huella del correo.

### RF-002 Tipos de evento
El sistema deberá reconocer exactamente estos tipos de evento: registro de cuenta, solicitud de
registro pendiente, envío de código, validación de código, inicio de sesión, bloqueo por límite de
intentos, cierre de sesión, cambio de contraseña, restablecimiento de contraseña, edición de perfil
y deshabilitación de cuenta.

### RF-003 Inicio de sesión exitoso
Cuando un inicio de sesión sea exitoso, el sistema deberá registrar un evento de tipo inicio de
sesión con resultado éxito, y la clave de sesión de ese evento deberá ser la de la sesión ya
iniciada.

### RF-004 Inicio de sesión fallido
Cuando la librería de autenticación rechace un inicio de sesión, el sistema deberá registrar un
evento de tipo inicio de sesión con resultado fallo y uno de estos motivos en los metadatos:
credenciales incorrectas, límite de intentos alcanzado o cuenta inactiva. Esto ocurre también cuando
el correo no corresponde a ninguna cuenta; en ese caso el evento no tiene vínculo con una cuenta.
Esto ocurre también cuando la cuenta está inactiva aunque las credenciales sean válidas. Este
requisito cubre los rechazos que la aplicación puede producir con su configuración actual; si se
activan nuevas comprobaciones, la spec deberá ampliarse.

### RF-005 Bloqueo por límite de intentos
Cuando la librería de autenticación rechace un intento porque se ha superado el límite, el sistema
deberá registrar, por ese mismo intento, un evento de fallo de inicio de sesión (RF-004) y un evento
de tipo bloqueo.

### RF-006 Fuente única de intentos fallidos
El sistema no deberá contar intentos fallidos ni bloquear cuentas por su cuenta; la única fuente de
esas decisiones es la librería de autenticación.

### RF-007 Registro y solicitud pendiente
Cuando se cree una cuenta, o cuando se cree una solicitud de registro pendiente, el sistema deberá
registrar un evento del tipo correspondiente con su resultado.

### RF-008 Códigos
Cuando se envíe un código, el sistema deberá registrar un evento de envío con su resultado. Cuando
se valide un código, el sistema deberá registrar un evento de validación con resultado éxito. Cuando
un código sea rechazado, el sistema deberá registrar un evento de validación con resultado fallo. Un
código es rechazado cuando es incorrecto, cuando ha caducado él o su proceso, cuando se ha alcanzado el
límite de intentos o cuando ya se había validado. Si el proceso no existe, o si se rechaza por un cambio
en la cuenta (cuenta inactiva, o correo o contraseña cambiados), entonces el sistema no deberá registrar
ningún evento de validación.

### RF-009 Cierre de sesión
Cuando una persona cierre sesión, el sistema deberá registrar un evento de cierre de sesión.

### RF-010 Contraseña y perfil
Cuando se cambie o restablezca una contraseña, cuando se edite un perfil o cuando se deshabilite
una cuenta, el sistema deberá registrar un evento del tipo correspondiente con su resultado. Si un cambio o un restablecimiento de contraseña se rechaza por una contraseña no válida, entonces el sistema no deberá registrar ningún evento de fallo.

### RF-011 Sin datos sensibles
El sistema nunca deberá guardar en un evento contraseñas, códigos, tokens ni el correo en claro.
La clave de sesión se guarda como huella calculada con HMAC, nunca en claro. El correo se guarda
como huella HMAC de su versión en minúsculas, sin espacios al principio ni al final. Los metadatos
son una lista abierta de datos no sensibles.

### RF-012 Solo inserción desde la aplicación
El sistema no deberá permitir modificar ni borrar eventos desde el panel de administración, desde
el ORM ni desde ninguna otra vía de la aplicación, salvo el comando de purga de RF-014, que es la
única vía autorizada de borrado. Si se intenta modificar un evento, o borrarlo fuera de esa vía,
entonces el sistema deberá rechazar la operación. Las vías de la aplicación son el ORM, el panel de
administración y los comandos de gestión. El SQL directo contra la base de datos no es una vía de la
aplicación: queda como riesgo residual aceptado, igual que la protección a nivel de rol, que está fuera de
alcance.

### RF-013 Consulta para investigación
El sistema deberá mostrar los eventos a las personas con el permiso específico de visualización de
eventos de seguridad en el panel de administración, en modo solo lectura, con filtros laterales por
tipo, resultado y rango de fechas, y búsqueda por dirección IP y búsqueda exacta por huella del correo.

### RF-014 Conservación
El sistema deberá conservar cada evento durante un año desde su marca de tiempo. Ningún evento de
menos de un año deberá borrarse, y los de más de un año deberán poder eliminarse únicamente mediante
ese comando.

### RF-015 IP real del cliente
Solo las conexiones desde las direcciones de la lista de proxies de confianza, configurada en el
entorno de despliegue, son intermediarios de confianza. La lista contiene direcciones IP exactas. Si la
lista está vacía o no está configurada, la aplicación arranca y no confía en ningún proxy. Cuando una petición llegue a través de él, el sistema deberá registrar la IP del cliente
original. Para cualquier otra conexión, el sistema deberá registrar la IP de la conexión directa,
ignorando las cabeceras de intermediarios.

### RF-016 Marca de tiempo indexada
El sistema deberá guardar la marca de tiempo de cada evento en UTC e indexarla.

## Supuestos
- S-01 La IP real se obtiene con la lógica de IP real que ya existe en el proyecto (`apps/core`).
  *Suposición:* no la he verificado en esta fase.
- S-02 La clave para las huellas HMAC vive en el almacén de secretos y se obtiene de la utilidad HMAC
  centralizada que está en curso. Esta feature no empieza su implementación hasta que esa utilidad
  esté mergeada.
- S-03 La purga de los eventos de más de un año la ejecuta una persona operadora; no es automática.
  *Suposición:* no confirmada explícitamente en la clarificación.

## Fuera de alcance
- Alertas, paneles de análisis o detección automática de ataques.
- Exportación a sistemas externos.
- Registro de consultas o lecturas de los propios eventos.
- Eventos de otros módulos que no estén en RF-002.
- Protección de la base de datos a nivel de rol (no se elige en esta feature).

## Criterios de finalización
- Un inicio de sesión exitoso y un inicio de sesión fallido generan dos filas, cada una con la IP
  real del cliente, con un test que lo demuestre.
- Un intento rechazado por límite genera exactamente dos filas: un fallo de inicio de sesión y un
  bloqueo.
- Un código rechazado genera un evento de validación con resultado fallo.
- Cada tipo de evento de RF-002 tiene al menos un test que comprueba su registro.
- Ningún evento contiene contraseñas, códigos, tokens ni correos en claro; un test lo verifica con
  datos reales de cada flujo.
- Una petición con cabecera de intermediario falsa, llegada sin pasar por el proxy de confianza,
  registra la IP de la conexión directa.
- Editar o borrar un evento desde el ORM y desde el panel de administración falla, con un test; el
  comando de purga es la única vía que borra, con un test.
- El panel de administración muestra los eventos en solo lectura, solo al usuario con el permiso de
  RF-013, y con los filtros de RF-013.
- Un comando documentado purga los eventos de más de un año y no toca los recientes.
- Toda la verificación se puede repetir desde la consola (pruebas o comando de gestión), sin frontend.

## Historial de cambios
- 2026-10-13 — Creación de la spec a partir de la entrevista (modo ligero) — RF: RF-001 a RF-016 — Estado: pendiente de clarificar
- 2026-10-13 — Clarificación con H-01 a H-08 (borrado solo por purga, dos filas por bloqueo, proxy de confianza fijo, clave de sesión opcional, metadatos abiertos, rechazo de código como validación fallida, permiso específico de consulta, sin vínculo directo a la cuenta) — RF: RF-001, RF-005, RF-008, RF-011 a RF-015 — Estado: clarificado
- 2026-10-13 — Cambio de RF-013 (filtros laterales por tipo, resultado y fecha; búsqueda por IP y huella del correo) y de RF-015 (lista de proxies en el entorno de despliegue) tras la validación — RF: RF-013, RF-015 — Estado: impacto analizado
- 2026-10-13 — Cambio de RF-004: se registran también los rechazos posteriores a credenciales válidas (cuenta inactiva; el correo sin verificar no aplica porque la verificación de correo está desactivada — corregido el 2026-10-14) — RF: RF-004 — Estado: impacto analizado
- 2026-10-14 — Aclaración de RF-010: un cambio o restablecimiento de contraseña rechazado por contraseña no válida no deja evento de fallo (opción B aprobada) — RF: RF-010 — Estado: impacto analizado
- 2026-10-14 — Aclaración de RF-008 (qué es un código rechazado) y de RF-012 (vías de la aplicación; el SQL directo queda como riesgo residual), y corrección de la entrada de RF-004 del 2026-10-13, tras la validación — RF: RF-004, RF-008, RF-012 — Estado: impacto analizado
