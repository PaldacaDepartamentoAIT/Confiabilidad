# Entrega E-02b · Cierre de otras sesiones, invalidación masiva y purga en el servicio

Rama: `feat/inicio-cierre-sesion-revocar-sesiones` · PR: pendiente · Líneas de código y tests: 212 (límite: 400).

## Qué se hizo
- Se completó el servicio `apps/accounts/sessions.py` (`T-006`):
  - `revoke_other_session(user, current_session_key, session_id, *, request=None)` (`RF-009`,
    cierre de otra sesión o de todas las demás): rechaza cerrar la sesión actual
    (`CURRENT_SESSION`) y una inexistente, caducada o de otro usuario (`NOT_FOUND`); cuando es otra
    sesión vigente de la cuenta, la elimina de `UserSession` y de la caché `sessions` y emite
    `user_logged_out` para registrar el evento `LOGOUT` en `SecurityEvent`.
  - `revoke_all_other_sessions(user, current_session_key, *, request=None)` (`RF-009`, `C-05`):
    revoca todas las demás sesiones de la cuenta emitiendo un evento `LOGOUT` por cada sesión vigente
    efectivamente cerrada, y devuelve `0` sin generar eventos cuando solo existe la sesión actual.
  - `revoke_all_user_sessions(user)` (`RF-003`, invalidación inmediata al desactivar o borrar una
    cuenta; `RF-010`, invalidación de sesiones al cambiar o restablecer la contraseña): invalida
    todas las sesiones de la cuenta en el almacén y borra sus filas de `UserSession`.
  - `purge_expired()` (`RF-021`, limpieza de sesiones caducadas; `C-01`): borra las filas de
    `UserSession` vencidas por tiempo o cuya sesión ya no existe en el almacén y devuelve el total
    eliminado.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-006 | Servicio de sesiones: cierre de otras sesiones, invalidación masiva y purga | `45a6e60` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con el entorno y los servicios levantados, actualiza las ramas remotas y
cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/inicio-cierre-sesion-revocar-sesiones
```
Ejecuta los tests del servicio de sesiones (incluye `T-005` y `T-006`):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_sessions_service.py --no-cov -v
```
Deberías ver los 7 tests en verde.

Ejecuta los análisis estáticos y la suite completa del backend:
```bash
docker compose -f docker/docker-compose.yml exec backend mypy . && docker compose -f docker/docker-compose.yml exec backend ruff check . && docker compose -f docker/docker-compose.yml exec backend black --check .
```
Deberías ver los tres análisis sin errores.
```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver la suite en verde con cobertura ≥ 80 %.
