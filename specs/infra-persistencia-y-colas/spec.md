# Spec — infra-persistencia-y-colas
Estado: aprobada

## Objetivo
Montar la infraestructura base del backend y demostrarla de punta a punta:
persistencia con **PostgreSQL**, **caché** y **sesiones** con Redis, y una **cola de
tareas** con **planificador de trabajos programados** (Celery + django-celery-beat).

Es el cimiento sobre el que se construirán las features de dominio. No implementa aún
lógica de negocio real; solo prueba que cada pieza de infraestructura funciona y es
verificable.

## Alcance
Incluye: configuración de caché/sesiones en Redis, una app de prueba con un modelo
desechable, una tarea Celery de prueba, el registro de una tarea periódica de demo en el
planificador, y vías CLI de verificación.

No incluye (no-objetivos):
- La entrega real de datos de equipos a usuarios según su periodicidad (feature posterior).
- Modelado del dominio real (equipos, activos, usuarios de negocio).
- Endpoints DRF de dominio, autenticación o UI.
- Degradación elegante (fail-open) ante caída de Redis.

## Requisitos funcionales
- **RF-001** — El backend usa PostgreSQL como base de datos por defecto y puede **escribir
  y leer** registros persistentes (validado con un modelo de prueba desechable).
- **RF-002** — El backend usa **Redis como backend de caché**; puede almacenar y recuperar
  valores de caché mediante la API de caché de Django.
- **RF-003** — Las **sesiones** de Django se almacenan en Redis, en un almacén **aislado**
  de la caché de datos (índice lógico/alias distinto), de modo que un `cache clear` de la
  caché de datos no afecte a las sesiones.
- **RF-004** — Existe una **cola de tareas** con Celery; una **tarea de prueba** se encola y
  se ejecuta en un worker.
- **RF-005** — Existe un **planificador de trabajos programados** con django-celery-beat,
  con schedules almacenados en BD y editables en runtime; se registra y ejecuta una **tarea
  periódica de prueba**. Esta tarea periódica de prueba **solo se registra/activa en
  entornos de desarrollo; nunca en producción**.
- **RF-006** — Todas las vías anteriores son **verificables desde CLI** (management commands
  y CLI de Celery), sin frontend (P-03).

## Supuestos
- **S-01** — La periodicidad real definida por cada usuario es una feature posterior; aquí
  solo se deja el cimiento (django-celery-beat) más una tarea periódica de demostración.
- **S-02** — El modelo de prueba (p. ej. `DemoRecord`) es **desechable** y no pre-modela el
  dominio real; se podrá eliminar sin afectar features futuras.
- **S-03** — Separación de índices lógicos de Redis, aislados entre sí: broker/result de
  Celery en `/0`, caché de datos en `/1`, **sesiones en `/2`**; así un `cache clear` de la
  caché de datos no afecta ni a la cola ni a las sesiones.
- **S-04** — Las sesiones usan un backend de caché sobre un alias Redis **propio y aislado**
  (S-03). Si más adelante se requiere mayor durabilidad, se puede migrar a `cached_db`.
- **S-05** — Redis es un servicio de infraestructura **requerido**. Ante su indisponibilidad,
  el sistema falla de forma controlada; **no** se implementa degradación elegante (fail-open)
  en esta feature — se podrá revisar más adelante.

## Criterios de aceptación
- **CA-1 (RF-001)** — Ejecutar la vía CLI de escritura crea un registro y el conteo en BD
  aumenta de forma persistente.
- **CA-2 (RF-002)** — Un `set` seguido de `get` sobre la caché devuelve el valor almacenado.
- **CA-3 (RF-004)** — Encolar la tarea de prueba y procesarla con un **worker real** (test
  de integración con broker Redis) resulta en su ejecución; efecto observable: se crea un
  registro en BD.
- **CA-4 (RF-005)** — En **desarrollo**, con el beat activo (DatabaseScheduler), la tarea
  periódica de demo se dispara automáticamente. La verificación automática comprueba que el
  `PeriodicTask` queda **registrado** en BD; el disparo real del beat se verifica manualmente
  por CLI.
- **CA-5 (calidad, constitución)** — La suite `pytest` pasa con cobertura ≥ 80%, y
  `mypy`, `ruff` y `black` quedan limpios en CI.

## Verificación (resumen; detalle en plan.md/tasks.md)
Vías CLI previstas (P-03): management commands `demo_seed` (BD), `demo_cache` (caché) y
`demo_task` (encolar tarea), más la CLI de Celery para worker y beat. La suite de tests
cubre BD, caché y comandos, y ejercita la cola con un **worker real** (fixture de Celery +
broker Redis) para validar el camino broker→worker; el registro del `PeriodicTask` del beat
se comprueba por estado en BD.

## Historial
- **2026-09-24 — Clarificación (feature nueva)** — clarificado. Resueltos C-01…C-04:
  RF-003 y RF-005 ajustados; S-03 y S-04 ajustados; S-05 añadido; CA-3 y CA-4 ajustados.
  Decisiones: tarea periódica de demo solo en desarrollo; sesiones aisladas de la caché de
  datos; verificación de la cola con worker real; Redis como servicio requerido sin fail-open.
- **2026-09-24 — Validación** — CUMPLIDA. Los 6 RF (RF-001…RF-006) y los criterios CA-1…CA-5
  verificados con evidencia (suite 13/13, cobertura 100%, mypy/ruff/black limpios), en un
  subagente con contexto limpio. Dos mejoras opcionales (no defectos) anotadas como T-009 y
  T-010: test conductual de aislamiento de sesiones (RF-003) e higiene de la fixture eager (RF-004).
