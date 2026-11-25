# Resumen: tareas-purga-y-alertas

Estado: cerrada con riesgo residual aceptado (2026-11-25).

## Qué se hizo
- **Programación configurable de las tres purgas (`RF-001`, `RF-002`, `RF-003`)**:
  - Se añadieron en `backend/config/settings.py` (y se documentaron en `backend/.env.example`) las variables `PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS` (`3600`), `PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS` (`3600`), `PURGE_SECURITY_EVENTS_INTERVAL_SECONDS` (`86400`), `MAINTENANCE_ALERT_EMAILS` y `MAINTENANCE_LOCK_TIMEOUT_SECONDS` (`3600`).
  - Se registraron las tres tareas en `CELERY_BEAT_SCHEDULE` (`apps.accounts.tasks.purge_stale_registrations`, `apps.accounts.tasks.purge_expired_sessions` y la nueva `apps.audit.tasks.purge_security_events`) para su sincronización mediante `DatabaseScheduler`.
  - `apps.audit.tasks.purge_security_events` ejecuta `call_command("purge_security_events")` respetando el corte de un año y la protección de solo inserción de auditoría (`test_purge_access.py`).
- **Modelos y ejecutor común de mantenimiento (`RF-004`, `RF-005`, `RF-006`, `RF-007`)**:
  - Se crearon `MaintenanceTaskStatus` (una única fila por tarea, ausente antes de su primera ejecución) y `MaintenanceAlert` (abiertas con `resolved_at=None` o resueltas) en `backend/apps/core/models.py` con la migración `0002_maintenance_models`.
  - Se implementó `run_maintenance_task` en `backend/apps/core/maintenance.py` con bloqueo distribuido en Redis por tarea (`_task_lock`), sobrescritura de última ejecución, resumen truncado de error a 500 caracteres sin trazas ni secretos, traza completa vía `logger.exception`, creación de alerta persistente y envío de correo operativo solo en el primer fallo mientras la alerta siga abierta, resiliencia ante fallos SMTP o lista vacía de destinatarios, registro exclusivo en logs si falla la base de datos y cierre automático de alertas abiertas al recuperarse la tarea.
- **Panel interno de administración (`RF-008`)**:
  - Se registraron `MaintenanceTaskStatusAdmin` y `MaintenanceAlertAdmin` en `backend/apps/core/admin.py` en modo solo lectura para operadores autorizados (`view_maintenancetaskstatus` / `view_maintenancealert` o superusuarios), con filtros por tarea, resultado y estado (`open` / `resolved`).
- **Comando CLI y simulación de fallo (`RF-008`, `RF-009`)**:
  - Se implementó `python manage.py maintenance_tasks` en `backend/apps/core/management/commands/maintenance_tasks.py` con los subcomandos `status` (`--open-only`), `run <tarea|--all>` (`--async`) y `simulate-failure <tarea>` (`--wait`), provocando `SimulatedMaintenanceFailure` en el trabajador Celery antes de borrar registros reales.
- **Entregas integradas en `feat/tareas-purga-y-alertas`**:
  - `E-01` (`PR #146`), `E-01b` (`PR #147`), `E-02` (`PR #148`), `E-02b` (`PR #149`) y `E-03` (`PR #150`).

## Cómo probarlo
Desde la raíz del repositorio, en tu entorno con Docker:

1. Levanta únicamente `db` y `redis` (si `worker` está encendido puede interferir con dos tests antiguos de Celery que usan la cola por defecto) y ejecuta los tests de la feature y la suite completa:
```bash
docker compose -f docker/docker-compose.yml stop worker beat
```
```bash
docker compose -f docker/docker-compose.yml up -d db redis backend
```
```bash
docker compose -f docker/docker-compose.yml exec -T backend pytest --no-cov apps/audit/tests/test_purge_task.py apps/audit/tests/test_purge_access.py apps/core/tests/test_maintenance_models.py apps/core/tests/test_maintenance_runner.py apps/core/tests/test_maintenance_alerts.py apps/core/tests/test_maintenance_tasks.py apps/core/tests/test_maintenance_admin.py apps/core/tests/test_maintenance_command.py apps/core/tests/test_maintenance_worker_e2e.py apps/accounts/tests/test_registration_background.py apps/accounts/tests/test_purge_expired_sessions.py
```
Deberías ver todos los tests de la feature en verde.

```bash
docker compose -f docker/docker-compose.yml exec -T backend pytest
```
Deberías ver toda la suite de backend en verde con cobertura ≥ 80 %.

2. Comprueba tipos, lint y formato en el backend:
```bash
docker compose -f docker/docker-compose.yml exec -T backend sh -c "mypy . && ruff check . && black --check ."
```
Deberías ver `Success: no issues found`, `All checks passed!` y cero archivos por reformatear.

3. Levanta `worker` y `beat` y prueba el flujo CLI completo de estado, fallo simulado sin borrado y recuperación:
```bash
docker compose -f docker/docker-compose.yml up -d backend worker beat
```
```bash
docker compose -f docker/docker-compose.yml exec -T backend python manage.py maintenance_tasks status
```
```bash
docker compose -f docker/docker-compose.yml exec -T backend python manage.py maintenance_tasks simulate-failure purge_security_events --wait 15
```
```bash
docker compose -f docker/docker-compose.yml exec -T backend python manage.py maintenance_tasks status
```
Deberías ver `simulated failure observed for purge_security_events`, el estado en `status=failure` y una alerta con `state=open` (y la traza completa en los logs de `worker`).

