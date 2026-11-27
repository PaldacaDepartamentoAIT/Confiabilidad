# Entrega E-02b · Endpoints HTTP y CLI de cambio de contraseña (`POST auth/password/change` y `profile change-password`)

Rama: `feat/perfil-y-cambio-contrasena-api-password-http` · PR: #156 · Líneas de código y tests: 394 (límite: 400).

## Qué se hizo
- En `backend/apps/accounts/api/profile_serializers.py` y `backend/apps/accounts/api/messages.py` (`T-007`, `RF-007` y `RF-013`) se añadió `PasswordChangeSerializer` y el mensaje `current_password_incorrect` en `es`, `pt-BR` y `en`, permitiendo evaluar primero la contraseña actual incluso cuando `new_password` falte o esté vacía para que cuente en el límite de `RF-008`.
- En `backend/apps/accounts/api/profile_views.py` y `backend/apps/accounts/api/urls.py` (`T-008`, `RF-006`…`RF-009`, `RF-011`, `RF-013`) se expusieron `AppPasswordChangeView` (`/api/app/v1/auth/password/change`) y `BrowserPasswordChangeView` (`/api/browser/v1/auth/password/change`):
  - exigen sesión válida, cuenta activa, términos vigentes aceptados y protección CSRF en el cliente web;
  - comprueban el bloqueo `429` (`Retry-After` y `retry_after`) antes de evaluar contraseñas, manteniendo abierta la sesión actual;
  - devuelven errores de campo con códigos estables (`current_password_incorrect`, códigos de política de contraseñas, `required`, `blank`, `null`) o `200` (`{"result": "password_changed"}`) conservando la sesión actual e invalidando el resto.
- En `backend/apps/accounts/management/commands/profile.py` (`T-009`, `RF-015`) se añadió el subcomando `profile change-password --email ...` con entrada sin eco vía `getpass` cuando se omiten `--current-password` o `--new-password`, y opción `--keep-session-key`.
- En `backend/apps/accounts/tests/test_profile_api.py` y `backend/apps/accounts/tests/test_profile_service.py` se añadieron pruebas de serializador, flujo completo con dos sesiones simultáneas entre clientes (`browser` y `app`), bloqueo `429`, CSRF, términos pendientes y subcomando CLI.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-007 | Serializador de cambio de contraseña y mensajes multiidioma | `ad91358` |
| T-008 | Endpoints `POST` de `auth/password/change` para web y escritorio | `210d28e` |
| T-009 | Subcomando CLI `profile change-password` | `7a78bc4` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con Docker, PostgreSQL y Redis levantados, actualiza las ramas remotas y cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/perfil-y-cambio-contrasena-api-password-http
```
Ejecuta los tests nuevos de backend (sin umbral global sobre otros módulos):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_profile_api.py apps/accounts/tests/test_profile_service.py -v --no-cov
```
Deberías ver todos los tests en verde.

Ejecuta la suite completa, `mypy .`, `ruff check .` y `black --check .`:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver toda la suite en verde con cobertura ≥ 80 %.
```bash
docker compose -f docker/docker-compose.yml exec backend mypy .
```
Deberías ver `Success: no issues found`.
```bash
docker compose -f docker/docker-compose.yml exec backend ruff check .
```
Deberías ver `All checks passed!`.
```bash
docker compose -f docker/docker-compose.yml exec backend black --check .
```
Deberías ver `All done!`.

Para probar el cierre de las demás sesiones con `curl` (usa una cuenta activa con términos aceptados; `<EMAIL>` y `<PASSWORD>` son sus credenciales actuales):
1. Inicia dos sesiones (`<TOKEN_1>` y `<TOKEN_2>` son los valores `session_token` devueltos):
```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"<EMAIL>","password":"<PASSWORD>"}'
```
```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"<EMAIL>","password":"<PASSWORD>"}'
```
2. Cambia la contraseña usando `<TOKEN_1>` (`<NEW_PASSWORD>` debe cumplir la política de 12 o más caracteres):
```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/password/change -H "X-Session-Token: <TOKEN_1>" -H "Content-Type: application/json" -d '{"current_password":"<PASSWORD>","new_password":"<NEW_PASSWORD>"}'
```
Deberías ver `{"result":"password_changed"}`.
3. Verifica que `<TOKEN_1>` sigue autenticando y `<TOKEN_2>` devuelve `401`:
```bash
curl -i -s http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <TOKEN_1>"
```
Deberías ver `HTTP/1.1 200 OK`.
```bash
curl -i -s http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <TOKEN_2>"
```
Deberías ver `HTTP/1.1 401 Unauthorized`.

Para probar también desde consola (`<EMAIL>` es el correo de la cuenta):
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py profile change-password --email <EMAIL>
```
Te pedirá la contraseña actual y la nueva sin mostrarlas en pantalla, y mostrará `account: <EMAIL>` y `revoked_sessions: ...`.
