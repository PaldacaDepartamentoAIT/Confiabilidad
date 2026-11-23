# Resumen — inicio-cierre-sesion

## Qué se hizo
Se completó el flujo de inicio y cierre de sesión, aceptación de términos pendientes tras un cambio de versión, listado y revocación selectiva o masiva de otras sesiones activas y limpieza de sesiones caducadas, tanto en el navegador (`browser`) como en el cliente de escritorio (`app`). Cada entrega tiene su propio resumen en [`entregas/`](entregas/).

**Backend** (`backend/apps/accounts/`):
- **Seguridad e intentos (`E-01`, `E-04b`):** configuración y límites de tasa por IP (`30/m` en `/auth/login`, `/auth/terms/accept` y `/auth/sessions/revoke*`), cálculo de intentos fallidos y bloqueo al sexto fallo (también en cuentas inactivas mediante `AuditAccountAdapter.record_inactive_login_attempt`) con respuestas idénticas y sin filtrar existencia ni estado de la cuenta (neutralidad en el cuerpo y en la cabecera `Vary: Cookie`).
- **Modelo y ciclo de vida (`E-02`, `E-02b`, `E-03`):** modelo `UserSession` (`session_key` en SHA-256 sin guardar el token en claro, IP, `user_agent`, fechas de creación y última actividad), servicio de listado y revocación individual o masiva de sesiones, invalidación automática al cerrar sesión, desactivar la cuenta, borrarla o cambiar/restablecer la contraseña, y purga periódica (`purge_expired_sessions` cada hora en Celery beat y como comando `manage.py purge_expired_sessions`).
- **API propia (`E-04`, `E-05`, `E-05b`):** endpoints bajo `/api/browser/v1/auth/…` (cookie + CSRF) y `/api/app/v1/auth/…` (`X-Session-Token`): `login`, `session`, `logout`, `terms/accept`, `sessions`, `sessions/revoke` y `sessions/revoke-others`. Las rutas de gestión de sesiones exigen sesión activa y términos vigentes aceptados (`401 unauthenticated` o `403 terms_required`), mientras que `session`, `logout` y `terms/accept` quedan accesibles con términos pendientes.

**Frontend** (`frontend/src/`):
- **Cliente de API (`E-06`, `E-06b`):** almacén en memoria `tokenStorage.ts` para `X-Session-Token` en escritorio, captura automática del token y manejo uniforme de `401 unauthenticated` y `403 terms_required` en `client.ts`, funciones `getSession`, `login`, `logout`, `acceptTerms`, `listSessions`, `revokeSession` y `revokeOtherSessions` en `api/auth.ts`, y mensajes multilingües (`es`, `pt-BR`, `en`).
- **Componentes reutilizados y mejoras visuales (`E-07c`, `E-07d`, `E-07e`):** componente `IconButton` (borde e icono en el color principal, tooltip hacia arriba y tamaño compacto `28 × 28 px` en tablas), menús de idioma y usuario desplegándose hacia arriba en `Sidebar` (con «Cerrar sesión» en el menú de usuario y colores del avatar invertidos en modo claro), columnas redimensionables con elipsis dinámica (`...`) y selección múltiple con casillas y barra superpuesta sobre la cabecera de `Table`.
- **Pantallas, rutas y accesibilidad (`E-07`, `E-07b`, `E-08`, `E-09`):**
  - `/login` (`LoginPage`): correo, contraseña, límite con cuenta atrás y enlace a `/register`.
  - `/terms` (`TermsPage`): muestra la versión vigente en Markdown dentro de `DocumentCheckbox`, botón para aceptar y salir o cerrar sesión si falta una versión vigente.
  - `/` (`HomePage`): área privada con `AppLayout`, nombre/iniciales y cierre de sesión en el menú de usuario del pie lateral, tabla seleccionable de sesiones activas (marcando la actual con `Chip` y permitiendo seleccionar y cerrar una o varias de las demás desde la barra superior de la tabla).
  - `/showcase` (`ShowcasePage`): catálogo de componentes trasladado fuera de `/`.
  - Enlaces a `/login` desde `/register` y `/register/done`, guardas y redirecciones en `App.tsx` y pruebas de accesibilidad (`auth/a11y.test.tsx`).

