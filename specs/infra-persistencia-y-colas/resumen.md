# Resumen — infra-persistencia-y-colas
Estado: validada (CUMPLIDA) · Última actualización: 2026-09-25

## Qué se hizo
Se montó la **infraestructura base del backend** y se demostró de punta a punta:

- **Base de datos (PostgreSQL):** el backend persiste y lee datos. Se añadió un modelo
  desechable de prueba `DemoRecord` (`apps/core`) con su migración.
- **Caché (Redis):** caché de datos de Django sobre Redis, en un índice aislado (`/1`).
- **Sesiones (Redis):** las sesiones de usuario viven en Redis, en un índice **separado** de
  la caché (`/2`), para que limpiar la caché no cierre las sesiones.
- **Cola de tareas (Celery):** una tarea de prueba `record_ping` se encola y la ejecuta un
  worker real.
- **Planificador (django-celery-beat):** trabajos programados con horarios guardados en la
  base de datos y **editables en caliente** (pensado para la periodicidad que definirá cada
  usuario). Incluye una tarea periódica de demostración que **solo se activa en desarrollo**.
- **Verificación por CLI:** comandos `demo_seed`, `demo_cache`, `demo_task` y
  `demo_beat_register` para probar cada pieza sin necesidad de frontend.

Calidad: 13 tests automáticos en verde, cobertura 100 %, y análisis estático limpio
(ruff, black, mypy). Validado de forma independiente (ver `spec.md` → Historial).

## Cómo probarlo (usuario)
Requisitos: tener **Podman** funcionando. Abre una terminal en la raíz del repo.

```powershell
# 1. Situarte en la rama y preparar servicios
git switch feat/infra-persistencia-y-colas
podman compose -f docker/docker-compose.yml up -d db redis
podman compose -f docker/docker-compose.yml build backend
podman compose -f docker/docker-compose.yml run --rm backend python manage.py migrate

# 2. Prueba automática completa (debe dar 13 passed, 100% cobertura)
podman compose -f docker/docker-compose.yml run --rm backend pytest -q

# 3. Base de datos: crea un registro (repite y el total sube)
podman compose -f docker/docker-compose.yml run --rm backend python manage.py demo_seed

# 4. Caché: escribe y lee una clave (imprime "Cache get -> demo-command-value")
podman compose -f docker/docker-compose.yml run --rm backend python manage.py demo_cache

# 5. Cola + worker real: arranca el worker, encola la tarea y mira los logs
podman compose -f docker/docker-compose.yml up -d worker
podman compose -f docker/docker-compose.yml run --rm backend python manage.py demo_task
podman compose -f docker/docker-compose.yml logs --tail 20 worker

# 6. Planificador (solo desarrollo): registra la periódica, arranca el beat y espera ~60s
podman compose -f docker/docker-compose.yml run --rm backend python manage.py demo_beat_register
podman compose -f docker/docker-compose.yml up -d beat
podman compose -f docker/docker-compose.yml logs --tail 30 beat worker

# 7. Estado en BD (evidencia de persistencia)
podman compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.core.models import DemoRecord; print('total:', DemoRecord.objects.count())"

# Al terminar (opcional): apaga los servicios (los datos se conservan)
podman compose -f docker/docker-compose.yml down
```

Análisis estático (opcional, en el venv de Windows):
```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m black --check .
.\.venv\Scripts\python.exe -m mypy .
cd ..
```

## Referencias
- Requisitos y criterios: `spec.md`
- Diseño técnico y decisiones: `plan.md`
- Desglose de tareas: `tasks.md`
