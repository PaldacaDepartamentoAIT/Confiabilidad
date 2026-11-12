# Entrega E-02b · Prueba del modal en Chromium

Rama: `feat/casilla-con-documento-aspecto` (sale de `feat/casilla-con-documento`) · PR: [#107](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/107) ·
Líneas de código y tests: 216 (límite: 400).

## Qué se hizo
- Hay una prueba nueva, `frontend/visual/document-modal.visual.test.ts`, que abre el catálogo en un Chromium
  real y comprueba el modal de documento en tema claro y oscuro (13 pruebas por tema, 26 en total). Forma
  parte de `pnpm --filter frontend test:visual` y del CI.
- Comprueba lo que jsdom no puede ver: los colores de la cortina (`rgba(0, 0, 0, 0.5)`) y de la caja, el
  borde y el radio; los enlaces del documento (azul grisáceo, sin subrayado, en pestaña nueva); que Tab y
  Mayús+Tab no llevan el foco a la página de detrás; que la página de detrás no se desplaza; el cierre por
  la «×», Escape y la cortina con el foco devuelto al botón que lo abrió; el ancho de 640 px y de 568 px a
  600 px de pantalla; que se recalcula al reducir la ventana con el modal abierto; que con muy poco alto la
  «×» y la casilla siguen a la vista; que solo se desplaza el contenido; y que `axe`, con la regla de
  contraste, no halla violaciones con el modal abierto.
- Esta prueba fue la que descubrió el defecto del foco (T-016, ya arreglado en E-02): antes del arreglo,
  fallaban las seis pruebas de cierre.
- Esta parte salió de una entrega de 425 líneas, dividida en dos por la regla de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-007 | Prueba del modal en Chromium | `615e4c8` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Descarga Chromium para Playwright (solo la primera vez):
```bash
pnpm --filter frontend exec playwright install chromium
```

Ejecuta las pruebas visuales:
```bash
pnpm --filter frontend test:visual
```
Deberías ver 40 pruebas en verde (14 que ya había y 26 del modal).

Para ver que detectan un cambio, en `frontend/src/components/DocumentModal.css` cambia `rgba(0, 0, 0, 0.5)`
por `rgba(0, 0, 0, 0.4)` y vuelve a ejecutarlas: falla la de la cortina. Deshaz el cambio.

## Marco teórico
- **Probar en un navegador real:** jsdom simula el DOM pero no calcula el diseño ni el foco real. Cosas como «el
  foco no sale del modal» o «la página de detrás no se desplaza» solo se pueden comprobar en un navegador de
  verdad.
