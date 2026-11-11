# Entrega E-15 · Rejilla de estado

Rama: `feat/sistema-de-diseno-rejilla` (sale de `feat/sistema-de-diseno`) · PR: pendiente ·
Líneas de código y tests: 250 (límite: 400).

## Qué se hizo
- Hay una rejilla de estado: cuadros de 24 × 24 px separados 4 px que continúan en la fila siguiente.
  Los normales van en gris; los de P1, P2 y advertencia, en su color y con el glifo de su forma (12 px,
  en el color del lienzo) dentro, para no depender solo del color; el neutro (mantenimiento), con un
  borde de 2 px en texto secundario.
- Cada cuadro es una imagen con `title` y etiqueta accesible «nombre · estado», por ejemplo «A-115 · P2».
  El conjunto es un grupo con nombre.
- Debajo lleva su leyenda: las cuatro formas de 16 px con su etiqueta en tinta (mantenimiento, P1, P2 y
  advertencia). Quien usa la pieza da los textos de cada estado, de modo que sirven en cualquier idioma.
- El catálogo tiene una sección «Rejilla de estado» con los 48 activos de la referencia. Con ella, el
  catálogo muestra ya todas las piezas de la feature. Verificado en un navegador real, en oscuro:
  cuadros de 24 × 24 px separados 4 px y glifos de 12 px.
- Queda fuera la limpieza de `base.css` (T-051): se hará en E-15b.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-049 | Rejilla de estado | `993c8a5` |
| T-050 | Catálogo: rejilla de estado | `c3625f4` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 55 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y baja hasta «Rejilla de estado»: verás 48 cuadros, ocho con estado, y la
leyenda. Pasa el ratón por un cuadro para ver su título, por ejemplo «A-115 · P2».

## Marco teórico
- **Forma además de color:** un cuadro rojo y uno verde son iguales para quien no distingue esos
  colores. Por eso cada estado lleva también una forma distinta (cuadrado, triángulo, rombo, cuadrado
  vacío); el color solo refuerza.
- **`title` y `aria-label`:** el `title` aparece al pasar el ratón; el `aria-label` es lo que lee un lector
  de pantalla. Llevan el mismo texto para que todos obtengan la misma información.
