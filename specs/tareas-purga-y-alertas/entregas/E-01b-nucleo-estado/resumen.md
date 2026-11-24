# Entrega E-01b · Modelos y ejecutor base de última ejecución y alertas

Rama: `feat/tareas-purga-y-alertas-nucleo-estado` · PR: pendiente ·
Líneas de código y tests: 380 (límite: 400).

## Qué se hizo
- **Modelos de seguimiento y alertas** (`RF-004`, `RF-005`): se añadieron `MaintenanceTaskName`, `MaintenanceTaskStatus` (con `task_name` único, `started_at`, `finished_at`, `status`, `deleted_count` y `error_summary` hasta 500 caracteres, sin filas iniciales antes de ejecutarse) y `MaintenanceAlert` (con `task_name`, `created_at`, `error_summary` y `resolved_at`) en `backend/apps/core/models.py`, junto con la migración `0002_maintenance_models`.
- **Ejecutor común de mantenimiento** (`RF-004`, `RF-005`, `RF-007`, `RF-009`): se implementó `run_maintenance_task` en `backend/apps/core/maintenance.py` con:
  - Registro de la última ejecución sobrescribiendo la fila única de esa tarea en `MaintenanceTaskStatus`.
  - Resumen de error normalizado y truncado a 500 caracteres (`summarize_error`) sin trazas ni secretos, mientras `logger.exception` escribe la traza completa en los logs del servidor.
  - Creación de `MaintenanceAlert` abierta en cada fallo y relanzamiento de la excepción original sin reintentos silenciosos.
  - Aborto controlado con `SimulatedMaintenanceFailure` antes de ejecutar la acción cuando `simulate_failure=True`, sin borrar datos reales.
  - Resolución automática de todas las alertas abiertas de esa tarea (`resolved_at`) cuando una ejecución posterior finaliza con éxito.
- **Tests añadidos**: `backend/apps/core/tests/test_maintenance_models.py` (unicidad, estado abierta/resuelta y migraciones sin cambios pendientes) y `backend/apps/core/tests/test_maintenance_runner.py` (sobrescritura, truncado de error, fallo simulado sin tocar la acción y resolución automática tras éxito).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-002 | Modelos `MaintenanceTaskStatus` y `MaintenanceAlert` con migración | `ca5c3da` |
| T-003 | Ejecutor base de mantenimiento con última ejecución, alerta persistente y cierre al recuperarse | `7683010` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, en tu entorno con Docker.

Aplica la migración nueva del módulo `core`:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py migrate
```
Deberías ver `Applying core.0002_maintenance_models... OK`.

Ejecuta los tests de esta entrega (sin umbral global por ser una ejecución parcial):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest --no-cov apps/core/tests/test_maintenance_models.py apps/core/tests/test_maintenance_runner.py
```
Deberías ver los 7 tests en verde.

Ejecuta la suite completa con cobertura y las comprobaciones de tipos, lint y formato:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest
```
```bash
docker compose -f docker/docker-compose.yml exec backend sh -c "mypy . && ruff check . && black --check ."
```
Deberías ver toda la suite en verde (cobertura ≥ 80 %) y sin errores de `mypy`, `ruff` ni `black`.

Prueba manualmente desde consola que `run_maintenance_task` registra un fallo simulado y luego resuelve la alerta al tener éxito:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from apps.core.maintenance import run_maintenance_task; from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus; MaintenanceAlert.objects.all().delete(); MaintenanceTaskStatus.objects.all().delete(); exec('try:\n run_maintenance_task(MaintenanceTaskName.PURGE_SECURITY_EVENTS, lambda: 0, simulate_failure=True)\nexcept Exception as exc:\n print(\"failed:\", type(exc).__name__)'); print('open:', MaintenanceAlert.objects.filter(resolved_at__isnull=True).count()); print('deleted:', run_maintenance_task(MaintenanceTaskName.PURGE_SECURITY_EVENTS, lambda: 2)); print('open_after:', MaintenanceAlert.objects.filter(resolved_at__isnull=True).count())"
```
Deberías ver `failed: SimulatedMaintenanceFailure`, `open: 1`, `deleted: 2` y `open_after: 0`.
