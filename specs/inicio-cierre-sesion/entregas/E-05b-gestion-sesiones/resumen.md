# Entrega E-05b · API de listado y cierre de otras sesiones activas

Rama: `feat/inicio-cierre-sesion-gestion-sesiones` · PR: pendiente · Líneas de código y tests: 312 (límite: 400).

## Qué se hizo
- Se añadió `RevokeSessionSerializer` en `apps/accounts/api/auth_serializers.py` (`T-013`).
- Se implementaron las vistas protegidas por `_require_auth(..., require_terms=True)` en `apps/accounts/api/auth_views.py` y `apps/accounts/api/urls.py` (`T-013`, `RF-008`, `RF-009`, `RF-011`, `RF-018`):
  - `GET /api/{browser,app}/v1/auth/sessions`: limpia filas caducadas de la cuenta y devuelve las vigentes ordenadas de más reciente a más antigua con `id`, `ip`, `user_agent`, `created_at`, `last_seen_at` e `is_current` (nunca `session_key`).
  - `POST /api/{browser,app}/v1/auth/sessions/revoke`: revoca otra sesión concreta (`400 cannot_revoke_current_session` si es la actual, `404 not_found` si es ajena o no existe).
  - `POST /api/{browser,app}/v1/auth/sessions/revoke-others`: revoca todas las demás sesiones activas y responde `{"result": "revoked", "revoked_count": <n>}` (con `revoked_count: 0` y sin eventos de auditoría si no había otras sesiones).
- Se añadieron los tests de integración `apps/accounts/tests/test_sessions_api.py` (`CF-4`, `C-01`, `C-05`, `C-06`).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-013 | Rutas de listado y cierre de otras sesiones activas | `3fc6eee` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con el entorno y los servicios levantados, actualiza las ramas remotas y cambia a la rama de la entrega:

```bash
git fetch origin
```

```bash
git checkout feat/inicio-cierre-sesion-gestion-sesiones
```
Deberías ver tu copia de trabajo en `feat/inicio-cierre-sesion-gestion-sesiones`.

Ejecuta los tests de esta entrega:

```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_sessions_api.py --no-cov -v
```
Deberías ver todos los tests de listado y revocación de sesiones en verde.

Ejecuta los análisis estáticos y la suite completa del backend:

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
Deberías ver todos los archivos con el formato correcto.

```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver toda la suite en verde con cobertura ≥ 80 %.

### Prueba en vivo con `curl` (cliente `app`)
Con un usuario activo que ya haya aceptado los términos vigentes (ver pasos en `E-05`), abre dos sesiones `app` distintas y copia sus tokens como `<TOKEN_1>` y `<TOKEN_2>`:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"demo@example.com","password":"DemoPass123!","language":"es"}'
```
Deberías ver el primer `session_token` (`<TOKEN_1>`).

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"demo@example.com","password":"DemoPass123!","language":"es"}'
```
Deberías ver el segundo `session_token` (`<TOKEN_2>`).

Lista las sesiones activas usando `<TOKEN_2>` (copia el `id` donde `"is_current": false` como `<OTHER_ID>`):

```bash
curl -s http://localhost:8000/api/app/v1/auth/sessions -H "X-Session-Token: <TOKEN_2>"
```
Deberías ver dos sesiones: una con `"is_current": true` y la otra con `"is_current": false`.

Revoca `<OTHER_ID>` desde `<TOKEN_2>` y comprueba que `<TOKEN_1>` deja de autenticar al instante:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/sessions/revoke -H "Content-Type: application/json" -H "X-Session-Token: <TOKEN_2>" -d '{"session_id": <OTHER_ID>}'
```
Deberías ver `{"result":"revoked"}`.

```bash
curl -s http://localhost:8000/api/app/v1/auth/session -H "X-Session-Token: <TOKEN_1>"
```
Deberías ver HTTP 401 con `"code":"unauthenticated"`.
