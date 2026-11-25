# Plan: tareas-purga-y-alertas
Estado: aprobado

## Módulos

### M-01 Configuración de intervalos, destinatarios y programación periódica
Responsabilidad: define en `config/settings.py` y documenta en `backend/.env.example` las variables configurables de intervalo (`PURGE_STALE_REGISTRATIONS_INTERVAL_SECONDS=3600`, `PURGE_EXPIRED_SESSIONS_INTERVAL_SECONDS=3600`, `PURGE_SECURITY_EVENTS_INTERVAL_SECONDS=86400`), la lista de destinatarios operativos (`MAINTENANCE_ALERT_EMAILS`) y el tiempo límite del bloqueo distribuido (`MAINTENANCE_LOCK_TIMEOUT_SECONDS`). Registra las tres tareas en `CELERY_BEAT_SCHEDULE` (`apps.accounts.tasks.purge_stale_registrations`, `apps.accounts.tasks.purge_expired_sessions` y `apps.audit.tasks.purge_security_events`) para que `DatabaseScheduler` las sincronice en `PeriodicTask` al arrancar `beat`.
RF: RF-001, RF-002

### M-02 Modelos y ejecutor de estado y alertas de mantenimiento
Responsabilidad: define en `apps/core/models.py` (con su migración correspondiente) los modelos `MaintenanceTaskStatus` y `MaintenanceAlert`. Implementa en `apps/core/maintenance.py` el ejecutor común `run_maintenance_task(task_name, action, *, simulate_failure=False)` con serialización por tarea mediante bloqueo distribuido en Redis, aborto controlado antes de ejecutar `action()` cuando `simulate_failure=True`, actualización sobrescrita de `MaintenanceTaskStatus` al finalizar, creación de `MaintenanceAlert` y registro de traza completa en logs ante fallos, envío de correo operativo inmediato solo si no existía alerta abierta previa para esa tarea (protegido frente a fallos de envío), manejo seguro ante indisponibilidad de BD (solo logs, sin intento de correo) y resolución automática de alertas abiertas cuando una ejecución posterior termina con éxito.
RF: RF-003, RF-004, RF-005, RF-006, RF-007

### M-03 Tareas periódicas de purga conectadas al ejecutor
Responsabilidad: adapta `apps.accounts.tasks.purge_stale_registrations` y `apps.accounts.tasks.purge_expired_sessions` en `apps/accounts/tasks.py`, e implementa `apps.audit.tasks.purge_security_events` en `apps/audit/tasks.py`, aceptando `simulate_failure: bool = False` y delegando la ejecución en `run_maintenance_task`. La tarea de auditoría invoca `call_command("purge_security_events")` preservando intactas las reglas de retención de cada dominio y la guarda de acceso solo-inserción de `apps/audit/models.py`.
RF: RF-001, RF-003, RF-004, RF-005, RF-007, RF-009

### M-04 Panel de administración interno
Responsabilidad: registra en `apps/core/admin.py` los modelos `MaintenanceTaskStatus` y `MaintenanceAlert` en modo solo lectura para operadores autorizados (`is_staff` con permisos de vista o superusuarios), con columnas de estado, fechas de inicio/fin/resolución, cantidad depurada, resumen truncado de error y filtros por tarea y estado (abierta/resuelta).
RF: RF-008

### M-05 Comando de consola (CLI) de operación, consulta y simulación
Responsabilidad: implementa `python manage.py maintenance_tasks` en `apps/core/management/commands/maintenance_tasks.py` con subcomandos para: consultar el estado de última ejecución de las tres tareas (indicando explícitamente si alguna aún no tiene ejecuciones) y sus alertas (`status`), ejecutar manualmente una o todas las tareas (`run <tarea|--all>` con opción `--async`) y lanzar cualquiera de las tres en modo de fallo simulado encolado en el trabajador Celery (`simulate-failure <tarea>` con espera opcional del resultado).
RF: RF-008, RF-009

## Modelo de datos

