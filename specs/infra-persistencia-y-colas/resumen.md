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

1. Sitúate en la rama y prepara los servicios, un comando cada vez:
```powershell
git switch feat/infra-persistencia-y-colas
```
```powershell
podman compose -f docker/docker-compose.yml up -d db redis
```
```powershell
podman compose -f docker/docker-compose.yml build backend
```
```powershell
podman compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
```

2. Prueba automática completa:
```powershell
podman compose -f docker/docker-compose.yml run --rm backend pytest -q
```
Debe dar 13 passed y 100 % de cobertura.

3. Base de datos: crea un registro.
```powershell
podman compose -f docker/docker-compose.yml run --rm backend python manage.py demo_seed
```
Si lo repites, el total sube.

4. Caché: escribe y lee una clave.
```powershell
podman compose -f docker/docker-compose.yml run --rm backend python manage.py demo_cache
```
Imprime `Cache get -> demo-command-value`.

5. Cola + worker real: arranca el worker, encola la tarea y mira los logs.
```powershell
podman compose -f docker/docker-compose.yml up -d worker
```
```powershell
podman compose -f docker/docker-compose.yml run --rm backend python manage.py demo_task
```
```powershell
podman compose -f docker/docker-compose.yml logs --tail 20 worker
```

6. Planificador (solo desarrollo): registra la tarea periódica, arranca el beat, espera unos 60 s
   y mira los logs.
```powershell
podman compose -f docker/docker-compose.yml run --rm backend python manage.py demo_beat_register
```
```powershell
podman compose -f docker/docker-compose.yml up -d beat
```
```powershell
podman compose -f docker/docker-compose.yml logs --tail 30 beat worker
```

7. Estado en la base de datos (evidencia de persistencia):
```powershell
podman compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.core.models import DemoRecord; print('total:', DemoRecord.objects.count())"
```

Al terminar (opcional), apaga los servicios; los datos se conservan:
```powershell
podman compose -f docker/docker-compose.yml down
```

Análisis estático (opcional, en el venv de Windows). Entra en `backend`:
```powershell
cd backend
```
Ejecuta las tres herramientas, una cada vez:
```powershell
.\.venv\Scripts\python.exe -m ruff check .
```
```powershell
.\.venv\Scripts\python.exe -m black --check .
```
```powershell
.\.venv\Scripts\python.exe -m mypy .
```
Vuelve a la raíz:
```powershell
cd ..
```

## Referencias
- Requisitos y criterios: `spec.md`
- Diseño técnico y decisiones: `plan.md`
- Desglose de tareas: `tasks.md`
