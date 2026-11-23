# Entrega E-07e · Selección de filas con casillas en tablas

Rama: `feat/inicio-cierre-sesion-tabla-seleccion` · PR: pendiente · Líneas de código y tests: 428 (límite: 400).
Excepción: 428 líneas reales (dentro de `sdd.max_lineas_pr_excepcion`, 500) por entregar en un mismo corte vertical el componente `Table` seleccionable con su barra superpuesta animada, sus pruebas unitarias y de accesibilidad, el icono `IconTrash` y su muestra en `/`.

## Qué se hizo
- Se documentó la selección de filas y la barra superpuesta animada en [`docs/identidad-visual.md`](../../../../docs/identidad-visual.md) (fila «Selección de filas» de la tabla).
- `Table` ([`Table.tsx`](../../../../frontend/src/components/data/Table.tsx), [`Table.css`](../../../../frontend/src/components/data/Table.css)) admite ahora la propiedad opcional `selection`:
  - Añade una primera columna de `44 px` con una casilla por fila seleccionable y, cuando se indica `selectAllLabel` (para tablas con acciones sobre múltiples elementos), una casilla en la cabecera que marca o desmarca todas las filas seleccionables (estado intermedio con una raya si solo hay algunas). Si se omite `selectAllLabel`, la cabecera no muestra casilla de «seleccionar todo».
  - Las filas que `isSelectable` descarta no llevan casilla y «seleccionar todo» las ignora.
  - Las filas marcadas se resaltan con el fondo del 9 % de la tinta y una línea de `2 px` en el color principal a su izquierda.
  - Mientras haya alguna fila marcada, aparece superpuesta sobre la cabecera (`44 px` de alto, sin aumentar la altura de la tabla y fija ante el desplazamiento horizontal) una barra (`.table-selection-bar`) con animación de arriba hacia abajo (`0,18 s`, fundido y `6 px`), fondo `--secondary`, línea izquierda de `2 px` en `--primary`, la misma casilla alineada a `12 px` con idéntico comportamiento, el conteo (`selectedLabel(count)`, por ejemplo `n seleccionadas`) a su lado y `actions` (botones de icono compactos) a la derecha.
- Se añadió `IconTrash` a la librería de iconos.
- El catálogo muestra el ejemplo en la tabla «Inventario de activos» ([`DataSection.tsx`](../../../../frontend/src/showcase/sections/DataSection.tsx)).

## Commits

- `382d64d` — documenta la selección de filas en tablas
- `68b87de` — añade `IconTrash` a la librería de iconos
- `7894b3e` — añade selección de filas con casillas en `Table`
- `01ba559` — actualiza especificación de barra de selección inferior en `docs/identidad-visual.md`
- `b848b94` — mueve las acciones a barra animada con `n seleccionadas` y hace opcional `selectAllLabel`
- `63bfb09` — documenta barra superpuesta sobre cabecera en `docs/identidad-visual.md`
- `1a48276` — superpone la barra de selección sobre la cabecera (`44 px`) con la casilla alineada a `12 px`

## Cómo ejecutarlo y probarlo
Actualiza las ramas remotas y cambia a la rama de la entrega:

```bash
git fetch origin
```

```bash
git checkout feat/inicio-cierre-sesion-tabla-seleccion
```
Deberías ver tu copia de trabajo en `feat/inicio-cierre-sesion-tabla-seleccion`.

### Verlo en el navegador
Levanta el servidor de desarrollo del frontend:

```bash
pnpm --filter frontend dev
```
Deberías ver Vite sirviendo la aplicación en `http://localhost:5173/`.

Abre `http://localhost:5173/` y baja hasta la tabla «Inventario de activos»: marca una o varias casillas y verás superponerse sobre la cabecera de la tabla (sin cambiar su alto) la barra animada con la casilla alineada a la izquierda, «n seleccionadas» a su lado y el botón de icono a la derecha.

### Tests y análisis estático
Ejecuta las pruebas de la tabla, los iconos y el catálogo:

```bash
pnpm --filter frontend test src/components/data/Table.test.tsx src/icons/icons.test.tsx src/showcase/ShowcasePage.test.tsx src/showcase/a11y.test.tsx
```
Deberías ver las cuatro suites en verde.

```bash
pnpm --filter frontend lint
```
Deberías ver el linter limpio sin errores.

```bash
pnpm --filter frontend typecheck
```
Deberías ver `tsc --noEmit` terminar sin errores.
