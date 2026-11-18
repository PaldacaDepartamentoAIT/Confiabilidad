# Entrega E-04 · Catálogo de mensajes y API de autenticación

Rama: `feat/inicio-cierre-sesion-api-auth` · PR: pendiente · Líneas de código y tests: 424 (límite: 400; excepción hasta 500 por mantener en una única entrega el catálogo de mensajes y los tres endpoints `login`/`session`/`logout` para `browser` y `app`).

## Qué se hizo
- Se añadieron los mensajes multilingües (`es`, `pt-BR`, `en`) para autenticación y cierre de sesión en `apps/accounts/api/messages.py` (`T-009`, `RF-002`, `RF-005`, `RF-012`, `RF-019`):
  - `invalid_credentials`, `too_many_login_attempts`, `already_authenticated`, `unauthenticated`, `terms_required` y `cannot_revoke_current_session`.
- Se implementaron los endpoints propios de autenticación en `apps/accounts/api/auth_serializers.py`, `apps/accounts/api/auth_views.py` y `apps/accounts/api/urls.py` (`T-010`, `RF-001`..`RF-006`, `RF-018`):
  - `POST /api/browser/v1/auth/login` y `POST /api/app/v1/auth/login`: validan credenciales con normalización de correo, respetan el límite de 30 req/min por IP, rechazan sesiones ya activas con `400 already_authenticated`, delegan el inicio de sesión en el adaptador de allauth y devuelven usuario + estado de términos (`terms_status`, `terms`) y `session_token` en clientes `app`.
  - `GET /api/browser/v1/auth/session` (asegura la cookie CSRF) y `GET /api/app/v1/auth/session` (por cabecera `X-Session-Token`): devuelven el estado actual de la sesión y términos, o `401 unauthenticated` si no hay sesión activa.
  - `POST /api/browser/v1/auth/logout` y `POST /api/app/v1/auth/logout`: cierran la sesión activa y devuelven `200 {"result": "logged_out"}` o `401 unauthenticated` sin registrar evento cuando no había sesión (`C-05`).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-009 | Catálogo de mensajes de error de autenticación y sesiones (`es`, `pt-BR`, `en`) | `8142236` |
| T-010 | API propia de login, estado de sesión y logout para `browser` y `app` | `ce07107` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con el entorno y los servicios levantados, actualiza las ramas remotas y cambia a la rama de la entrega:

```bash
git fetch origin
```

```bash
git checkout feat/inicio-cierre-sesion-api-auth
```

Ejecuta los tests nuevos y modificados de esta entrega:

```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_registration_api_messages.py apps/accounts/tests/test_auth_api.py --no-cov -v
```
Deberías ver todos los tests de mensajes y autenticación en verde.

Ejecuta los análisis estáticos y la suite completa del backend:

```bash
docker compose -f docker/docker-compose.yml exec backend mypy .
```
Deberías ver `Success: no issues found` sin errores de tipado.

```bash
docker compose -f docker/docker-compose.yml exec backend ruff check .
```
Deberías ver la salida limpia sin advertencias de linter.

```bash
docker compose -f docker/docker-compose.yml exec backend black --check .
```
Deberías ver que todos los archivos cumplen el formato esperado.

```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver toda la suite en verde con cobertura ≥ 80 %.

### Prueba en vivo con `curl` (cliente `app`)
Si no tienes un usuario activo en la base de datos de desarrollo, crea uno temporal desde el contenedor del backend:

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); user, created = User.objects.get_or_create(email='demo@example.com', defaults={'is_active': True}); user.is_active = True; user.set_password('DemoPass123!'); user.save()"
```
Deberías ver el comando terminar sin errores.

Inicia sesión con el cliente `app` (guardando la respuesta para copiar el campo `session_token`):

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"demo@example.com","password":"DemoPass123!","language":"es"}'
```
Deberías ver HTTP 200 con JSON que incluye `"user"`, `"terms_status"`, `"terms"` y `"session_token"`.

Usa el valor de `session_token` obtenido en el paso anterior como `<SESSION_TOKEN>` para consultar la sesión activa:

```bash
curl -s http://localhost:8000/api/app/v1/auth/session -H "X-Session-Token: <SESSION_TOKEN>"
```
Deberías ver HTTP 200 con el usuario y su estado actual de términos.

Cierra la sesión con el mismo `<SESSION_TOKEN>`:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/logout -H "X-Session-Token: <SESSION_TOKEN>"
```
Deberías ver `{"result": "logged_out"}`.

## Marco teórico
- **Por qué los endpoints viven en `/api/<cliente>/v1/auth/` junto a `/_allauth/`**: `django-allauth` headless expone sus propios contratos genéricos bajo `/_allauth/`, pensados para flujos múltiples y con respuestas propias (incluyendo enumeración de códigos o formatos por flujo). Los endpoints propios bajo `/api/browser/v1/auth/` y `/api/app/v1/auth/` actúan como fachada estricta del dominio: fijan respuestas neutras idénticas (`invalid_credentials`), aplican la puerta de términos y el límite por IP, y devuelven en una sola respuesta el estado de términos que necesita el cliente sin filtrar detalles internos ni duplicar la lógica de allauth.
