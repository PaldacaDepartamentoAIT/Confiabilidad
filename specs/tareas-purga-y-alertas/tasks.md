# Tareas: tareas-purga-y-alertas
Estado: aprobado

- [x] T-001 Programación configurable de las tres purgas y tarea periódica de auditoría
  RF: RF-001, RF-002, RF-003 | Depende de: — | Archivos: 3 (`backend/config/settings.py`, `backend/apps/audit/tasks.py`, `backend/apps/audit/tests/test_purge_task.py`)
  Hecho cuando: `pytest apps/audit/tests/test_purge_task.py apps/audit/tests/test_purge_access.py` pasa: `CELERY_BEAT_SCHEDULE` incluye las tres tareas con intervalos configurables por entorno (`3600`, `3600`, `86400`), `DatabaseScheduler.setup_schedule()` registra los tres `PeriodicTask`, `apps.audit.tasks.purge_security_events` ejecuta `call_command("purge_security_events")` respetando el corte de un año y `test_purge_access.py` sigue en verde.
  Decisiones: `apps.audit.tasks.purge_security_events` extrae el conteo desde el primer token de la salida estándar de `manage.py purge_security_events` y falla explícitamente con `RuntimeError` si la salida llega vacía. Confianza: [Cierto]. Cómo revertirla: exponer una función auxiliar pública en el propio comando `purge_security_events.py` que devuelva el entero directamente.

- [x] T-002 Modelos `MaintenanceTaskStatus` y `MaintenanceAlert` con migración
  RF: RF-004, RF-005 | Depende de: — | Archivos: 3 (`backend/apps/core/models.py`, `backend/apps/core/migrations/0002_maintenance_models.py`, `backend/apps/core/tests/test_maintenance_models.py`)
  Hecho cuando: `pytest apps/core/tests/test_maintenance_models.py` pasa: `MaintenanceTaskStatus` exige unicidad por `task_name` (sin filas iniciales antes de ejecutarse), `MaintenanceAlert` distingue abiertas (`resolved_at=None`) de resueltas y la migración aplica limpia.
  Decisiones: se define longitud máxima de 500 caracteres para `error_summary` en ambos modelos (en línea con `D-05` del plan). Confianza: [Cierto]. Cómo revertirla: ajustar `max_length` con una nueva migración.

- [x] T-003 Ejecutor base de mantenimiento con última ejecución, alerta persistente y cierre al recuperarse
  RF: RF-004, RF-005, RF-007, RF-009 | Depende de: T-002 | Archivos: 2 (`backend/apps/core/maintenance.py`, `backend/apps/core/tests/test_maintenance_runner.py`)
  Hecho cuando: `pytest apps/core/tests/test_maintenance_runner.py` pasa: `run_maintenance_task` actualiza sobrescribiendo `MaintenanceTaskStatus` en éxito/fallo, aborta antes de ejecutar la acción cuando `simulate_failure=True`, crea `MaintenanceAlert` con resumen truncado al fallar, relanza la excepción sin reintentos silenciosos y marca resueltas las alertas abiertas de la tarea cuando la siguiente ejecución tiene éxito.
  Decisiones: el resumen de error normaliza saltos de línea/espacios en `TipoExcepcion: mensaje` y trunca a 500 caracteres con `...`, definiendo `SimulatedMaintenanceFailure` para distinguir fallos simulados de errores reales. Confianza: [Cierto]. Cómo revertirla: usar `RuntimeError` directo o ajustar `MAX_ERROR_SUMMARY_LENGTH`.

- [ ] T-004 Serialización por tarea en Redis, logs completos y envío resiliente de correo de alerta
  RF: RF-004, RF-005, RF-006 | Depende de: T-001, T-003 | Archivos: 2 (`backend/apps/core/maintenance.py`, `backend/apps/core/tests/test_maintenance_alerts.py`)
  Hecho cuando: `pytest apps/core/tests/test_maintenance_alerts.py` pasa: dos ejecuciones concurrentes de la misma tarea se serializan en orden con el bloqueo Redis sin bloquear otras tareas; los fallos emiten `logger.exception` con traza completa; el correo operativo se envía solo si no había alerta abierta previa para esa tarea y `MAINTENANCE_ALERT_EMAILS` no está vacío; los fallos de envío SMTP se registran en logs conservando estado y alerta; y si falla la BD al persistir, se registran ambos errores en logs sin intentar enviar correo.

- [ ] T-005 Conexión de las tres tareas periódicas al ejecutor de mantenimiento
  RF: RF-001, RF-003, RF-004, RF-005, RF-007, RF-009 | Depende de: T-001, T-004 | Archivos: 3 (`backend/apps/accounts/tasks.py`, `backend/apps/audit/tasks.py`, `backend/apps/core/tests/test_maintenance_tasks.py`)
  Hecho cuando: `pytest apps/core/tests/test_maintenance_tasks.py apps/accounts/tests/test_registration_background.py apps/accounts/tests/test_purge_expired_sessions.py apps/audit/tests/test_purge_access.py` pasa: las tres tareas aceptan `simulate_failure: bool = False`, delegan en `run_maintenance_task`, conservan sus reglas de borrado al ejecutarse normal y generan fallo + alerta sin borrar datos reales cuando `simulate_failure=True`.

