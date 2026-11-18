# Entrega E-02 · Modelo `UserSession` y servicio básico de sesiones activas

Rama: `feat/inicio-cierre-sesion-servicio-sesiones` · PR: pendiente · Líneas de código y tests: 399 (límite: 400).

## Qué se hizo
- Se añadió el modelo `UserSession` (`accounts_usersession`) y la migración `0015_usersession`
  (`RF-007`, registro de sesiones activas):
  - guarda `user`, `session_key` (único de 64 caracteres para la huella HMAC), `ip`, `user_agent`
    (normaliza valores vacíos o de solo espacios a `"unknown"` y conserva íntegra cualquier cadena no
    vacía sin recortar; `C-08`), `created_at` y `last_seen_at` (indexado).
- Se implementó la primera parte del servicio `apps/accounts/sessions.py` (`RF-006`, cierre de la
  sesión actual; `RF-007`; `RF-008`, consulta de sesiones activas; `D-02`, huella HMAC e índice
  inverso en caché):
  - `register_session(request, user)`: registra la fila en `UserSession` con `audit_session_fingerprint`
    (nunca la clave en claro) y guarda el índice inverso `user-session-key:<huella> -> <clave>` en
    la caché `sessions` con el TTL de `conf.session_lifetime()`.
  - `is_session_active(raw_key, user_id)`: comprueba vigencia por tiempo y presencia en la caché de
    sesiones.
  - `touch_session(request, user)`: actualiza `last_seen_at`, `ip`, `user_agent` y TTL solo cuando ha
    transcurrido al menos `conf.session_activity_update_interval()` (60 s por defecto).
  - `list_active_sessions(user, current_session_key)`: limpia las filas vencidas o ausentes en el
    almacén de sesiones (`C-01`) y devuelve las activas ordenadas de más reciente a más antigua con
    `is_current` y sin exponer `session_key`.
  - `close_current_session(user, session_key)`: borra la fila de `UserSession`, el índice inverso y
    la sesión del almacén de Django.
- La entrega se dividió respecto a `T-006` (cierre de otras sesiones, invalidación masiva y purga,
  que pasa a `E-02b`) para mantenerse dentro del límite de 400 líneas por PR.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-004 | Modelo `UserSession` | `fe762cd` |
| T-005 | Servicio de sesiones: alta, actividad, consulta y cierre actual | `f90f1cf` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con el entorno y los servicios levantados, actualiza las ramas remotas y
cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/inicio-cierre-sesion-servicio-sesiones
```
Comprueba que no faltan migraciones por generar y aplica la migración `0015_usersession`:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py makemigrations --check --dry-run
```
Deberías ver `No changes detected`.
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py migrate
```
Deberías ver `Applying accounts.0015_usersession... OK`.

Ejecuta los tests nuevos de esta entrega:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_user_session_model.py apps/accounts/tests/test_sessions_service.py --no-cov -v
```
Deberías ver los 7 tests en verde.

Ejecuta los análisis estáticos y la suite del backend:
```bash
docker compose -f docker/docker-compose.yml exec backend mypy . && docker compose -f docker/docker-compose.yml exec backend ruff check . && docker compose -f docker/docker-compose.yml exec backend black --check .
```
Deberías ver los tres análisis sin errores.
```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver la suite en verde (si el contenedor `worker` de desarrollo está levantado, detenlo antes si quieres evitar la interferencia en `apps/core/tests/test_task_worker.py`).

## Marco teórico
### Huella HMAC en `UserSession` e índice inverso efímero en Redis
En la autenticación por token de escritorio (`X-Session-Token`), el valor que presenta el cliente es
la clave de sesión de Django. Si la tabla `UserSession` guardara esa clave en claro, cualquiera que
leyera una copia o consulta de la base de datos podría suplantar cualquier sesión abierta. Al guardar
en PostgreSQL únicamente la huella HMAC (`audit_session_fingerprint`) y mantener la correspondencia
`huella -> clave` solo en la caché Redis `sessions` (donde ya viven las sesiones activas y con su
mismo vencimiento), una lectura de la base de datos no sirve para suplantar sesiones, pero el
servidor conserva la capacidad de comprobar si una sesión sigue viva y revocarla al instante.
