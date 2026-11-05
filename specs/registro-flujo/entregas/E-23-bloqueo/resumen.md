# Entrega E-23 · Correcciones de la segunda validación

Rama: `feat/registro-flujo-bloqueo` · PR: pendiente ·
Líneas de código y tests: 95 (límite: 400).

La segunda validación de la feature (subagente sin contexto, 2026-11-04) dio NO CUMPLIDA por RF-009
(fallo de código, encontrado en Chromium contra el backend real) y por dos aserciones que faltaban
para RF-012 y RF-019. El usuario aprobó estas dos tareas de corrección.

## Qué se hizo
- **El bloqueo se muestra al quinto intento** (`frontend/src/registration/VerifyPage.tsx`, T-059):
  el servidor responde «código incorrecto» al intento que agota los cinco y «bloqueado» solo a
  partir del siguiente. La pantalla solo se bloqueaba con esa segunda respuesta, así que tras el
  quinto fallo seguía ofreciendo el envío. Ahora, tras un código incorrecto, consulta el estado: si
  el código ya está bloqueado, muestra «Has agotado los intentos…» y desactiva «Verificar»; si no,
  conserva el mensaje de código incorrecto bajo el campo.
- **Datos del cliente y límite por IP** (`backend/apps/accounts/tests/test_registration_flow_api.py`,
  T-060): un test demuestra que completar ignora el correo, el nombre y el país que envíe el
  cliente, y otro que, superado el límite por IP, un identificador desconocido, uno inválido y uno
  real reciben exactamente la misma respuesta `429`.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-059 | El bloqueo se muestra al quinto intento fallido | `a356b6e` |
| T-060 | Tests de los datos del cliente al completar y del límite con cualquier identificador | `2efa640` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, ejecuta los tests de la pantalla de verificación:
```bash
pnpm --filter frontend exec vitest run src/registration/VerifyPage
```
Deberías ver 39 tests en verde, entre ellos «the fifth wrong code shows the lock without another
attempt». Levanta Postgres y Redis:
```bash
docker compose -f docker/docker-compose.yml up -d db redis
```
Ejecuta los tests de la API del flujo:
```bash
docker compose -f docker/docker-compose.yml run --rm backend pytest -q apps/accounts/tests/test_registration_flow_api.py
```
Deberías ver todos en verde. Para verlo en el navegador, sigue «En la web» de
[`resumen.md`](../../resumen.md) hasta la pantalla de verificación y escribe `000000` cinco veces:
al quinto deberías ver «Has agotado los intentos con este código…» y el botón «Verificar»
desactivado.

## Marco teórico
- **Por qué el servidor no responde «bloqueado» al quinto intento.** El servidor cuenta el intento
  fallido y responde por ese intento: el código era incorrecto. Solo al siguiente envío ve que ya
  había cinco y responde «bloqueado». Cambiarlo en el servidor obligaría a cambiar también la
  equivalencia entre plaza y registro real; preguntar el estado tras cada fallo, que no cuenta para
  el límite por IP, lo resuelve en la pantalla sin tocar el servidor.
