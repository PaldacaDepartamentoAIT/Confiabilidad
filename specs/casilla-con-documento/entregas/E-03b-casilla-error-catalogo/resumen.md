# Entrega E-03b · Error, revalidación y catálogo de la casilla

Rama: `feat/casilla-con-documento-casilla` (sale de `feat/casilla-con-documento`, con E-03 ya fusionada) · PR: pendiente ·
Líneas de código y tests: 331 (límite: 400).

## Qué se hizo
- La casilla con documento muestra la marca de obligatoria (un asterisco fuera del enlace, más
  `aria-required`), su ayuda y su error debajo de la fila, con la reserva de espacio de los demás campos para que
  el formulario no cambie de alto. El error y la ayuda solo se ven fuera del modal.
- Al cerrar el modal, con la «×», Escape o la cortina, el foco vuelve al enlace (también en navegadores que no
  enfocan un enlace al pulsarlo) y se pide la revalidación al formulario con el estado actual de la casilla. Con
  un error visible, marcarla desde el modal no lo retira hasta cerrar el modal; al cerrarlo, se retira si está
  marcada y se mantiene si no.
- El catálogo tiene una sección «Casillas con documento» con los cuatro casos: términos (obligatoria), novedades
  por correo (opcional), política de datos (obligatoria, con error que se revalida al cerrar) y aviso de
  privacidad (sin documento). Se conserva también el modal de ejemplo de E-01b, porque la prueba en Chromium lo
  abre desde su botón.
- Verificado en un navegador real: el error no cambia la altura de la fila (42 px con y sin error), el foco vuelve
  al enlace y las 40 pruebas visuales del modal siguen pasando.
- Esta parte salió de una entrega de 670 líneas, dividida en dos por la regla de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-010 | Cierre, error y revalidación | `d530b3c` |
| T-011 | Catálogo: casilla con documento | `90bc764` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 61 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y baja hasta «Casillas con documento». Pulsa el enlace de «Acepto la política de
datos» (que tiene un error visible), marca la casilla dentro del modal —el error sigue ahí— y ciérralo: el error
desaparece y el foco vuelve al enlace. Prueba también pulsar el cuadro de otra casilla y pulsar el hueco de la
fila: no abre nada.

## Marco teórico
- **Validación al cerrar:** un formulario suele validar un campo cuando se sale de él. Como el modal se cierra
  sin que el foco «salga» de la casilla de verdad, el componente avisa al formulario a mano al cerrar para que
  valide en ese momento.
- **Reserva de espacio:** el error ocupa un hueco que ya estaba reservado, de modo que aparecer o desaparecer no
  mueve lo que hay debajo.
