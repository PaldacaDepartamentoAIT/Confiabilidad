# Resumen — perfil-y-cambio-contrasena

## Qué se hizo
Se completó la autogestión de la cuenta autenticada (consulta y edición de datos personales y cambio de contraseña con conservación de la sesión actual y cierre de todas las demás) en backend (servicio, API dual web/escritorio y CLI) y en frontend (`/profile` en web y cliente de escritorio). Cada entrega tiene su propio resumen en [`entregas/`](entregas/).

**Backend** (`backend/apps/accounts/`):
- **Servicio de perfil (`E-01`, `profile.py`):** funciones `get_profile` y `update_profile` con actualización parcial mediante centinela `_Unset` (nombre completo, fecha de nacimiento y país de residencia, sin exponer ni modificar idioma ni consentimientos), normalización y validación reutilizando `usuario-personalizado` (conservando `"ZZ"` únicamente mientras el país no cambie), registro en `HistoricalRecords` y emisión de `signals.profile_edited` solo cuando algún campo normalizado cambia efectivamente.
- **Límite de intentos y cambio de contraseña (`E-02`, `throttling.py`, `conf.py`, `sessions.py`, `models.py`, `profile.py`):** limitador configurable por cuenta en caché (`5` intentos en `5` minutos con bloqueo de `5` minutos por defecto, ajustables por `PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS`, `PASSWORD_CHANGE_ATTEMPT_WINDOW_MINUTES` y `PASSWORD_CHANGE_LOCKOUT_MINUTES`), evaluación prioritaria de `current_password` (contabilizando el fallo aunque `new_password` falte o sea inválida), aceptación de nueva contraseña igual a la vigente si cumple la política, actualización atómica usando `_skip_password_session_revocation` para preservar la sesión actual (`refresh_current_session`: rotación de clave y `HASH_SESSION_KEY` en navegador; conservación de `X-Session-Token` en escritorio) mientras revoca de inmediato todas las demás en `UserSession` (`revoke_all_other_sessions`), auditoría de `PASSWORD_CHANGE` y de `LOGOUT` por cada sesión cerrada, encolado transaccional de `password_changed` siempre y `sessions_closed` solo cuando se cierran otras sesiones, y limpieza del contador de fallos en `transaction.on_commit`.
- **API dual y CLI (`E-01b`, `E-02b`, `E-05`, `profile_serializers.py`, `profile_views.py`, `messages.py`, `urls.py`, `management/commands/profile.py`):** rutas `/api/{browser,app}/v1/auth/profile` (`GET`, `PATCH`) y `/api/{browser,app}/v1/auth/password/change` (`POST`) con guarda de sesión activa y términos vigentes (`401` / `403 terms_required`), protección CSRF en `browser` y exención en `app`, rechazo explícito de `email` (`email_immutable`), peticiones vacías (`no_profile_fields`) y claves desconocidas (`unknown_field`), `429` con `Retry-After` y `retry_after` durante el bloqueo, mensajes traducidos a `es`, `pt-BR` y `en`, y comandos CLI `manage.py profile {show,edit,change-password}` (con `getpass` y `--keep-session-key`).

**Frontend** (`frontend/src/`):
- **Cliente API e i18n (`E-03`, `E-03b`, `E-04`, `api/client.ts`, `api/profile.ts`, `forms/countries.ts`, `registration/serverErrors.ts`, `i18n/locales/{es,pt-BR,en}.ts`):** método `patch` en `ApiClient`, deduplicación de peticiones `GET` concurrentes en vuelo, funciones `getProfile`, `updateProfile` y `changePassword`, helper compartido de países localizado con `Intl.DisplayNames`, mapeo de códigos de servidor (`email_immutable`, `unknown_field`, `no_profile_fields`, `current_password_incorrect`) y textos completos en los tres idiomas.
- **Pantalla `/profile` y mejoras de UI (`E-03`, `E-03b`, `E-04`, `E-05`, `ProfilePage.tsx`, `privateNav.tsx`, `UserProvider.tsx`, `Block.tsx`, `Menu.tsx`, `Button.css`, `ToastProvider.tsx`):** ruta privada `/profile` en `App.tsx` enlazada desde el menú lateral compartido (`privateNav.tsx`), estado persistente del usuario en contexto (`UserProvider.tsx`), *skeletons* con transición *fade* durante la carga en `/` y `/profile`, tarjeta única a ancho completo en solo lectura por defecto (correo `disabled` y nombre, país y fecha en fila de tres columnas, con `"ZZ"` mostrado como «Sin país asignado» y omitido al guardar si no cambia), menú vertical de tres puntos («Editar», «Cambiar contraseña» y «Deshabilitar» deshabilitada), validación local al salir del campo y al enviar con foco al primer error, descarte de errores locales al cancelar, confirmaciones mediante notificación flotante (*toast* en esquina inferior derecha), cambio de contraseña en dos columnas sin campo de repetición (mostrar/ocultar y requisitos en vivo), vaciado selectivo según el error, cuenta atrás persistente con botón deshabilitado ante `429`, redirecciones a `/login` y `/terms` y verificación de accesibilidad (`axe-core`).