### `MaintenanceTaskStatus` (`apps/core/models.py`)
- `task_name`: `CharField(max_length=64, unique=True, choices=MaintenanceTaskName.choices)` (`purge_stale_registrations`, `purge_expired_sessions`, `purge_security_events`). No existen filas antes de la primera ejecución de cada tarea.
- `started_at`: `DateTimeField()`
- `finished_at`: `DateTimeField()`
- `status`: `CharField(max_length=16, choices=Status.choices)` (`success` | `failure`)
- `deleted_count`: `PositiveIntegerField(default=0)`
- `error_summary`: `CharField(max_length=500, blank=True, default="")`

### `MaintenanceAlert` (`apps/core/models.py`)
- `task_name`: `CharField(max_length=64, choices=MaintenanceTaskName.choices, db_index=True)`
- `created_at`: `DateTimeField(default=timezone.now, db_index=True)`
- `error_summary`: `CharField(max_length=500)`
- `resolved_at`: `DateTimeField(null=True, blank=True, db_index=True)` (nulo = abierta; con fecha = resuelta)

## Decisiones

### D-01 Centralizar seguimiento, alertas, admin y CLI en `apps.core`
Elegida: ubicar `MaintenanceTaskStatus`, `MaintenanceAlert`, `apps/core/maintenance.py`, `apps/core/admin.py` y el comando `maintenance_tasks` en `apps.core`, dejando cada tarea `@shared_task` en su app de dominio (`apps.accounts.tasks` y `apps.audit.tasks`).
Descartada: crear una nueva app Django exclusiva para mantenimiento o duplicar estado/alertas entre `accounts` y `audit`.
Motivo: `apps.core` ya aloja la infraestructura transversal (`beat.py`, `checks.py`, `fingerprints.py`); evita duplicar modelos/lógica y mantiene desacopladas `accounts` y `audit`.

### D-02 Invocar la depuración de auditoría mediante `call_command("purge_security_events")`
Elegida: `apps.audit.tasks.purge_security_events` ejecuta `call_command("purge_security_events", stdout=buffer)` y obtiene el entero de filas eliminadas desde la salida estándar del comando.
Descartada: importar `apps.audit.models.purge_expired` desde `apps.audit.tasks` y ampliar la lista blanca de `apps/audit/tests/test_purge_access.py`.
Motivo: reutiliza la interfaz CLI pública ya existente sin alterar los tests ni los límites de seguridad de la feature `auditoria-eventos-seguridad`.

### D-03 Serialización por tarea mediante bloqueo distribuido en Redis
Elegida: serializar ejecuciones concurrentes de una misma tarea usando un bloqueo de `redis.Redis.from_url(settings.CACHE_URL).lock(f"maintenance-task:{task_name}", timeout=settings.MAINTENANCE_LOCK_TIMEOUT_SECONDS, blocking=True)`.
Descartada: bloqueo en base de datos (`select_for_update` o advisory lock de PostgreSQL) o ejecución sin bloqueo.
Motivo: evita solapamientos entre ejecuciones automáticas y manuales incluso entre distintos procesos worker, no bloquea tareas distintas entre sí y no falla antes de tiempo si la base de datos es precisamente lo que está caído.

### D-04 Envío directo de correos de alerta con `EmailMessage`
Elegida: enviar los avisos de fallo directamente con `django.core.mail.EmailMessage` en `apps/core/maintenance.py` dentro de un bloque `try/except` que registra cualquier error de envío sin perder el estado ni la alerta.
Descartada: encolar en `apps.emails.outbox.OutboundEmail` (que depende de la propia base de datos, plantillas `EmailTemplate` y del ciclo de `dispatch_due`).
Motivo: ante un fallo en tareas de mantenimiento o cola saturada, el aviso debe intentar salir de inmediato sin depender de plantillas en BD ni de otra tarea periódica.

### D-05 Resumen de error truncado en BD/correo y traza completa solo en logs
Elegida: construir `error_summary` con `f"{type(exc).__name__}: {exc}"` (espacios normalizados y truncado a 500 caracteres) para `MaintenanceTaskStatus`, `MaintenanceAlert` y el correo operativo, emitiendo la traza completa únicamente vía `logger.exception(...)`. Si falla la persistencia en BD al registrar el fallo o la alerta, se registran ambas excepciones con `logger.exception(...)` y se omite el envío de correo.
Descartada: almacenar o enviar por correo el stacktrace completo, o intentar enviar correo cuando no es posible comprobar en BD si ya existe alerta abierta.
Motivo: evita filtrar trazas internas o secretos en correos/panel y evita tormentas de correos ante caídas prolongadas de base de datos.

