# Entrega E-04b · Neutralidad y bloqueo por intentos fallidos en el inicio de sesión

Rama: `feat/inicio-cierre-sesion-neutralidad` · PR: pendiente · Líneas de código y tests: 122 (límite: 400).

## Qué se hizo
- Se corrigió la llamada a `adapter.pre_login` en `apps/accounts/api/auth_views.py` para pasar los argumentos por nombre obligatorios de `DefaultAccountAdapter.pre_login` cuando la cuenta está inactiva.
- Se añadieron los tests de integración `apps/accounts/tests/test_auth_neutrality.py` para `POST /api/browser/v1/auth/login` y `POST /api/app/v1/auth/login` (`T-011`, `RF-002`, `RF-004`, `CF-2`, `CF-6`):
  - Verifican que correo inexistente, contraseña incorrecta en cuenta activa, cuenta inactiva con contraseña incorrecta y cuenta inactiva con contraseña correcta devuelven exactamente el mismo código HTTP (`400`), cuerpo (`invalid_credentials`), cabeceras y cookies en los intentos 1 a 5.
  - Verifican que los cuatro casos alcanzan el mismo bloqueo (`400 too_many_login_attempts`) en el 6.º intento y no dejan filas en `UserSession`.
  - Verifican que la cuenta inactiva con contraseña correcta registra `SecurityEvent(event_type="login", success=False, metadata={"reason": "inactive_account"})` en los 5 intentos previos y `SecurityEvent(event_type="lockout", success=False, metadata={"reason": "too_many_login_attempts"})` en el 6.º.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-011 | Test de neutralidad y bloqueo en el inicio de sesión | `d04eb10` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con el entorno y los servicios levantados, actualiza las ramas remotas y cambia a la rama de la entrega:

```bash
git fetch origin
```

```bash
git checkout feat/inicio-cierre-sesion-neutralidad
```
Deberías ver tu copia de trabajo en la rama `feat/inicio-cierre-sesion-neutralidad`.

Ejecuta los tests de neutralidad y autenticación:

```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_auth_neutrality.py apps/accounts/tests/test_auth_api.py --no-cov -v
```
Deberías ver todos los tests de neutralidad y autenticación en verde.

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

### Comprobación rápida con `curl`
Lanza 6 intentos fallidos seguidos sobre un correo inexistente (cada petición devuelve la respuesta JSON):

```bash
for i in 1 2 3 4 5 6; do curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"inexistente@example.com","password":"wrong","language":"es"}'; echo ""; done
```
Deberías ver cinco respuestas idénticas con `"code":"invalid_credentials"` y en la sexta `"code":"too_many_login_attempts"`.
