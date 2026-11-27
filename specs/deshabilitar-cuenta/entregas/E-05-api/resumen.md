# Entrega E-05 · Endpoints HTTP de perfil ampliado, baja de cuenta y login de cuentas deshabilitadas

Rama: `feat/deshabilitar-cuenta-api` · PR: pendiente · Líneas de código y tests: 448 (límite excepcional: 500).

## Qué se hizo
- En [profile_views.py](../../../../backend/apps/accounts/api/profile_views.py), [profile_serializers.py](../../../../backend/apps/accounts/api/profile_serializers.py) y [messages.py](../../../../backend/apps/accounts/api/messages.py) se ampliaron `GET` y `PATCH` de `auth/profile` con `can_disable`, `disable_block_reason` (`"owns_company"`, `"last_superuser"` o `null`) y `disable_retry_after`, se añadió `AccountDisableSerializer` y se añadieron los textos localizados en `es`, `pt-BR` y `en` para `owns_company`, `last_superuser`, `account_disabled` y `account_disabled_expired` (`RF-003`, `RF-004`, `RF-005`, `RF-014`, `RF-016`).
- En [profile_views.py](../../../../backend/apps/accounts/api/profile_views.py) y [urls.py](../../../../backend/apps/accounts/api/urls.py) se expusieron `POST /api/browser/v1/auth/account/disable` (sesión por cookie + CSRF) y `POST /api/app/v1/auth/account/disable` (`X-Session-Token`), protegidos por `_require_auth(..., require_terms=True)`, respetando la prioridad empresa → último superusuario → bloqueo temporal (`429` con `Retry-After`) → contraseña actual, y revocando de inmediato todas las sesiones activas al completarse (`RF-001`, `RF-006`, `RF-007`, `RF-013`, `RF-015`).
- En [auth_views.py](../../../../backend/apps/accounts/api/auth_views.py) se ajustó `AppLoginView._authenticate` para que, cuando las credenciales correspondan a una cuenta inactiva, sume al límite de intentos y registre auditoría `inactive_account` devolviendo `account_disabled` (dentro de 12 meses, con `EMAIL_SUPPORT_ADDRESS`) o `account_disabled_expired` (plazo vencido), conservando `invalid_credentials` neutro en cualquier otro caso (`RF-008`).
- En [test_disable_api.py](../../../../backend/apps/accounts/tests/test_disable_api.py), [test_profile_api.py](../../../../backend/apps/accounts/tests/test_profile_api.py) y [test_auth_neutrality.py](../../../../backend/apps/accounts/tests/test_auth_neutrality.py) se cubrieron los contratos de perfil, baja, revocación inmediata, límites y respuestas de login.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [tasks.md](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-009 | Extensión de `GET auth/profile` con estado de baja, serializador y mensajes multiidioma | `1f6cc47` |
| T-010 | Endpoints `POST auth/account/disable` (web y escritorio) y rechazo informativo en login | `18a755b` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con Docker, PostgreSQL y Redis levantados, actualiza las ramas remotas y cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/deshabilitar-cuenta-api
```
Ejecuta los tests de esta entrega y los relacionados de perfil y autenticación (sin medir cobertura global):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_disable_api.py apps/accounts/tests/test_profile_api.py apps/accounts/tests/test_auth_neutrality.py apps/accounts/tests/test_registration_api_messages.py -v --no-cov
```
Deberías ver todos los tests de API de baja, perfil, mensajes y login en verde.

Ejecuta la suite completa, el comprobador de tipos, el linter y el formateador:
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

Para probar el flujo completo por HTTP con `curl` usando `<EMAIL>` y `<PASSWORD>` de una cuenta activa con términos aceptados (sustituye `<SESSION_TOKEN>` por el valor `session_token` devuelto al iniciar sesión):
```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"<EMAIL>","password":"<PASSWORD>","language":"es"}'
```
Deberías ver un JSON con `session_token`. Consulta su estado en el perfil:
```bash
curl -s http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <SESSION_TOKEN>"
```
Deberías ver `"can_disable": true` (o `"owns_company"` si posee una empresa). Deshabilita la cuenta:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/account/disable -H "Content-Type: application/json" -H "X-Session-Token: <SESSION_TOKEN>" -d '{"current_password":"<PASSWORD>","language":"es"}'
```
Deberías ver `{"result":"account_disabled"}`. Comprueba la revocación inmediata y el rechazo informativo en el login:
```bash
curl -i -s http://localhost:8000/api/app/v1/auth/session -H "X-Session-Token: <SESSION_TOKEN>"
```
Deberías ver código HTTP `401`.
```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"<EMAIL>","password":"<PASSWORD>","language":"es"}'
```
Deberías ver `code: "account_disabled"` con las indicaciones para contactar a soporte.

## Marco teórico
### Rechazo específico con credenciales válidas frente a neutralidad en errores (`RF-008`)
En un login tradicional anti-enumeración, cualquier fallo devuelve el mismo mensaje genérico. Aquí se mantiene esa neutralidad cuando el correo no existe o la contraseña falla, y únicamente cuando el usuario demuestra conocer la contraseña real de una cuenta deshabilitada se le informa del estado de baja y del plazo de 12 meses con soporte (siguiendo el mismo límite de intentos fallidos y auditoría para evitar abuso).
