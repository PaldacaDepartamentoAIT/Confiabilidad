# Entrega E-01b · Endpoints HTTP de consulta y edición de perfil (`GET`/`PATCH auth/profile`)

Rama: `feat/perfil-y-cambio-contrasena-api-perfil-http` · PR: pendiente · Líneas de código y tests: 368 (límite: 400).

## Qué se hizo
- En `backend/apps/accounts/api/profile_serializers.py` y `backend/apps/accounts/api/messages.py` se implementó `ProfileUpdateSerializer` (`RF-002`, `RF-003`, `RF-004`, `RF-013`):
  - admite actualización parcial con `name`, `birthdate` y `country` (tolerando `language` para seleccionar el idioma de respuesta);
  - rechaza explícitamente `email` con código `email_immutable`, cualquier campo desconocido con `unknown_field`, y peticiones sin ningún campo editable con `no_profile_fields`;
  - valida `name`, `birthdate` y `country` (preservando `"ZZ"` solo mientras el país guardado sea `"ZZ"`) y añade mensajes en `es`, `pt-BR` y `en` en `messages.py`.
- En `backend/apps/accounts/api/profile_views.py` y `backend/apps/accounts/api/urls.py` se expusieron `AppProfileView` (`/api/app/v1/auth/profile`) y `BrowserProfileView` (`/api/browser/v1/auth/profile`) con `GET` y `PATCH` (`RF-001`…`RF-004`, `RF-011`, `RF-013`):
  - exigen sesión válida, cuenta activa y términos vigentes aceptados (`_require_auth(..., require_terms=True)`);
  - exigen protección CSRF en el cliente web (`_BrowserCsrfMixin` + `ensure_csrf_cookie` en `GET`) y credencial `X-Session-Token` en el de escritorio.
- En `backend/apps/accounts/tests/test_profile_api.py` se añadieron pruebas de serializador, mensajes en los 3 idiomas y flujo HTTP completo en `browser` y `app`.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-002 | Validación estricta del cuerpo de perfil y mensajes multiidioma | `3c7822f` |
| T-003 | Endpoints `GET` y `PATCH` de `auth/profile` para web y escritorio | `ab7dbd1` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con Docker, PostgreSQL y Redis levantados, actualiza las ramas remotas y cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/perfil-y-cambio-contrasena-api-perfil-http
```
Ejecuta los tests de esta entrega (sin umbral global sobre otros módulos):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_profile_api.py -v --no-cov
```
Deberías ver todos los tests de `test_profile_api.py` en verde.

Ejecuta la suite completa y `mypy`:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver toda la suite en verde con cobertura ≥ 80 %.
```bash
docker compose -f docker/docker-compose.yml exec backend mypy .
```
Deberías ver `Success: no issues found`.

Para probar el endpoint desde consola con `curl` (usa una cuenta activa con términos vigentes aceptados; inicia sesión en `app` para obtener `<TOKEN>`):
```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"<EMAIL>","password":"<PASSWORD>"}'
```
Con el `session_token` devuelto (`<TOKEN>`), consulta tu perfil:
```bash
curl -s http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <TOKEN>"
```
Deberías ver el JSON con `email`, `name`, `birthdate` y `country`. Actualiza un campo:
```bash
curl -s -X PATCH http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <TOKEN>" -H "Content-Type: application/json" -d '{"name":"Nombre API"}'
```
Deberías ver el perfil actualizado. Intenta enviar `email` para verificar su rechazo:
```bash
curl -s -X PATCH http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <TOKEN>" -H "Content-Type: application/json" -d '{"email":"otro@example.com"}'
```
Deberías ver HTTP 400 con el código `email_immutable` en `errors.email`.

## Marco teórico
### Actualización parcial (`PATCH`) con lista blanca estricta de claves
En DRF, por defecto un serializador ignora las claves desconocidas del JSON entrante. Si un cliente intenta modificar `email` o envía por error un nombre de campo equivocado (`nombre` en lugar de `name`), ignorarlo en silencio podría devolver `200` sin aplicar el cambio o hacer creer que el correo es editable. Validar explícitamente las claves recibidas en `to_internal_value` distingue `email_immutable`, `unknown_field` y `no_profile_fields` antes de validar tipos y reglas de negocio.