### Entregas
| Entrega | Rama |
|---|---|
| E-01 Límites e intentos en cuenta inactiva | `feat/inicio-cierre-sesion-limites` |
| E-02 Modelo `UserSession` y servicio básico | `feat/inicio-cierre-sesion-servicio-sesiones` |
| E-02b Cierre masivo, invalidación y purga en servicio | `feat/inicio-cierre-sesion-revocar-sesiones` |
| E-03 Señales de ciclo de vida y comando `purge_expired_sessions` | `feat/inicio-cierre-sesion-purga` |
| E-04 Catálogo de mensajes y API de autenticación | `feat/inicio-cierre-sesion-api-auth` |
| E-04b Neutralidad y bloqueo en inicio de sesión | `feat/inicio-cierre-sesion-neutralidad` |
| E-05 Aceptación de términos pendientes y guarda | `feat/inicio-cierre-sesion-api-sesiones` |
| E-05b Listado y cierre de otras sesiones | `feat/inicio-cierre-sesion-gestion-sesiones` |
| E-06 Cliente de autenticación y `tokenStorage` | `feat/inicio-cierre-sesion-cliente-auth` |
| E-06b Textos y errores en cliente | `feat/inicio-cierre-sesion-textos-auth` |
| E-07 Pantalla de inicio de sesión | `feat/inicio-cierre-sesion-pantallas-acceso` |
| E-07b Pantalla de términos y rutas `/login` y `/terms` | `feat/inicio-cierre-sesion-pantalla-terminos` |
| E-07c `IconButton`, menús hacia arriba y menú de usuario | `feat/inicio-cierre-sesion-componentes-menu` |
| E-07d Columnas redimensionables y elipsis en tablas | `feat/inicio-cierre-sesion-tabla-redimensionable` |
| E-07e Selección de filas en tablas | `feat/inicio-cierre-sesion-tabla-seleccion` |
| E-08 Área privada, gestión de sesiones y `/showcase` | `feat/inicio-cierre-sesion-pantalla-sesiones` |
| E-09 Enlaces a `/login`, redirecciones, accesibilidad y resumen | `feat/inicio-cierre-sesion-rutas` |

## Cómo probarlo

### En el navegador (o en el cliente de escritorio)
1. Levanta los servicios de desarrollo:

```bash
docker compose -f docker/docker-compose.yml up -d db redis backend worker frontend
```
Deberías ver los cinco servicios en marcha.

2. Asegúrate de tener las migraciones aplicadas y términos vigentes publicados (creados con una cuenta verificada como en `specs/registro-flujo/resumen.md` o mediante `manage.py`):

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py migrate
```
Deberías ver las migraciones aplicadas sin errores pendientes.

3. Abre `http://localhost:5173/`: al no haber sesión activa te redirigirá a `http://localhost:5173/login`.
4. Prueba los enlaces públicos:
   - Pulsa «Crear una cuenta» en `/login` y confirma que abre `http://localhost:5173/register` sin recargar.
   - Pulsa «Iniciar sesión» en `/register` y confirma que vuelve a `http://localhost:5173/login` sin recargar.
5. Inicia sesión con una cuenta activa:
   - Si no ha aceptado los términos vigentes, entrarás en `/terms`; lee el documento, marca la casilla y pulsa «Aceptar y continuar» para ir a `/`.
   - Con términos aceptados, entrarás en `/` («Panel principal»), donde verás tu usuario en el pie del menú lateral y la tabla «Sesiones activas».
   - Si estando autenticado abres `/login` o `/register`, te devolverá automáticamente a `/` (o a `/terms` si faltan términos).
6. En una segunda ventana (o navegador privado) inicia sesión con la misma cuenta, vuelve a la primera ventana y recarga `/` para ver ambas sesiones. Marca la casilla de la otra sesión (o la casilla superior para seleccionar todas las demás) y pulsa el botón de icono en la barra superior de la tabla para cerrarla.
7. Abre el menú del usuario en la base del menú lateral y pulsa «Cerrar sesión» para volver a `/login`.
8. Abre `http://localhost:5173/showcase` para comprobar el catálogo de componentes fuera de `/`.

