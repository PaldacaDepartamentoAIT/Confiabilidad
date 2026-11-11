# Entrega E-13b · Tabla

Rama: `feat/sistema-de-diseno-tabla` (sale de `feat/sistema-de-diseno`, con E-13 ya fusionada) · PR: pendiente ·
Líneas de código y tests: 363 (límite: 400).

## Qué se hizo
- Hay una tabla con cabecera de 12,5 px en texto secundario y filas de 44 px separadas por una línea
  de 1 px. Cada columna es de uno de tres tipos: texto, código (fuente monoespaciada de 13 px) o
  estado (la forma de la prioridad —cuadrado, triángulo, rombo, cuadrado vacío— junto al texto, que va
  siempre en tinta; el estado normal no lleva forma pero reserva el mismo hueco de 16 px).
- Si la tabla no cabe, se desplaza en horizontal dentro de su bloque; la región se puede enfocar con el
  teclado y tiene nombre. Con la pantalla a 420 px, la tabla (640 px) se desplaza dentro de 300 px.
- Sin filas, la tabla muestra una sola celda con el mensaje de vacío en lugar de las filas.
- El catálogo tiene una sección «Tabla» con el inventario de la referencia (cinco activos, con chips de
  criticidad y los cuatro estados) y una tabla sin filas.
- No incluye selección de filas ni pie de tabla (la guía los describe, pero RF-022 no los pide).
- Esta parte salió de «Indicadores y tabla» (478 líneas), dividida por la regla de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-044 | Tabla | `89c05ad` |
| T-066 | Catálogo: tabla | ver historial de la rama |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 52 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y baja hasta «Tabla»: verás el inventario de activos con sus estados y,
debajo, una tabla vacía con su mensaje. Estrecha la ventana por debajo de 640 px y desplaza la tabla
en horizontal.

## Marco teórico
- **Estado sin depender del color:** cada estado lleva una forma distinta además del color, y el texto
  va en tinta. Así una persona que no distingue colores sigue sabiendo qué estado es.
- **Región desplazable con foco:** una zona que se desplaza solo con el ratón es inaccesible para quien
  usa el teclado; por eso la tabla está en una región enfocable y con nombre.