```bash
docker compose -f docker/docker-compose.yml exec -T backend python manage.py maintenance_tasks run --all
```
```bash
docker compose -f docker/docker-compose.yml exec -T backend python manage.py maintenance_tasks status
```
Deberías ver las tres tareas en `status=success` y la alerta anterior con `state=resolved`.

4. Para verificar el disparo autónomo de `beat` + `worker` con intervalos cortos (10 segundos) sin esperar una hora ni un día:
```bash
PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS=10 PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS=10 PURGE_SECURITY_EVENTS_INTERVAL_SECONDS=10 docker compose -f docker/docker-compose.yml up -d --force-recreate beat worker
```
Espera ~15 segundos y consulta el estado:
```bash
docker compose -f docker/docker-compose.yml exec -T backend python manage.py maintenance_tasks status
```
Deberías ver `finished_at` actualizado automáticamente en las tres tareas. Después restablece los intervalos estándar:
```bash
docker compose -f docker/docker-compose.yml up -d --force-recreate beat worker
```
Deberías ver `beat` y `worker` de nuevo con los intervalos por defecto (`3600` s y `86400` s).

5. En el navegador, entra al panel `/admin/core/maintenancetaskstatus/` y `/admin/core/maintenancealert/` con un superusuario o un usuario `is_staff` con permisos de lectura en `core` para revisar últimas ejecuciones y filtrar alertas abiertas o resueltas (sin botones de alta, edición ni borrado).

## Riesgo residual aceptado
La validación estricta (`2026-11-25`) dejó **8 de 9** requisitos cumplidos y el usuario aceptó cerrar la feature con este riesgo residual mínimo (origen *Test*):
1. **`RF-005` — Verificación de traza completa en logs de fallo**: los tests `test_run_records_truncated_failure_creates_alert_and_reraises` (`backend/apps/core/tests/test_maintenance_runner.py`) y `test_database_error_during_failure_recording_logs_only_and_skips_email` (`backend/apps/core/tests/test_maintenance_alerts.py`) comprueban `rec.message` en `caplog.records`, sin asertar explícitamente `rec.exc_info is not None` ni `"Traceback" in caplog.text`. La implementación en `backend/apps/core/maintenance.py` sí utiliza `logger.exception(...)`, por lo que en ejecución real emite la traza completa; el único riesgo es que un cambio futuro sustituya `logger.exception` por `logger.error` sin que estos dos tests lo detecten (impacto bajo, probabilidad baja).
2. **Observaciones operativas durante la validación**:
   - Si se ejecuta la suite completa de `pytest` mientras el contenedor `worker` de desarrollo está levantado, 2 tests preexistentes ajenos a esta feature (`apps/core/tests/test_task_worker.py` y `apps/emails/tests/test_worker.py`) pueden fallar porque el `worker` vivo consume tareas de la cola por defecto `celery`; con solo `db` y `redis` levantados no ocurre.
   - El disparo periódico autónomo en bucle de `beat` + `worker` con intervalos cortos se valida en vivo con el entorno Docker (paso 4 de «Cómo probarlo») y en `pytest` mediante `DatabaseScheduler` + `start_worker`.

## Marco teórico
- **Bloqueo distribuido en Redis frente a bloqueo en base de datos**: las tareas periódicas pueden dispararse desde varios procesos worker o coincidir con una ejecución manual desde CLI. Un bloqueo en Redis por nombre de tarea serializa las ejecuciones de esa misma tarea entre procesos distintos sin bloquear a las otras dos tareas y sigue funcionando aunque la base de datos esté caída.
- **Envío directo de correo de alerta fuera del outbox**: normalmente los correos transaccionales pasan por la cola en base de datos (`OutboundEmail`). Sin embargo, si el fallo operativo ocurre precisamente por saturación de cola o incidencias de mantenimiento, el aviso operativo se envía de forma inmediata con `EmailMessage` dentro de un `try/except` para no depender del ciclo de `dispatch_due`.
- **Supresión de correos repetidos mientras existe alerta abierta**: ante un fallo persistente (por ejemplo, en una tarea horaria), crear una alerta por cada fallo conserva la trazabilidad de cuántas veces falló, mientras que enviar correo solo al abrirse el incidente evita inundar el buzón operativo hasta que la tarea se recupere y cierre sus alertas abiertas.
- **Simulación de fallo en el trabajador real sin borrar datos**: probar una alerta llamando solo a una función local no comprueba el broker Redis ni la serialización Celery. El comando `simulate-failure` encola la tarea con `simulate_failure=True` para que recorra Redis y el trabajador real, falle antes de ejecutar la purga y dispare el flujo completo de estado, alerta, log y correo sin riesgo para los datos.
- **Aislamiento de colas en pruebas E2E de Celery**: cuando se ejecuta un worker de pruebas (`start_worker`) contra el mismo Redis que usa un servicio `worker` de desarrollo ya levantado, ambos compiten por la cola por defecto `celery`. Usar una cola dedicada en el worker de pruebas (`test-maintenance`) garantiza que las tareas de prueba lleguen al proceso conectado a la base de datos de test.
