# Entrega E-07e · Selección de filas con casillas en tablas

Rama: `feat/inicio-cierre-sesion-tabla-seleccion` · PR: pendiente · Líneas de código y tests: 355 (límite: 400).

## Qué se hizo
- Se documentó la selección de filas en [`docs/identidad-visual.md`](../../../../docs/identidad-visual.md) (fila «Selección de filas» de la tabla).
- `Table` ([`Table.tsx`](../../../../frontend/src/components/data/Table.tsx), [`Table.css`](../../../../frontend/src/components/data/Table.css)) admite ahora la propiedad opcional `selection`:
  - Añade una primera columna de `44 px` con una casilla por fila y una casilla en la cabecera que marca o desmarca todas las filas seleccionables (estado intermedio con una raya si solo hay algunas).
  - Las filas que `isSelectable` descarta no llevan casilla y `select all` las ignora.
  - Las filas marcadas se resaltan con el fondo del 9 % de la tinta y una línea de `2 px` en el color principal a su izquierda.
  - La propiedad `actions` aparece en la misma fila de la cabecera, alineada al extremo derecho, solo mientras haya alguna fila marcada (queda fuera de la zona con desplazamiento para que el tooltip hacia arriba de `IconButton` no se recorte).
- Se añadió `IconTrash` a la librería de iconos.
- El catálogo muestra el ejemplo en la tabla «Inventario de activos» ([`DataSection.tsx`](../../../../frontend/src/showcase/sections/DataSection.tsx)).

## Commits

- docs: documenta la selección de filas en tablas
- feat: añade `IconTrash` a la librería de iconos
- feat: añade selección de filas con casillas y acciones en la cabecera de `Table`

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
Deberías ver Vite sirviendo la aplicación en `http://localhost:5173/showcase`.

Abre `http://localhost:5173/showcase` y baja hasta la tabla «Inventario de activos»: marca una casilla de fila y verás aparecer el botón de papelera en el extremo derecho de la cabecera; marca la casilla de la cabecera y se marcan todas las filas.

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
