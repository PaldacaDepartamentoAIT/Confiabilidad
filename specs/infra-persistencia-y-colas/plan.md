# Plan: infra-persistencia-y-colas
Estado: aprobado

## Módulos

### M-01 Configuración de caché y sesiones
Responsabilidad: en `backend/config/settings.py`, definir `CACHES` con dos aliases sobre el
backend nativo `django.core.cache.backends.redis.RedisCache` — `default` (datos, Redis `/1`)
y `sessions` (Redis `/2`) — y configurar `SESSION_ENGINE =
"django.contrib.sessions.backends.cache"` con `SESSION_CACHE_ALIAS = "sessions"`. Nuevos
`CACHE_URL` y `SESSION_CACHE_URL` en settings y `.env.example`. Registrar `django_celery_beat`
y `apps.core` en `INSTALLED_APPS`.
RF: RF-002, RF-003

### M-02 Persistencia de prueba
Responsabilidad: nueva app `backend/apps/core/` (con `backend/apps/__init__.py`) que aporta el
modelo desechable `DemoRecord` y su migración `0001_initial`. Ejercita la escritura/lectura en
PostgreSQL (ya configurado en `settings.DATABASES`).
RF: RF-001

### M-03 Cola de tareas de prueba
Responsabilidad: `apps/core/tasks.py` con la tarea Celery `record_ping`, que crea un
`DemoRecord` (efecto observable de que la tarea se ejecutó). Celery ya está configurado en
`config/celery.py` con `autodiscover_tasks()`, que la descubrirá.
RF: RF-004

### M-04 Planificador de demo (solo desarrollo)
Responsabilidad: función idempotente de registro (en `apps/core`) que crea/actualiza un
`IntervalSchedule` + `PeriodicTask` de django-celery-beat apuntando a `record_ping`, expuesta
por el management command `demo_beat_register`. **No** se registra por migración para no
activarse en producción (RF-005). El servicio `beat` de `docker-compose.yml` pasa a usar
`--scheduler django_celery_beat.schedulers:DatabaseScheduler`. `django_celery_beat` se añade a
los overrides `ignore_missing_imports` de mypy en `pyproject.toml`.
RF: RF-005

### M-05 Vías CLI de verificación
Responsabilidad: management commands en `apps/core/management/commands/` — `demo_seed`
(escribe un `DemoRecord`), `demo_cache` (set/get sobre la caché) y `demo_task` (encola
`record_ping` con `.delay()`). Cumplen P-03 (backend verificable desde CLI).
RF: RF-006

## Modelo de datos
`DemoRecord` (app `apps.core`, tabla propia; **desechable**, S-02):
- `id`: BigAutoField (PK por defecto).
- `label`: CharField(max_length=100).
- `source`: CharField(max_length=20) — origen del registro (`seed` | `task` | `beat`), para
  distinguir en la verificación quién lo creó.
- `created_at`: DateTimeField(auto_now_add=True).

`IntervalSchedule` y `PeriodicTask` provienen de django-celery-beat (no se modelan aquí; se
usan desde M-04).

## Decisiones

### D-01 Planificador de trabajos programados
Elegida: django-celery-beat (schedules en BD).
Descartada: Celery beat integrado (`CELERY_BEAT_SCHEDULE` en código).
Motivo: el caso de uso real exige periodicidad **definida por cada usuario y editable en
runtime**; el schedule en código obligaría a redesplegar por cada cambio.

### D-02 Backend de caché
Elegida: `RedisCache` nativo de Django 4+ (usa la lib `redis` ya presente).
Descartada: `django-redis`.
Motivo: evita una dependencia extra; suficiente para el baseline. Trade-off: sin `fail-open`
ante caída de Redis, coherente con S-05 (Redis es servicio requerido en esta feature).

### D-03 Aislamiento de Redis por índice lógico
Elegida: broker/result `/0`, caché de datos `/1`, sesiones `/2` (aliases separados).
Descartada: un único índice/instancia compartida.
Motivo: un `cache clear` de la caché de datos no debe afectar ni a la cola ni a las sesiones
(RF-003, S-03).

### D-04 Almacén de sesiones
Elegida: backend de caché (`SESSION_ENGINE = ...backends.cache`) sobre el alias Redis
`sessions` (`/2`).
Descartada: `cached_db` / sesiones en BD.
Motivo: RF-003 pide sesiones en Redis y rendimiento; la durabilidad extra de `cached_db` no se
necesita ahora y queda como evolución (S-04).

### D-05 Registro de la tarea periódica de demo
Elegida: registro idempotente vía management command `demo_beat_register` (se ejecuta solo en
desarrollo).
Descartada: data migration que crea el `PeriodicTask`.
Motivo: RF-005 exige que la periódica de demo **no** corra en producción; una migración se
aplicaría en todos los entornos. El command es explícito, idempotente y testeable.

### D-06 Verificación de la cola
Elegida: test de integración con **worker real** (fixture `celery_worker` de Celery + broker
Redis).
Descartada: únicamente Celery en modo `task_always_eager`.
Motivo: CA-3 (clarificación C-03) exige ejercitar el camino real broker→worker. Trade-off: ese
test requiere Redis, disponible en CI y en `docker compose`.

## Estrategia de tests
- **Unitario** (`apps/core/tests/`):
  - `test_models.py`: crea y lee un `DemoRecord` → RF-001 (Postgres real de CI/docker).
  - `test_cache.py`: `cache.set`/`cache.get` roundtrip sobre el alias `default` → RF-002.
  - `test_sessions.py`: `SessionStore` guarda y recupera; se afirma que el engine es de caché y
    el alias es `sessions` → RF-003.
  - `test_commands.py`: `demo_seed`, `demo_cache`, `demo_task` → RF-006.
- **Integración**:
  - `test_task_worker.py`: con el fixture `celery_worker`, `record_ping.delay()` y esperar el
    resultado; se afirma que se creó el `DemoRecord` → RF-004 (CA-3, worker real).
  - `test_beat_register.py`: ejecutar `demo_beat_register` y afirmar que `IntervalSchedule` +
    `PeriodicTask` quedan en BD (idempotente al repetir) → RF-005 (CA-4, parte automática).
- **Manual / CLI** (P-03): worker y beat reales por CLI/`docker compose` para el disparo real
  del beat (CA-4, parte manual).
- **Cobertura** (P-05 ≥80%): `models.py`, `tasks.py`, comandos y la función de registro quedan
  cubiertos; `settings.py`, `celery.py` y migraciones están excluidos en `pyproject.toml`.
- La suite requiere Postgres + Redis (ambos presentes en CI y en `docker compose`).

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-02 | unitario (`test_models`) + CLI (`demo_seed`) |
| RF-002 | M-01 | unitario (`test_cache`) + CLI (`demo_cache`) |
| RF-003 | M-01 | unitario (`test_sessions`) |
| RF-004 | M-03 | integración worker real (`test_task_worker`) + CLI (`demo_task` + worker) |
| RF-005 | M-04 | integración (`test_beat_register`) + CLI/manual (beat real) |
| RF-006 | M-05 | unitario (`test_commands`) |

## RF sin cobertura
Ninguno.
