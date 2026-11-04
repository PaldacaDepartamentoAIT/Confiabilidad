# Entrega E-22 · Correcciones de la validación

Rama: `feat/registro-flujo-correcciones` · PR: pendiente ·
Líneas de código y tests: 111 (límite: 400).

La validación de la feature (subagente sin contexto, 2026-11-04) dio NO CUMPLIDA por RF-024 (fallo
de código) y por dos tests que no cubrían lo que piden RF-017 y RF-014. El usuario aprobó estas tres
tareas de corrección.

## Qué se hizo
- **Límite superado al reenviar** (`frontend/src/registration/VerifyPage.tsx`, T-056): un `429` al
  pedir otro código muestra «Demasiados intentos. Vuelve a intentarlo en N s.» contando hacia atrás,
  y desaparece al llegar a cero con el botón de nuevo activo. Antes solo cambiaba la etiqueta del
  botón, igual que en la espera normal de 60 s, y la persona no sabía que había superado un límite.
  La espera normal de un código nuevo no se anuncia como límite.
- **Equivalencia con cookies y ruta web**
  (`backend/apps/accounts/tests/test_registration_flow_equivalence.py`, T-057): el test que compara
  la plaza con un registro real compara ya también las cookies de cada respuesta, que Django no
  incluye en las cabeceras, y hace parte del recorrido por la ruta web con CSRF. Una cookie que
  solo pusiera la plaza pasaba con el test anterior y ahora lo hace fallar.
- **Todo o nada con el marketing** (`backend/apps/accounts/tests/test_registration_service.py`,
  T-058): si la creación de la cuenta falla al final, no queda ni usuario, ni correo verificado, ni
  aceptación de términos, ni concesión de marketing, y el registro pendiente sigue existiendo.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commits |
|---|---|---|
| T-056 | Mensaje general al rechazar el reenvío por límite | `90e3f86` |
| T-057 | La equivalencia compara también las cookies | `c7903bc`, `b156ed6` |
| T-058 | Todo o nada al completar, también con el marketing | `c5a9b32` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, ejecuta los tests de la pantalla de verificación:
```bash
pnpm --filter frontend exec vitest run src/registration/VerifyPage
```
Deberías ver 36 tests en verde, entre ellos «over the limit, says so with the wait…» y «after the
limit, the normal wait of a new code is not announced as a limit». Levanta Postgres y Redis:
```bash
docker compose -f docker/docker-compose.yml up -d db redis
```
Ejecuta los tests de la equivalencia y del servicio del registro:
```bash
docker compose -f docker/docker-compose.yml run --rm backend pytest -q apps/accounts/tests/test_registration_flow_equivalence.py apps/accounts/tests/test_registration_service.py
```
Deberías ver todos en verde. Ejecuta la suite completa:
```bash
docker compose -f docker/docker-compose.yml run --rm backend pytest -q
```
Deberías ver 2010 tests en verde (1 omitido, ajeno a la feature).

## Marco teórico
- **Por qué un test que pasa puede no probar lo que dice.** El test de equivalencia comparaba las
  «cabeceras» de cada respuesta, pero en Django las cookies no viajan en ese diccionario. Una
  diferencia de cookies entre la plaza y el registro real habría pasado inadvertida. Un mutante (una
  cookie solo para la plaza) lo demostró: con el test anterior, todo en verde.
- **Por qué validar con alguien sin contexto.** Quien implementa tiende a dar por buenas sus propias
  decisiones; el fallo de RF-024 lo introdujo una decisión de T-048 que su propio test daba por
  correcta. Una validación hecha por quien solo lee la spec y los tests detecta esa desviación.
