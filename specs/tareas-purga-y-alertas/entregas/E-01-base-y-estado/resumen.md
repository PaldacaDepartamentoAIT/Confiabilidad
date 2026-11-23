# Entrega E-01 · Programación configurable y tarea periódica de auditoría

Rama: `feat/tareas-purga-y-alertas-base-y-estado` · PR: pendiente ·
Líneas de código y tests: 166 (límite: 400).

## Qué se hizo
- **Variables configurables de intervalo, destinatarios y bloqueo** (`RF-002`): se añadieron en `backend/config/settings.py` las variables `PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS` (por defecto `3600.0`), `PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS` (por defecto `3600.0`), `PURGE_SECURITY_EVENTS_INTERVAL_SECONDS` (por defecto `86400.0`), `MAINTENANCE_ALERT_EMAILS` (por defecto vacía) y `MAINTENANCE_LOCK_TIMEOUT_SECONDS` (por defecto `3600`).
- **Programación de las tres purgas en Celery Beat** (`RF-001`, `RF-002`): `CELERY_BEAT_SCHEDULE` ahora usa esos intervalos configurables e incorpora `"audit-purge-security-events"` apuntando a `apps.audit.tasks.purge_security_events`.
- **Tarea periódica de depuración de auditoría** (`RF-001`, `RF-003`): se creó `apps.audit.tasks.purge_security_events` en `backend/apps/audit/tasks.py`, que ejecuta el comando autorizado `manage.py purge_security_events` y devuelve el número de eventos eliminados, preservando las reglas de retención de un año y el aislamiento de acceso solo-inserción verificado por `test_purge_access.py`.
- **Tests añadidos**: `backend/apps/audit/tests/test_purge_task.py` cubre la purga de eventos mayores a un año desde la tarea Celery, los intervalos por defecto en `CELERY_BEAT_SCHEDULE`, la sincronización en `PeriodicTask` con `DatabaseScheduler` y la sobrescritura por variables de entorno.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Programación configurable de las tres purgas y tarea periódica de auditoría | `0354306` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, en tu entorno con Docker y las dependencias instaladas.

Levanta los servicios base y aplica migraciones:
```bash
docker compose -f docker/docker-compose.yml up -d db redis backend worker beat
```
Deberías ver los servicios en marcha.

Ejecuta los tests de la entrega (incluida la guarda de acceso de auditoría):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/audit/tests/test_purge_task.py apps/audit/tests/test_purge_access.py
```
Deberías ver todos los tests de ambos archivos en verde.

Comprueba tipos, lint y formato en el backend:
```bash
docker compose -f docker/docker-compose.yml exec backend sh -c "mypy . && ruff check . && black --check ."
```
Deberías ver la salida limpia sin errores.

Dispara manualmente la nueva tarea periódica de auditoría a través del trabajador Celery:
```bash
docker compose -f docker/docker-compose.yml exec backend celery -A config call apps.audit.tasks.purge_security_events
```
Deberías ver el identificador de la tarea encolada y en los logs del servicio `worker` la ejecución completada con el conteo de eventos eliminados.

Comprueba que `DatabaseScheduler` registró las tres tareas periódicas en la base de datos:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from django_celery_beat.models import PeriodicTask; print(list(PeriodicTask.objects.filter(name__in=['accounts-purge-stale-registrations','accounts-purge-expired-sessions','audit-purge-security-events']).values_list('name','task','enabled')))"
```
Deberías ver las tres tuplas con `enabled=True`.

## Marco teórico
### Por qué la tarea periódica de auditoría llama al comando en lugar de importar la función interna de borrado
`SecurityEvent` es una tabla de solo inserción (`InsertOnlyError` bloquea `update()` y `delete()` en cualquier uso normal del ORM). Para evitar que otra parte del código o el panel de administración borre eventos de auditoría por error, `test_purge_access.py` analiza el árbol sintáctico de todo el backend y prohíbe importar `purge_expired` o `_purge_allowed` fuera del modelo y del comando `purge_security_events`. Al invocar `call_command("purge_security_events")` desde `apps.audit.tasks.purge_security_events`, la tarea periódica reutiliza esa única puerta autorizada sin debilitar la garantía de seguridad ya existente.
