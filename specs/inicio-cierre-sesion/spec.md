# Spec: inicio-cierre-sesion
Estado: borrador
Aprobación: ligera

## Objetivo (por qué)
Permitir que una persona entre en la herramienta con su correo y su contraseña y salga de ella
desde los **dos clientes** (la web y el escritorio), con dos garantías: solo entran las cuentas
activas, y cerrar sesión deja inservible la credencial tanto en el cliente como en el servidor.

El mecanismo de autenticación ya existe y está validado (feature `auth-headless`), pero le faltan
tres cosas para ser utilizable y seguro: no hay pantallas de inicio ni de cierre de sesión, ningún
test comprueba el rechazo de cuentas inactivas ni la invalidación tras el cierre, y el límite de
intentos fallidos está desactivado desde aquella feature, que lo dejó pendiente para la de
autenticación definitiva. Esta feature es la que lo reactiva.

## Requisitos funcionales

### RF-001 Inicio de sesión con correo y contraseña
Cuando una persona envíe desde cualquiera de los dos clientes el correo y la contraseña correctos
de una cuenta activa, el sistema deberá iniciar su sesión y llevarla a la aplicación.

### RF-002 Rechazo indistinguible de cuentas inactivas
Si una persona envía el correo y la contraseña correctos de una cuenta inactiva, entonces el
sistema deberá rechazar el inicio de sesión sin crear sesión ni credencial, con la misma respuesta
(código, cuerpo y mensaje en pantalla) que para unas credenciales inválidas.

### RF-003 Rechazo de credenciales inválidas en pantalla
Si las credenciales enviadas son inválidas, entonces el sistema deberá mostrar en la pantalla de
inicio de sesión un mensaje genérico de credenciales incorrectas, sin indicar si el correo existe,
y conservar el correo introducido.

### RF-004 Límite de intentos fallidos
Si se superan los intentos fallidos de inicio de sesión permitidos, entonces el sistema deberá
rechazar nuevos intentos durante un periodo de espera, aunque las credenciales sean correctas, y
mostrar un mensaje genérico que pida esperar antes de reintentar.

### RF-005 Cierre de sesión activo
Cuando una persona autenticada pulse «Cerrar sesión» en cualquiera de los dos clientes, el sistema
deberá invalidar en el servidor la sesión o el token desde el que se cierra, borrar la credencial
que guarda ese cliente y llevarla a la pantalla de inicio de sesión.

### RF-006 Credencial inservible tras el cierre
Cuando se presente una cookie de sesión o un token que se cerró con RF-005, el sistema deberá
tratar la petición como no autenticada.

### RF-007 Sesiones de otros dispositivos intactas
Cuando una persona cierre sesión en un cliente, el sistema deberá mantener válidas el resto de
sesiones abiertas de esa misma cuenta.

### RF-008 Cierre de sesión sin respuesta del servidor
Si el servidor no confirma el cierre de sesión (sin conexión o con error), entonces el cliente
deberá borrar igualmente su credencial, llevar a la persona a la pantalla de inicio de sesión y
avisarle de que el servidor no confirmó el cierre.

### RF-009 Desactivación con la sesión abierta
Mientras una cuenta esté inactiva, el sistema deberá tratar como no autenticadas todas las
peticiones con cookies de sesión o tokens emitidos a esa cuenta, incluidos los emitidos antes de
la desactivación.

### RF-010 Pérdida de sesión en el cliente
Cuando el servidor trate como no autenticada una petición de un cliente que creía tener sesión
(por cierre, caducidad o desactivación), el cliente deberá borrar su credencial y llevar a la
persona a la pantalla de inicio de sesión.

### RF-011 Protección de páginas privadas y vuelta al destino
Cuando una persona sin sesión abra una página privada, el sistema deberá llevarla a la pantalla de
inicio de sesión y, tras iniciarla, devolverla a la página que pidió.

### RF-012 Solo destinos internos
Si el destino de vuelta tras el inicio de sesión no es una página interna de la aplicación,
entonces el sistema deberá ignorarlo y llevar a la persona a la página de inicio.