### Entregas
| Entrega | Rama | PR |
|---|---|---|
| E-01 Servicio y comandos CLI de consulta y edición de perfil | `feat/perfil-y-cambio-contrasena-api-perfil` | `#153` |
| E-01b Endpoints HTTP de consulta y edición de perfil (`GET`/`PATCH auth/profile`) | `feat/perfil-y-cambio-contrasena-api-perfil-http` | `#154` |
| E-02 Servicio de cambio de contraseña con límite configurable y cierre de otras sesiones | `feat/perfil-y-cambio-contrasena-api-password` | `#155` |
| E-02b Endpoints HTTP y CLI de cambio de contraseña (`POST auth/password/change` y `profile change-password`) | `feat/perfil-y-cambio-contrasena-api-password-http` | `#156` |
| E-03 Pantalla `/profile`, *skeletons* con *fade*, usuario persistente y deduplicación de `GET` | `feat/perfil-y-cambio-contrasena-ui-perfil` | `#157` |
| E-03b Edición parcial de datos personales y menú de tarjeta en `/profile` | `feat/perfil-y-cambio-contrasena-ui-perfil-edicion` | `#158` |
| E-04 Formulario de cambio de contraseña en `/profile` | `feat/perfil-y-cambio-contrasena-ui-password` | `#159` |
| E-05 Correcciones de validación (limpieza de errores locales y cobertura de bloqueo entre sesiones) | `feat/perfil-y-cambio-contrasena-correcciones` | `#160` |

## Cómo probarlo

### En el navegador (o en el cliente de escritorio)
1. Levanta los servicios de desarrollo:

```bash
docker compose -f docker/docker-compose.yml up -d db redis backend worker frontend
```
Deberías ver los cinco servicios en marcha.

2. Inicia sesión en `http://localhost:5173/login` con una cuenta activa que tenga términos vigentes aceptados (y abre una segunda sesión en una ventana privada para verificar el cierre de otras sesiones al cambiar la contraseña).
3. En el menú lateral izquierdo, pulsa «Perfil» para abrir `/profile`:
   - Verás la tarjeta de «Información personal» en solo lectura a ancho completo, con el correo electrónico deshabilitado y nombre completo, país y fecha de nacimiento en fila horizontal. Si la cuenta conserva el país relleno `"ZZ"`, aparecerá «Sin país asignado».
4. Pulsa el menú vertical de tres puntos (esquina superior derecha de la tarjeta) y elige «Editar»:
   - Borra el nombre completo y pulsa `Tab` para comprobar la validación local (`Completa este campo.`); pulsa «Cancelar» y vuelve a abrir «Editar» comprobando que el nombre regresa al valor guardado y no reaparece el error anterior.
   - Modifica el nombre o la fecha y pulsa «Guardar cambios»: verás la notificación flotante (*toast*) en la esquina inferior derecha, la tarjeta volverá a solo lectura y el nombre actualizado aparecerá de inmediato en el pie del menú lateral.
5. Pulsa el menú de tres puntos y elige «Cambiar contraseña»:
   - Prueba una nueva contraseña corta para confirmar la lista de requisitos en vivo y la validación local sin envío al servidor.
   - Envía una contraseña actual incorrecta junto a una nueva válida: se vaciará solo «Contraseña actual» conservando la nueva; tras `5` fallos seguidos en `5` minutos verás la cuenta atrás y el botón deshabilitado hasta llegar a cero.
   - Envía la contraseña actual correcta y una nueva contraseña válida: verás la notificación flotante, volverás a solo lectura manteniendo abierta tu sesión actual y la otra ventana pasará a `/login` al intentar navegar o recargar.

