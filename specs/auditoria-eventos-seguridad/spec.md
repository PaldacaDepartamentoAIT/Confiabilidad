# Spec: auditoria-eventos-seguridad
Estado: borrador
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
correo, resultado (éxito o fallo) y metadatos.

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
evento de tipo inicio de sesión con resultado fallo y el motivo del rechazo en los metadatos.
Esto ocurre también cuando el correo no corresponde a ninguna cuenta; en ese caso el evento no
tiene vínculo con una cuenta.

### RF-005 Bloqueo por límite de intentos
Cuando la librería de autenticación rechace un intento porque se ha superado el límite, el sistema
deberá registrar un evento de tipo bloqueo por cada intento rechazado.

### RF-006 Fuente única de intentos fallidos
El sistema no deberá contar intentos fallidos ni bloquear cuentas por su cuenta; la única fuente de
esas decisiones es la librería de autenticación.

### RF-007 Registro y solicitud pendiente
Cuando se cree una cuenta, o cuando se cree una solicitud de registro pendiente, el sistema deberá
registrar un evento del tipo correspondiente con su resultado.

### RF-008 Códigos
Cuando se envíe un código, o cuando se valide o se rechace uno, el sistema deberá registrar un
evento de envío o de validación con su resultado.

### RF-009 Cierre de sesión
Cuando una persona cierre sesión, el sistema deberá registrar un evento de cierre de sesión.

### RF-010 Contraseña y perfil
Cuando se cambie o restablezca una contraseña, cuando se edite un perfil o cuando se deshabilite
una cuenta, el sistema deberá registrar un evento del tipo correspondiente con su resultado.

### RF-011 Sin datos sensibles
El sistema nunca deberá guardar en un evento contraseñas, códigos, tokens ni el correo en claro.
La clave de sesión se guarda como huella calculada con HMAC, nunca en claro. El correo se guarda
como huella HMAC de su versión en minúsculas, sin espacios al principio ni al final.

### RF-012 Solo inserción desde la aplicación
El sistema no deberá permitir modificar ni borrar eventos desde el panel de administración, desde
el ORM ni desde ninguna vía de la aplicación. Si se intenta, entonces el sistema deberá rechazar la
operación.

### RF-013 Consulta para investigación
El sistema deberá mostrar los eventos a las personas con permiso de staff en el panel de
administración, en modo solo lectura, con filtros por fecha, tipo, IP y huella del correo.

### RF-014 Conservación
El sistema deberá conservar cada evento durante un año desde su marca de tiempo. Ningún evento de
menos de un año deberá borrarse, y los de más de un año deberán poder eliminarse con un único
comando.

### RF-015 IP real del cliente
Cuando una petición llegue a través de intermediarios, el sistema deberá registrar la IP del
cliente original y no la del intermediario.

### RF-016 Marca de tiempo indexada
El sistema deberá guardar la marca de tiempo de cada evento en UTC e indexarla.

## Supuestos
- S-01 La IP real se obtiene con la lógica de IP real que ya existe en el proyecto (`apps/core`).
  *Suposición:* no la he verificado en esta fase.
- S-02 La clave para las huellas HMAC vive en el almacén de secretos y se obtiene de la utilidad HMAC
  centralizada que está en curso. Esta feature no empieza su implementación hasta que esa utilidad
  esté mergeada.
- S-03 La purga de los eventos de más de un año la ejecuta una persona operadora; no es automática.
  *Suposición:* confirmar en la clarificación.

## Fuera de alcance
- Alertas, paneles de análisis o detección automática de ataques.
- Exportación a sistemas externos.
- Registro de consultas o lecturas de los propios eventos.
- Eventos de otros módulos que no estén en RF-002.
- Protección de la base de datos a nivel de rol (no se elige en esta feature).

## Criterios de finalización
- Un inicio de sesión exitoso y un inicio de sesión fallido generan dos filas, cada una con la IP
  real del cliente, con un test que lo demuestre.
- Cada tipo de evento de RF-002 tiene al menos un test que comprueba su registro.
- Ningún evento contiene contraseñas, códigos, tokens ni correos en claro; un test lo verifica con
  datos reales de cada flujo.
- Editar o borrar un evento desde el ORM y desde el panel de administración falla, con un test.
- El panel de administración muestra los eventos en solo lectura y con los filtros de RF-013.
- Un comando documentado purga los eventos de más de un año y no toca los recientes.
- Toda la verificación se puede repetir desde la consola (pruebas o comando de gestión), sin frontend.

## Historial de cambios
- 2026-10-13 — Creación de la spec a partir de la entrevista (modo ligero) — RF: RF-001 a RF-016 — Estado: pendiente de clarificar
