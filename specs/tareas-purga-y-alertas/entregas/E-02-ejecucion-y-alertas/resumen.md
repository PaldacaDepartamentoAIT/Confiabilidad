# Entrega E-02 · Serialización en Redis y alertas resilientes por correo

Rama: `feat/tareas-purga-y-alertas-ejecucion-y-alertas` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#148](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/148) ·
Líneas de código y tests: 314 (límite: 400).

## Qué se hizo
- **Serialización por tarea con bloqueo distribuido en Redis** (`RF-004`, `D-03`): `_task_lock` en `backend/apps/core/maintenance.py` adquiere un bloqueo bloqueante por `task_name` sobre `settings.CACHE_URL` (con `timeout=settings.MAINTENANCE_LOCK_TIMEOUT_SECONDS`), de modo que ejecuciones concurrentes de la misma tarea se ejecutan en orden sin pisarse, mientras tareas distintas corren en paralelo sin bloquearse entre sí.
- **Correo operativo en el primer fallo abierto y resiliencia** (`RF-005`, `RF-006`, `D-04`, `D-05`):
  - En fallos consecutivos de una misma tarea se registra cada nueva `MaintenanceAlert` y se actualiza `MaintenanceTaskStatus`, pero solo se envía el correo operativo cuando no existía ya una alerta abierta previa para esa tarea.
  - El correo incluye únicamente tarea, marca temporal y el resumen truncado del error (sin trazas ni secretos), mientras `logger.exception` registra la traza completa en los logs del servidor.
  - Si `MAINTENANCE_ALERT_EMAILS` está vacío, se omite el envío sin error. Si el envío SMTP falla, el error se registra en logs conservando intactos el estado y la alerta.
  - Si la base de datos no está disponible al persistir el fallo o la alerta, se capturan y registran ambas excepciones en logs y se omite el envío de correo.
- **Tests añadidos**: `backend/apps/core/tests/test_maintenance_alerts.py` cubre serialización concurrente entre hilos, independencia entre tareas distintas, supresión de correos repetidos hasta la recuperación, lista vacía de destinatarios, fallo de envío SMTP y caída de base de datos.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-004 | Serialización por tarea en Redis, logs completos y envío resiliente de correo de alerta | `cf8369b` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, en tu entorno con Docker.

Ejecuta los tests del ejecutor y alertas (sin umbral global por ser una ejecución parcial):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest --no-cov apps/core/tests/test_maintenance_runner.py apps/core/tests/test_maintenance_alerts.py
```
Deberías ver los 10 tests en verde.

Ejecuta la suite completa con cobertura y las comprobaciones de tipos, lint y formato:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest
```
```bash
docker compose -f docker/docker-compose.yml exec backend sh -c "mypy . && ruff check . && black --check ."
```
Deberías ver toda la suite en verde (cobertura ≥ 80 %) y sin errores de `mypy`, `ruff` ni `black`.

Comprueba desde consola el aviso por correo en el primer fallo abierto y la supresión en un fallo consecutivo:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from django.test import override_settings; from apps.core.maintenance import run_maintenance_task; from apps.core.models import MaintenanceAlert, MaintenanceTaskName; MaintenanceAlert.objects.all().delete(); run_with = lambda: run_maintenance_task(MaintenanceTaskName.PURGE_SECURITY_EVENTS, lambda: 0, simulate_failure=True); exec('''with override_settings(MAINTENANCE_ALERT_EMAILS=[\"ops@ejemplo.com\"]):\n for _ in range(2):\n  try: run_with()\n  except Exception: pass'''); print('open_alerts:', MaintenanceAlert.objects.filter(resolved_at__isnull=True).count())"
```
Deberías ver `open_alerts: 2` y un único correo impreso en la consola (backend de correo de desarrollo), seguido del cierre al ejecutar con éxito:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from apps.core.maintenance import run_maintenance_task; from apps.core.models import MaintenanceAlert, MaintenanceTaskName; run_maintenance_task(MaintenanceTaskName.PURGE_SECURITY_EVENTS, lambda: 0); print('open_alerts:', MaintenanceAlert.objects.filter(resolved_at__isnull=True).count())"
```
Deberías ver `open_alerts: 0`.
