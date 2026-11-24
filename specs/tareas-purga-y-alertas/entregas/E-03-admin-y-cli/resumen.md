# Entrega E-03 · Panel de administración, comando CLI y verificación E2E

Rama: `feat/tareas-purga-y-alertas-admin-y-cli` · PR: pendiente ·
Líneas de código y tests: 397 (límite: 400).

## Qué se hizo
- **Panel de administración interno de solo lectura** (`RF-008`): se registró en `backend/apps/core/admin.py` el visor de `MaintenanceTaskStatus` (filtrado por tarea y resultado) y de `MaintenanceAlert` (con `AlertStateFilter` para filtrar abiertas o resueltas), deshabilitando alta, edición y borrado para preservar la integridad operativa.
- **Comando CLI `maintenance_tasks`** (`RF-008`, `RF-009`): se implementó `backend/apps/core/management/commands/maintenance_tasks.py` con:
  - `status` (y `--open-only`): muestra la última ejecución de las tres tareas (indicando `no executions recorded` antes de la primera corrida) y las alertas.
  - `run <tarea|--all>` (con `--async` opcional): ejecuta manualmente una o las tres tareas.
  - `simulate-failure <tarea>` (con `--wait <segundos>` opcional): encola la tarea en modo de fallo simulado en el trabajador Celery real sin borrar datos reales.
- **Documentación de variables** (`RF-002`): se añadieron a `backend/.env.example` las variables `PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS`, `PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS`, `PURGE_SECURITY_EVENTS_INTERVAL_SECONDS`, `MAINTENANCE_ALERT_EMAILS` y `MAINTENANCE_LOCK_TIMEOUT_SECONDS`.
- **Tests añadidos**: `test_maintenance_admin.py`, `test_maintenance_command.py` y `test_maintenance_worker_e2e.py` (con el fixture `celery_worker` real sobre Redis para las tres tareas).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-006 | Panel de administración interno de solo lectura para estado y alertas | `9058ce8` |
| T-007 | Comando CLI `maintenance_tasks` y documentación de variables en `.env.example` | `013c1e9`, `201d417` |
| T-008 | Pruebas end-to-end con trabajador Celery real sobre Redis | `10de910` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, en tu entorno con Docker.

Ejecuta los tests de esta entrega (sin umbral global por ser una ejecución parcial) y después la suite completa con cobertura y análisis estático:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest --no-cov apps/core/tests/test_maintenance_admin.py apps/core/tests/test_maintenance_command.py apps/core/tests/test_maintenance_worker_e2e.py
```
```bash
docker compose -f docker/docker-compose.yml exec backend pytest
```
```bash
docker compose -f docker/docker-compose.yml exec backend sh -c "mypy . && ruff check . && black --check ."
```
Deberías ver todos los tests de la entrega y la suite completa en verde (cobertura ≥ 80 %), sin errores de `mypy`, `ruff` ni `black`.

Reinicia `backend`, `worker` y `beat` para que carguen el código actualizado:
```bash
docker compose -f docker/docker-compose.yml restart backend worker beat
```
Deberías ver los tres servicios reiniciados.

Consulta el estado actual desde consola, provoca un fallo simulado en el trabajador real esperando su resultado y vuelve a consultar:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py maintenance_tasks status
```
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py maintenance_tasks simulate-failure purge_security_events --wait 15
```
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py maintenance_tasks status
```
Deberías ver `simulated failure observed for purge_security_events`, el estado actualizado a `failure` y una alerta `state=open` (además del correo impreso en la consola de `worker` si configuraste `MAINTENANCE_ALERT_EMAILS`).

Ejecuta manualmente las tres tareas para recuperar el estado y cerrar alertas abiertas:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py maintenance_tasks run --all
```
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py maintenance_tasks status
```
Deberías ver las tres tareas en `status=success` y la alerta anterior en `state=resolved`.

Para comprobar que las tres tareas corren solas sin esperar una hora ni un día, levanta `beat` y `worker` con intervalos de 10 segundos y espera ~15 segundos mirando `status` o los logs de `worker`:
```bash
PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS=10 PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS=10 PURGE_SECURITY_EVENTS_INTERVAL_SECONDS=10 docker compose -f docker/docker-compose.yml up -d --force-recreate beat worker
```
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py maintenance_tasks status
```
Deberías ver `finished_at` actualizado automáticamente para `purge_stale_registrations`, `purge_expired_sessions` y `purge_security_events`. Al terminar la prueba, restablece los intervalos por defecto:
```bash
docker compose -f docker/docker-compose.yml up -d --force-recreate beat worker
```
Deberías ver `beat` y `worker` de nuevo con la configuración estándar (`3600` s y `86400` s).

También puedes abrir `/admin/core/maintenancetaskstatus/` y `/admin/core/maintenancealert/` en el panel de administración (como superusuario o usuario `is_staff` con permisos de lectura en `core`) para consultar el estado y filtrar alertas abiertas o resueltas.
