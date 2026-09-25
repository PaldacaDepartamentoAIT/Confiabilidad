# Spec: auth-headless
Estado: aprobada

## Objetivo (por qué)
Dotar al sistema de autenticación para sus **dos clientes**: la aplicación web (que mantiene
sesión por cookie) y el cliente de escritorio Tauri (que autentica por un token de sesión en
cabecera). Es un cimiento de seguridad reutilizable por el resto de features. En esta iteración
el usuario y los flujos son **de prueba**, solo para validar el mecanismo; los modelos y flujos
definitivos llegan en una feature posterior.

## Requisitos funcionales

### RF-001 Identidad por email
El sistema deberá identificar cada cuenta de usuario por su **email** (único y normalizado a
minúsculas / case-insensitive) y autenticarla con email y contraseña.

### RF-002 Inicio de sesión del cliente web (cookie)
Cuando un usuario envía credenciales válidas desde el cliente web, el sistema deberá
autenticarlo y establecer una **sesión basada en cookie**.

### RF-003 Inicio de sesión del cliente de aplicación (token)
Cuando un usuario envía credenciales válidas desde el cliente de aplicación, el sistema deberá
autenticarlo y devolver un **token de sesión** que el cliente presenta en una cabecera
(`X-Session-Token`) en las peticiones siguientes.

### RF-004 Consulta de la sesión actual
El sistema deberá permitir consultar la sesión actual y devolver el usuario autenticado, tanto
por cookie (cliente web) como por token (cliente de aplicación).

### RF-005 Rechazo de credenciales inválidas
Si las credenciales son inválidas, entonces el sistema deberá rechazar el inicio de sesión sin
establecer sesión ni emitir token.

### RF-006 Protección CSRF del cliente web
Mientras se use el cliente web basado en cookie, el sistema deberá exigir protección CSRF en las
peticiones que cambian estado (como el inicio de sesión). El cliente de aplicación (token) queda
**exento de CSRF** por no depender de cookies.

### RF-007 CORS para el cliente de escritorio
El sistema deberá aceptar peticiones con credenciales desde los **orígenes configurados del
cliente Tauri** —multiplataforma: `tauri://localhost` (macOS/Linux), `http(s)://tauri.localhost`
(Windows) y `http://localhost:<puerto>` (desarrollo)— y rechazar los orígenes no permitidos.

### RF-008 Cookies seguras en producción
Mientras el sistema opere en producción, el sistema deberá marcar la cookie de sesión y la de
CSRF como `Secure`, y la de sesión como `HttpOnly`.

### RF-009 HTTPS tras proxy en producción
Mientras el sistema opere en producción, el sistema deberá forzar HTTPS y reconocer el esquema
HTTPS que reenvía el proxy de confianza.

### RF-010 IP real del cliente tras el proxy
El sistema deberá determinar la IP real del cliente como la **última entrada** de la cabecera
`X-Forwarded-For` que añade el único proxy de confianza, y no una entrada anterior (suplantable)
ni la dirección del proxy.

## Supuestos
- S-01 El usuario de prueba se crea por seed/fixture/management command; **no hay signup** en
  esta feature.
- S-02 El modelo de usuario es un **placeholder mínimo** (email + contraseña); los campos
  completos del dominio llegan en la feature siguiente ("modelos completos").
- S-03 El endurecimiento (cookies `Secure`, redirección a HTTPS) se aplica **en producción**
  (`DEBUG=False`); en desarrollo local (HTTP) se relaja para no romper el flujo.
- S-04 Solo **cuenta local** (email + contraseña); proveedores sociales fuera de alcance.
- S-05 La **verificación de email está desactivada** en esta feature de prueba.
- S-06 La web y la API se sirven en el **mismo origen**; en desarrollo se preserva vía el proxy
  del dev server (Vite). CORS aplica **solo** al cliente de escritorio (que usa token).
- S-07 El cliente de aplicación (token) está **exento de CSRF** (no usa cookie); CSRF solo
  protege al cliente web. *Por qué:* sin autoridad ambiental (cookie) no hay petición forjable.
- S-08 Se asume **un único proxy inverso de confianza**; la IP real es la última entrada de
  `X-Forwarded-For`. *Por qué:* las entradas anteriores puede falsificarlas el cliente. Ajustable
  si se añaden más saltos (CDN, etc.).
- S-09 El **rate limiting / bloqueo por intentos fallidos se desactiva** en esta feature de
  prueba; se (re)activará en la feature de auth definitiva (ajuste de settings, no perjudica a
  futuro).

## Fuera de alcance
- Registro (signup), recuperación y cambio de contraseña, verificación de email.
- Proveedores sociales (Google, etc.).
- Modelos de dominio completos (usuario definitivo, roles, permisos de negocio).
- Logout como objetivo de verificación (queda disponible, pero no se verifica aquí).
- Interfaz de usuario del frontend.
- Límite de intentos fallidos / rate limiting (se reactivará en la feature de auth definitiva).

## Criterios de finalización
- CF-1 Un usuario de prueba inicia sesión desde el cliente web (cookie) y la consulta de sesión
  devuelve ese usuario.
- CF-2 Un usuario de prueba inicia sesión desde el cliente de aplicación (token) y la consulta de
  sesión con `X-Session-Token` devuelve ese usuario.
- CF-3 Un intento con credenciales inválidas es rechazado.
- CF-4 Son verificables: CORS permite el origen de Tauri y rechaza otros; las cookies son seguras
  en producción; la IP real se obtiene de `X-Forwarded-For`.
- CF-5 Suite `pytest` en verde con cobertura ≥ 80 %, y `mypy`/`ruff`/`black` limpios.

## Historial de cambios
- 2026-09-25 — Creación (feature nueva) — RF: RF-001…RF-010 — Estado: clarificado
- 2026-09-25 — Clarificación — RF: RF-001, RF-006, RF-007, RF-010 ajustados; S-06…S-09 añadidos;
  rate limiting fuera de alcance — Estado: clarificado
