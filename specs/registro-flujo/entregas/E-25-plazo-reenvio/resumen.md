# Entrega E-25 · Plazo del código nuevo al reenviar

Rama: `feat/registro-flujo-plazo-reenvio` · PR: pendiente ·
Líneas de código y tests: 117 (límite: 400).

Implementa el cambio de RF-006 del 2026-11-05 (observación 2 de la tercera validación), con su
clarificación, el análisis de impacto, D-19 en el plan y las tareas T-064 a T-066, todo aprobado por
el usuario. El PR incluye también esos cambios de `spec.md`, `plan.md` y `tasks.md`.

## Qué se hizo
- **El plazo cuenta desde el reenvío aceptado** (`registration.py`, `processes.py`, T-064): al aceptar
  un reenvío de la pantalla o de la API, el servidor fija ya el plazo del código nuevo (hoy 15
  minutos). Antes lo fijaba la tarea que emite el código, así que con la cola de Celery atrasada la
  pantalla decía «El código ha caducado» con un código recién pedido.
- **Una tarea de emisión propia del flujo** (`tasks.py`, T-065): `reissue_flow_code` emite el código y
  su correo sin mover ese plazo. El reenvío desde la consola y el cambio de contraseña siguen con la
  tarea compartida y no cambian.
- **Equivalencia** (`test_registration_flow_equivalence.py`, T-066): entre el reenvío y la emisión, la
  plaza y un registro real dan exactamente el mismo estado, con el plazo completo.

Si el correo se retrasa, llega con menos minutos de vida, y lo dice: el correo calcula el tiempo que
queda al salir. Si no llega a salir, la pantalla cuenta igualmente y, a cero, permite pedir otro
(S-18).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-064 | El reenvío del flujo fija el plazo al aceptar | `aacb926` |
| T-065 | Tarea de emisión propia del reenvío del flujo | `f22f150` |
| T-066 | La equivalencia cubre el estado entre el reenvío y la emisión | `f113d1f` |

## Cómo ejecutarlo y probarlo
Levanta Postgres y Redis:
```bash
docker compose -f docker/docker-compose.yml up -d db redis
```
Ejecuta los tests del servicio, de la emisión y de la equivalencia:
```bash
docker compose -f docker/docker-compose.yml run --rm backend pytest -q apps/accounts/tests/test_registration_flow.py apps/accounts/tests/test_registration_background.py apps/accounts/tests/test_registration_flow_equivalence.py
```
Deberías ver todos en verde. Para verlo en el navegador, levanta el backend y el frontend sin el
worker de Celery:
```bash
docker compose -f docker/docker-compose.yml up -d db redis backend frontend
```
Regístrate en http://localhost:5173/register y, en la pantalla de verificación, espera a que el
botón «Enviar otro código» se active y púlsalo. Deberías ver «El código caduca en 15:00.»: como el
worker no está en marcha, el correo no sale, pero el plazo ya está fijado.

## Marco teórico
- **Por qué el plazo se fija en la respuesta y el código no.** El código y su correo se generan fuera
  de la respuesta para que un registro real y una plaza tarden lo mismo (D-13 de
  `procesos-pendientes`). El plazo, en cambio, es solo una fecha que se guarda igual en los dos, así
  que fijarlo en la respuesta no los distingue y evita que la pantalla dependa de lo rápida que vaya
  la cola.