### Con `curl` en cliente `app` (sin frontend)
Inicia sesión en dos sesiones distintas (`<TOKEN_A>` y `<TOKEN_B>`) con una cuenta activa y términos aceptados:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"ana@planta.com","password":"turbina-compresor-7-marea"}'
```
Deberías ver el objeto JSON con `session_token`; repite la llamada para obtener un segundo token (`<TOKEN_B>`).

Consulta el perfil con `<TOKEN_A>`:

```bash
curl -s http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <TOKEN_A>"
```
Deberías ver `email`, `name`, `birthdate` y `country`.

Edita parcialmente el nombre e intenta cambiar `email`:

```bash
curl -s -X PATCH http://localhost:8000/api/app/v1/auth/profile -H "Content-Type: application/json" -H "X-Session-Token: <TOKEN_A>" -d '{"name":"Ana Actualizada"}'
```
Deberías ver HTTP `200` con el perfil actualizado.

```bash
curl -i -s -X PATCH http://localhost:8000/api/app/v1/auth/profile -H "Content-Type: application/json" -H "X-Session-Token: <TOKEN_A>" -d '{"email":"otro@planta.com"}'
```
Deberías ver HTTP `400` con el código `email_immutable` en `errors.email`.

Cambia la contraseña con `<TOKEN_A>` y comprueba que `<TOKEN_A>` sigue funcionando mientras `<TOKEN_B>` pasa a `401`:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/password/change -H "Content-Type: application/json" -H "X-Session-Token: <TOKEN_A>" -d '{"current_password":"turbina-compresor-7-marea","new_password":"nueva-clave-segura-99"}'
```
Deberías ver `{"result":"password_changed"}`.

```bash
curl -i -s http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <TOKEN_A>"
```
Deberías ver HTTP `200` con los datos del perfil.

```bash
curl -i -s http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <TOKEN_B>"
```
Deberías ver HTTP `401` (`unauthenticated`).

### Desde consola (`manage.py profile`)
Consulta, edita o cambia la contraseña de una cuenta directamente desde backend:

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py profile show --email ana@planta.com
```
Deberías ver `email`, `name`, `birthdate` y `country` de la cuenta.

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py profile edit --email ana@planta.com --name "Ana Consola"
```
Deberías ver los datos actualizados impresos en consola.

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py profile change-password --email ana@planta.com
```
Deberías poder introducir la contraseña actual y la nueva sin eco (`getpass`) y ver el resultado con `revoked_sessions`.

### Tests y análisis estático
En el backend:

```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_profile_service.py apps/accounts/tests/test_profile_api.py --no-cov
```
Deberías ver `34 passed`.

```bash
docker compose -f docker/docker-compose.yml exec backend sh -c "ruff check . && black --check . && mypy ."
```
Deberías ver todos los análisis limpios sin errores.

En el frontend:

```bash
pnpm --filter frontend test
```
Deberías ver `69` archivos y `864` tests en verde.

```bash
pnpm --filter frontend lint && pnpm --filter frontend typecheck
```
Deberías ver ESLint y `tsc --noEmit` sin errores.

## Marco teórico

### Conservación de la sesión actual y rotación contra fijación de sesión
En Django, cada sesión guarda una huella de la contraseña (`HASH_SESSION_KEY`). Cuando cambia la contraseña, si esa huella no se actualiza en la sesión en curso, el siguiente request del propio usuario se invalida automáticamente (`401`). Para mantener abierta únicamente la sesión desde la que la persona cambió su contraseña (conocida su clave actual), el servidor actualiza `HASH_SESSION_KEY` en esa sesión, rota su identificador en navegador (regenerando la cookie y sincronizando `UserSession` para evitar fijación de sesión), conserva el token de escritorio (`X-Session-Token`) sin obligar a reautenticar y elimina de inmediato todas las demás filas de `UserSession` y sus sesiones en Redis.

### Idempotencia y auditoría selectiva en `PATCH`
Permitir actualizaciones parciales (`PATCH`) plantea dos riesgos: aceptar campos prohibidos (`email` o atributos desconocidos ignorados silenciosamente) y generar ruido en el historial de versiones (`HistoricalRecords`) o en auditoría (`SecurityEvent`) cuando el usuario pulsa «Guardar» sin cambiar nada. Usar el centinela `_Unset` distingue un campo omitido de un campo enviado, rechaza explícitamente `email` y claves desconocidas, y compara los valores **después de normalizarlos** (por ejemplo, recortando espacios en `name` o pasando `country` a mayúsculas) antes de guardar o emitir `profile_edited`.

### País relleno `"ZZ"` como transición compatible
Las cuentas heredadas o importadas sin país pueden almacenar `"ZZ"` en lugar de un código ISO 3166-1 oficial. En lugar de bloquear al usuario impidiéndole editar su nombre hasta elegir país, la API conserva `"ZZ"` mientras no se envíe un cambio de país, y la pantalla `/profile` lo muestra como «Sin país asignado» omitiendo `country` en la petición si sigue sin seleccionarse. Una vez guardado un país válido, volver a enviar `"ZZ"` se rechaza.

### Límite de intentos de contraseña actual compartido entre sesiones
Limitar los fallos por sesión permitiría probar contraseñas indefinidamente abriendo otra sesión o usando web y escritorio en paralelo. Por eso el contador de fallos (`5` intentos en `5` minutos con bloqueo de `5` minutos por defecto) se almacena por cuenta en caché, evalúa la contraseña actual incluso cuando la nueva contraseña falta o incumple la política, y solo se reinicia en `transaction.on_commit` cuando un cambio de contraseña se confirma en base de datos.
