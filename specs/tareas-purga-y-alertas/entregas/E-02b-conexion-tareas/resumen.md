# Entrega E-02b · Conexión de las tres tareas periódicas al ejecutor

Rama: `feat/tareas-purga-y-alertas-conexion-tareas` · PR: pendiente ·
Líneas de código y tests: 144 (límite: 400).

## Qué se hizo
- **Conexión de las tres purgas a `run_maintenance_task`** (`RF-001`, `RF-003`, `RF-004`, `RF-005`, `RF-007`, `RF-009`):
  - `apps.accounts.tasks.purge_stale_registrations` y `apps.accounts.tasks.purge_expired_sessions` en `backend/apps/accounts/tasks.py` delegan ahora en `run_maintenance_task` aceptando `simulate_failure: bool = False`.
  - `apps.audit.tasks.purge_security_events` en `backend/apps/audit/tasks.py` envuelve `_run_audit_purge` en `run_maintenance_task` aceptando `simulate_failure: bool = False` y manteniendo intacto `test_purge_access.py`.
- **Tests añadidos**: `backend/apps/core/tests/test_maintenance_tasks.py` comprueba de forma parametrizada para las tres tareas que el fallo simulado (`simulate_failure=True`) aborta antes de eliminar registros reales, actualiza `MaintenanceTaskStatus`, abre una `MaintenanceAlert`, envía el correo de alerta, y que una ejecución normal posterior elimina el registro vencido y resuelve la alerta; además cubre el caso de salida vacía del comando de auditoría.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-005 | Conexión de las tres tareas periódicas al ejecutor de mantenimiento | `4c6b836` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, en tu entorno con Docker.

Ejecuta los tests de esta entrega y las suites relacionadas (sin umbral global por ser una ejecución parcial):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest --no-cov apps/core/tests/test_maintenance_tasks.py apps/accounts/tests/test_registration_background.py apps/accounts/tests/test_purge_expired_sessions.py apps/audit/tests/test_purge_access.py
```
Deberías ver todos los tests en verde.

Ejecuta la suite completa con cobertura y las comprobaciones de tipos, lint y formato:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest
```
```bash
docker compose -f docker/docker-compose.yml exec backend sh -c "mypy . && ruff check . && black --check ."
```
Deberías ver toda la suite en verde (cobertura ≥ 80 %) y sin errores de `mypy`, `ruff` ni `black`.

Reinicia el trabajador y el planificador si ya estaban arrancados para que carguen el código actualizado:
```bash
docker compose -f docker/docker-compose.yml restart worker beat
```
Deberías ver ambos servicios reiniciados.

Prueba desde Celery a disparar cualquiera de las tres tareas en modo fallo simulado (guarda el identificador que imprime como `<TASK_ID>`):
```bash
docker compose -f docker/docker-compose.yml exec backend celery -A config call apps.audit.tasks.purge_security_events --kwargs='{"simulate_failure": true}'
```
Deberías ver un UUID de tarea.

Comprueba el resultado de la tarea, los logs del worker y el estado abierto en base de datos:
```bash
docker compose -f docker/docker-compose.yml exec backend celery -A config result <TASK_ID>
```
```bash
docker compose -f docker/docker-compose.yml logs --tail=80 worker
```
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from apps.core.models import MaintenanceAlert, MaintenanceTaskStatus; print('STATUS:', list(MaintenanceTaskStatus.objects.values('task_name', 'status', 'deleted_count', 'error_summary', 'finished_at'))); print('ALERTS:', list(MaintenanceAlert.objects.values('task_name', 'created_at', 'resolved_at', 'error_summary')))"
```
Deberías ver `SimulatedMaintenanceFailure` en el resultado, la traza completa en los logs del worker, `status='failure'` en `MaintenanceTaskStatus` y una alerta con `resolved_at=None` en `MaintenanceAlert`.

Ahora lanza la misma tarea en modo normal y vuelve a consultar el estado en base de datos:
```bash
docker compose -f docker/docker-compose.yml exec backend celery -A config call apps.audit.tasks.purge_security_events
```
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from apps.core.models import MaintenanceAlert, MaintenanceTaskStatus; print('STATUS:', list(MaintenanceTaskStatus.objects.values('task_name', 'status', 'deleted_count', 'error_summary', 'finished_at'))); print('ALERTS:', list(MaintenanceAlert.objects.values('task_name', 'created_at', 'resolved_at', 'error_summary')))"
```
Deberías ver `status='success'` y la alerta anterior marcada con `resolved_at` relleno.