### D-06 Sincronización de las tres tareas en `CELERY_BEAT_SCHEDULE` con `DatabaseScheduler`
Elegida: definir las tres entradas en `settings.CELERY_BEAT_SCHEDULE` usando variables de entorno en segundos (`PURGE_*_INTERVAL_SECONDS`), de modo que `DatabaseScheduler.setup_schedule()` actualice `PeriodicTask` al arrancar `beat` (y sea ajustable a intervalos cortos en desarrollo/tests sin tocar código).
Descartada: migraciones de datos fijas con `PeriodicTask` o intervalos codificados sin variable de entorno.
Motivo: mantiene compatibilidad con los tests existentes de `CELERY_BEAT_SCHEDULE`, permite demostrar el disparo autónomo en segundos cambiando solo variables de entorno y respeta el `DatabaseScheduler` ya configurado en `docker/docker-compose.yml`.

## Estrategia de tests
- **Unitarios (`pytest`)**:
  - Configuración (`settings.CELERY_BEAT_SCHEDULE`, variables de entorno por defecto y sobrescritas, `DatabaseScheduler.setup_schedule()` creando/actualizando los tres `PeriodicTask`).
  - Ejecutor (`run_maintenance_task`): estado inicial ausente, sobrescritura de `MaintenanceTaskStatus` en éxito/fallo, truncado de `error_summary`, emisión de log con traza completa, supresión de correo en fallos consecutivos con alerta abierta previa, resolución automática de alertas abiertas en el siguiente éxito, resiliencia ante fallo de envío SMTP, comportamiento ante caída de BD (solo logs, sin correo), `simulate_failure=True` abortando antes de ejecutar `action()` y serialización ordenada de dos ejecuciones concurrentes de la misma tarea.
  - Tareas (`purge_stale_registrations`, `purge_expired_sessions`, `purge_security_events`): preservación de las reglas de borrado de cada dominio y preservación de `test_purge_access.py`.
  - Admin (`MaintenanceTaskStatusAdmin`, `MaintenanceAlertAdmin`): permisos de lectura para operadores autorizados, denegación de alta/edición/borrado y visualización/filtros.
- **Integración y CLI (`pytest`)**:
  - Comando `manage.py maintenance_tasks` (`status`, `run`, `simulate-failure`): salida legible, ejecución real de purga sin borrar datos cuando se simula fallo y comprobación de `MaintenanceTaskStatus`, `MaintenanceAlert`, logs y `mail.outbox`.
- **End-to-End con trabajador y planificador reales (`pytest` + verificación CLI)**:
  - Con el fixture `celery_worker` (worker Celery real sobre broker Redis): disparo asíncrono de `simulate-failure` para las tres tareas comprobando actualización de estado, alerta abierta, correo y cero datos borrados, seguido de ejecución exitosa que resuelve la alerta.
  - Verificación en el entorno Docker/Compose con intervalos reducidos en variables de entorno demostrando que `beat` (`DatabaseScheduler`) y `worker` disparan las tres tareas de forma autónoma y que `maintenance_tasks simulate-failure` genera la alerta completa.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 Ejecución automática de las tres tareas | M-01, M-03 | Unitario, Integración (`DatabaseScheduler`), E2E (worker + beat) |
| RF-002 Frecuencias configurables de programación | M-01 | Unitario, Integración (`DatabaseScheduler`) |
| RF-003 Preservación de reglas de retención y protección | M-02, M-03 | Unitario, Integración (`test_purge_access.py` y suites de purga) |
| RF-004 Registro de la última ejecución y serialización | M-02, M-03 | Unitario, Integración (concurrencia) |
| RF-005 Alerta inmediata, log completo y supresión de correo repetido | M-02, M-03 | Unitario, Integración, E2E |
| RF-006 Resiliencia ante fallo del canal de correo | M-02 | Unitario |
| RF-007 Resolución automática de alertas al recuperarse | M-02, M-03 | Unitario, E2E |
| RF-008 Consulta en el panel de administración interno | M-04, M-05 | Unitario, Integración |
| RF-009 Operación, consulta y fallo simulado desde CLI | M-03, M-05 | Integración, E2E (`celery_worker`) |

## RF sin cobertura
ninguno
