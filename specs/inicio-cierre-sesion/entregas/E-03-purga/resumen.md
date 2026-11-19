# Entrega E-03 · Ciclo de vida automático de sesiones y orden de purga en consola

Rama: `feat/inicio-cierre-sesion-purga` · PR: pendiente · Líneas de código y tests: 248 (límite: 400).

## Qué se hizo
- Se conectó el ciclo de vida automático de `UserSession` en `apps/accounts/models.py` (`T-007`):
  - `user_logged_in` y `user_logged_out` crean y borran la fila de `UserSession` (y su sesión en
    caché) cuando se inicia o cierra sesión mediante las señales estándar de Django (`RF-006`,
    `RF-007`).
  - `User.save()` y `pre_delete` sobre `User` invalidan todas las sesiones de la cuenta en el
    almacén de sesiones y vacían sus filas en `UserSession` cuando la cuenta se desactiva
    (`is_active=False`), cambia su contraseña o se borra físicamente (`RF-003`, `RF-010`, `C-03`).
  - El receptor de `password_reset_completed` refuerza la invalidación al completarse un
    restablecimiento de contraseña (`RF-010`).
- Se implementaron el comando de consola `manage.py purge_expired_sessions` y la tarea periódica
  `apps.accounts.tasks.purge_expired_sessions` en `CELERY_BEAT_SCHEDULE` cada 3600 segundos (`T-008`,
  `RF-021`).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-007 | Sincronización automática de sesiones al entrar, salir, desactivar, borrar o cambiar contraseña | `8f7ac80` |
| T-008 | Limpieza de sesiones caducadas por consola y tarea periódica | `d0f592f` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con el entorno y los servicios levantados, actualiza las ramas remotas y
cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/inicio-cierre-sesion-purga
```
Ejecuta los tests nuevos de esta entrega:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_sessions_lifecycle.py apps/accounts/tests/test_purge_expired_sessions.py --no-cov -v
```
Deberías ver los 5 tests en verde.

Prueba la orden de consola en vivo (muestra el conteo de sesiones caducadas eliminadas):
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py purge_expired_sessions
```
Deberías ver `<N> expired user sessions deleted.`.

Ejecuta los análisis estáticos y la suite completa del backend:
```bash
docker compose -f docker/docker-compose.yml exec backend mypy . && docker compose -f docker/docker-compose.yml exec backend ruff check . && docker compose -f docker/docker-compose.yml exec backend black --check .
```
Deberías ver los tres análisis sin errores.
```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver toda la suite en verde con cobertura ≥ 80 %.
