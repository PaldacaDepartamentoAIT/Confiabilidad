# Tareas: infra-persistencia-y-colas
Estado: aprobado

- [x] T-001 Andamiaje de `apps.core` y dependencia django-celery-beat
  RF: — | Depende de: — | Archivos: 6
  Hecho cuando: `cd backend && python manage.py check` no da errores y `apps.core` y
  `django_celery_beat` están en `INSTALLED_APPS`.
  Excepción: andamiaje inicial indivisible — registrar la app (paquetes `apps/` y `apps/core/`
  + `apps.py` + `settings.INSTALLED_APPS`) junto con la dependencia (`requirements.txt`) y su
  override de mypy (`pyproject.toml`) no puede partirse sin dejar la app a medio registrar.

- [x] T-002 Modelo `DemoRecord` y migración inicial
  RF: RF-001 | Depende de: T-001 | Archivos: 5
  Hecho cuando: `cd backend && pytest apps/core/tests/test_models.py -q` pasa (crea y lee un
  `DemoRecord` en PostgreSQL).
  Excepción: incluye los `__init__.py` de andamiaje de `migrations/` y `tests/` (creados una
  sola vez); el trabajo real son `models.py`, la migración `0001_initial.py` y su test.

- [x] T-003 Caché de datos en Redis (`/1`)
  RF: RF-002 | Depende de: T-001 | Archivos: 3
  Hecho cuando: `cd backend && pytest apps/core/tests/test_cache.py -q` pasa (un `cache.set`
  seguido de `cache.get` devuelve el valor sobre el alias `default`).

- [x] T-004 Sesiones en Redis aislado (`/2`)
  RF: RF-003 | Depende de: T-003 | Archivos: 3
  Hecho cuando: `cd backend && pytest apps/core/tests/test_sessions.py -q` pasa (una sesión se
  guarda y se recupera; el engine es de caché y el alias es `sessions`, distinto de la caché
  de datos).

- [x] T-005 Tarea Celery `record_ping` verificada con worker real
  RF: RF-004 | Depende de: T-002 | Archivos: 3
  Hecho cuando: `cd backend && pytest apps/core/tests/test_task_worker.py -q` pasa —
  `record_ping.delay()` procesada por un worker real (fixture `celery_worker` + broker Redis)
  crea un `DemoRecord` con `source="task"`.

- [ ] T-006 Management commands de verificación (`demo_seed`, `demo_cache`, `demo_task`)
  RF: RF-006 | Depende de: T-002, T-003, T-005 | Archivos: 6
  Hecho cuando: `cd backend && pytest apps/core/tests/test_commands.py -q` pasa y
  `python manage.py demo_seed`, `demo_cache` y `demo_task` se ejecutan sin error.
  Excepción: incluye los `__init__.py` de `management/` y `management/commands/` (una sola vez);
  los tres comandos son pequeños y cohesivos (una única superficie de verificación CLI) y
  comparten un solo test.

- [ ] T-007 Registro de la tarea periódica de demo (solo desarrollo)
  RF: RF-005 | Depende de: T-005, T-006 | Archivos: 3
  Hecho cuando: `cd backend && pytest apps/core/tests/test_beat_register.py -q` pasa —
  `demo_beat_register` crea (idempotente) un `IntervalSchedule` + `PeriodicTask` que apunta a
  `record_ping`; repetir el comando no duplica registros.

- [ ] T-008 Beat con `DatabaseScheduler` e ignorar artefactos del scheduler de archivo
  RF: RF-005 | Depende de: T-007 | Archivos: 2
  Hecho cuando: `docker compose -f docker/docker-compose.yml config` es válido y el servicio
  `beat` usa `--scheduler django_celery_beat.schedulers:DatabaseScheduler`; y
  `git check-ignore backend/celerybeat-schedule` responde (artefacto ignorado).

## RF sin tarea
Ninguno.