- [ ] T-006 Panel de administración interno de solo lectura para estado y alertas
  RF: RF-008 | Depende de: T-002 | Archivos: 2 (`backend/apps/core/admin.py`, `backend/apps/core/tests/test_maintenance_admin.py`)
  Hecho cuando: `pytest apps/core/tests/test_maintenance_admin.py` pasa: operadores autorizados pueden listar y filtrar `MaintenanceTaskStatus` y `MaintenanceAlert` (por tarea y estado abierta/resuelta) en el admin de Django, con permisos de añadir, editar y borrar deshabilitados.

- [ ] T-007 Comando CLI `maintenance_tasks` y documentación de variables en `.env.example`
  RF: RF-002, RF-008, RF-009 | Depende de: T-005 | Archivos: 3 (`backend/apps/core/management/commands/maintenance_tasks.py`, `backend/.env.example`, `backend/apps/core/tests/test_maintenance_command.py`)
  Hecho cuando: `pytest apps/core/tests/test_maintenance_command.py` pasa: `manage.py maintenance_tasks status` muestra el estado de las tres tareas (indicando «sin ejecuciones» antes de la primera) y sus alertas, `run` ejecuta manualmente una o todas, y `simulate-failure <tarea>` encola la tarea con `simulate_failure=True` para verificar el flujo en el trabajador; `.env.example` documenta todas las variables nuevas.

- [ ] T-008 Pruebas end-to-end con trabajador Celery real sobre Redis
  RF: RF-001, RF-005, RF-007, RF-009 | Depende de: T-007 | Archivos: 1 (`backend/apps/core/tests/test_maintenance_worker_e2e.py`)
  Hecho cuando: `pytest apps/core/tests/test_maintenance_worker_e2e.py` pasa con el fixture `celery_worker`: el envío asíncrono de fallo simulado en las tres tareas registra el fallo, abre la alerta, emite el correo y deja intactos los registros expirados; una ejecución normal posterior en el trabajador real depura los registros elegibles y resuelve las alertas abiertas.

## Entregas
Rama de integración: `feat/tareas-purga-y-alertas` (los PR de las entregas van contra ella; ver `AGENTS.md`)

- E-01 Programación configurable de las tres purgas y tarea periódica de auditoría
  Tareas: T-001 | Líneas estimadas: 166 | Rama: `feat/tareas-purga-y-alertas-base-y-estado`
  Cómo probarlo: ejecutar `pytest apps/audit/tests/test_purge_task.py apps/audit/tests/test_purge_access.py`, comprobar en `settings.CELERY_BEAT_SCHEDULE` / `DatabaseScheduler` los tres `PeriodicTask` y lanzar `celery -A config call apps.audit.tasks.purge_security_events`.

- E-01b Modelos y ejecutor base de última ejecución y alertas
  Tareas: T-002, T-003 | Líneas estimadas: 330 | Rama: `feat/tareas-purga-y-alertas-nucleo-estado`
  Cómo probarlo: aplicar migraciones (`python manage.py migrate`), ejecutar `pytest apps/core/tests/test_maintenance_models.py apps/core/tests/test_maintenance_runner.py` y ejercitar `run_maintenance_task` desde consola (`manage.py shell`) comprobando registro de última ejecución, alerta persistente y cierre automático al recuperarse.

- E-02 Serialización, alertas completas por correo y conexión de las tres tareas
  Tareas: T-004, T-005 | Líneas estimadas: 310 | Rama: `feat/tareas-purga-y-alertas-ejecucion-y-alertas`
  Cómo probarlo: ejecutar `pytest apps/core/tests/test_maintenance_alerts.py apps/core/tests/test_maintenance_tasks.py` y disparar cualquiera de las tres tareas con `simulate_failure=True` mediante `celery -A config call apps.audit.tasks.purge_security_events --kwargs='{"simulate_failure": true}'` para observar la alerta abierta y el aviso por correo sin borrar datos, seguido de una ejecución normal que cierra la alerta.

- E-03 Panel de administración, comando CLI y verificación end-to-end con worker real
  Tareas: T-006, T-007, T-008 | Líneas estimadas: 310 | Rama: `feat/tareas-purga-y-alertas-admin-y-cli`
  Cómo probarlo: ejecutar `pytest apps/core/tests/test_maintenance_admin.py apps/core/tests/test_maintenance_command.py apps/core/tests/test_maintenance_worker_e2e.py`, abrir `/admin/core/` para consultar estado y alertas, y usar `python manage.py maintenance_tasks status`, `run` y `simulate-failure`, además de levantar `beat` y `worker` con intervalos reducidos en entorno de desarrollo para verificar que las tres tareas corren solas.

## RF sin tarea
ninguno