### RF-013 Persistencia de la sesión entre aperturas
Mientras la sesión no haya caducado ni se haya cerrado, el sistema deberá mantener a la persona
autenticada al cerrar y volver a abrir el navegador o la aplicación de escritorio.

## Supuestos
- S-01 El estado activo/inactivo de la cuenta ya existe: `usuario-personalizado` (su RF-007)
  define que una cuenta inactiva no puede iniciar sesión, pero ninguna feature lo verifica en el
  inicio de sesión. Esta feature no añade formas de activar ni desactivar cuentas: usa las que ya
  existen (por ejemplo, el panel de administración).
- S-02 El correo se compara sin distinguir mayúsculas de minúsculas, como fija `auth-headless`
  (su RF-001).
- S-03 La duración de la sesión, el número de intentos fallidos permitidos y el periodo de espera
  de RF-004 son los valores por defecto de la librería de autenticación; el plan los concreta y la
  spec no fija cifras.
- S-04 Un intento con la contraseña correcta de una cuenta inactiva cuenta como intento fallido a
  efectos de RF-004, porque RF-002 lo hace indistinguible de una credencial inválida.
- S-05 Si una persona que ya tiene sesión abre la pantalla de inicio de sesión, se la lleva a la
  página de inicio.
- S-06 Los eventos de auditoría de inicio y cierre de sesión ya existen (feature
  `auditoria-eventos-seguridad`) y deben seguir registrándose; esta feature no los cambia.
- S-07 El cliente de escritorio reutiliza las pantallas del frontend web (principio P-08); lo
  único propio de cada cliente es cómo guarda y borra su credencial.
- S-08 Cerrar una sesión que el servidor ya había invalidado (por caducidad o desactivación) se
  trata como un cierre correcto, sin mensaje de error.

## Fuera de alcance
- Cerrar todas las sesiones de una cuenta («cerrar en todos los dispositivos»).
- Casilla «Recordarme» o sesiones que mueren al cerrar la aplicación.
- Registro, recuperación y cambio de contraseña (tienen sus propias features), salvo los enlaces
  que ya existan hacia ellas.
- Inicio de sesión con proveedores externos (Google, etc.) y segundo factor.
- Mensaje específico para cuentas inactivas (se descartó a favor de RF-002).
- Cambiar los valores por defecto del límite de intentos o de la duración de la sesión.

## Criterios de finalización
- CF-1 Una cuenta activa inicia sesión desde la web y desde el escritorio, entra en la aplicación,
  y la sesión sigue abierta tras cerrar y volver a abrir el cliente.
- CF-2 Con la contraseña correcta de una cuenta inactiva, la respuesta de la API y el mensaje en
  pantalla son idénticos a los de una contraseña incorrecta, y no se crea sesión.
- CF-3 Tras cerrar sesión, la cookie (web) o el token (escritorio) que se usaba recibe un rechazo
  de no autenticado, el cliente ya no guarda ninguna credencial y otra sesión de la misma cuenta
  sigue funcionando.
- CF-4 Al desactivar una cuenta con sesiones abiertas, la siguiente petición de cada una se
  rechaza y el cliente vuelve a la pantalla de inicio de sesión.
- CF-5 Superado el límite de intentos fallidos, un intento con la contraseña correcta se rechaza
  con el mensaje de espera.
- CF-6 Abrir una página privada sin sesión lleva al inicio de sesión y, tras entrar, a esa página;
  un destino externo se ignora.
- CF-7 Si el servidor no responde al cerrar sesión, el cliente borra su credencial, vuelve al
  inicio de sesión y muestra el aviso.
- CF-8 Suites `pytest` y `pnpm --filter frontend test` en verde, con cobertura ≥ 80 %, y tipos y
  lint limpios (P-04 a P-07).

## Historial de cambios
- 2026-11-16 — Creación (feature nueva) — RF: RF-001…RF-013 — Estado: pendiente de clarificar