### Con `curl` en cliente `app` (sin frontend)
Inicia sesión con una cuenta activa (sustituye correo y contraseña por los de tu cuenta de prueba):

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"ana@planta.com","password":"turbina-compresor-7-marea"}'
```
Deberías ver `session_token`, `user` y `terms_status`. Guarda ese `session_token` como `<TOKEN>` para los pasos siguientes.

Consulta la sesión actual:

```bash
curl -s http://localhost:8000/api/app/v1/auth/session -H "X-Session-Token: <TOKEN>"
```
Deberías ver el estado de la sesión (si `terms_status` es `"not_accepted"`, acéptalos primero con `POST /api/app/v1/auth/terms/accept` usando el `version` y `locale` recibidos).

Lista las sesiones activas:

```bash
curl -s http://localhost:8000/api/app/v1/auth/sessions -H "X-Session-Token: <TOKEN>"
```
Deberías ver la lista `sessions` ordenada de más reciente a más antigua con `is_current: true` en la tuya y ningún campo `session_key`. Toma el `id` de otra sesión como `<SESSION_ID>` para revocarla:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/sessions/revoke -H "Content-Type: application/json" -H "X-Session-Token: <TOKEN>" -d '{"session_id":<SESSION_ID>}'
```
Deberías ver `{"result":"revoked"}`.

Revoca todas las demás sesiones activas de golpe:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/sessions/revoke-others -H "Content-Type: application/json" -H "X-Session-Token: <TOKEN>" -d '{}'
```
Deberías ver `{"result":"revoked","revoked_count":<N>}`.

Prueba la neutralidad ante cuenta inexistente, contraseña incorrecta o cuenta inactiva: repite un `POST` a `/api/app/v1/auth/login` con distintos correos o claves incorrectas y tras 6 intentos desde la misma IP/cuenta recibirás `too_many_login_attempts`.

Cierra la sesión actual:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/logout -H "Content-Type: application/json" -H "X-Session-Token: <TOKEN>" -d '{}'
```
Deberías ver `{"result":"logged_out"}`, y cualquier llamada posterior con `<TOKEN>` responderá `401 unauthenticated`.

### Limpieza de sesiones caducadas desde consola
Para ejecutar la purga manual equivalente a la tarea horaria de Celery beat:

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py purge_expired_sessions
```
Deberías ver `<N> expired user sessions deleted.`.

### Tests y análisis estático
En el backend:

```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver toda la suite del backend en verde con cobertura ≥ 80 %.

```bash
docker compose -f docker/docker-compose.yml exec backend mypy .
```
Deberías ver `Success: no issues found`.

```bash
docker compose -f docker/docker-compose.yml exec backend ruff check .
```
Deberías ver la salida limpia sin advertencias.

```bash
docker compose -f docker/docker-compose.yml exec backend black --check .
```
Deberías ver todos los archivos formateados.

En el frontend:

```bash
pnpm --filter frontend test
```
Deberías ver toda la suite del frontend en verde.

```bash
pnpm --filter frontend lint
```
Deberías ver ESLint limpio.

```bash
pnpm --filter frontend typecheck
```
Deberías ver `tsc --noEmit` terminar sin errores.

```bash
pnpm --filter frontend test:visual
```
Deberías ver todas las pruebas visuales en Chromium en verde.

## Marco teórico

### Neutralidad de respuesta y cabecera `Vary: Cookie`
Si un endpoint responde distinto cuando una cuenta existe pero está inactiva frente a cuando no existe —ya sea en el código HTTP, en el mensaje o incluso en las cabeceras HTTP como `Vary: Cookie`—, un atacante puede enumerar correos registrados. Delegar en allauth las rutas reales sin sesión ni efecto distinto garantiza respuestas indistinguibles mientras se registra la auditoría (`LOCKOUT`) en cuentas reales inactivas.

### Puerta de términos vigentes en el área privada
Guardar solo una marca booleana de «aceptó términos al registrarse» deja fuera de cumplimiento a los usuarios antiguos cuando cambia la versión legal vigente. Comprobar en cada acceso al área privada el estado frente al documento publicado en vigor (`terms_status: "accepted" | "not_accepted" | "no_current_version"`) obliga a aceptar la nueva versión en `/terms` sin permitir llamadas de negocio (`403 terms_required`), pero manteniendo accesibles `session`, `logout` y `terms/accept`.

### Doble cliente: cookie + CSRF en web frente a `X-Session-Token` en escritorio
La versión web comparte origen a través del proxy y protege las mutaciones con cookie `HttpOnly` + cabecera CSRF. El cliente de escritorio (Tauri) puede operar contra el origen del servidor usando `X-Session-Token` por cabecera sin depender de cookies de terceros; mantener el token en memoria en `tokenStorage.ts` evita dejar credenciales persistentes en disco cuando no está habilitada una sesión recordada, y en el servidor `UserSession` guarda solo el resumen SHA-256 de la clave (`session_key`) para que una filtración de la base de datos de sesiones no permita suplantar sesiones activas.
