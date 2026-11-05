# Entrega E-03 · Menú de tema en la barra superior

Rama: `feat/registro-diseno-visual-menu-tema` (apilada sobre `feat/registro-diseno-visual-tema`,
E-02) · PR: [PaldacaDepartamentoAIT/Confiabilidad#62](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/62) · Líneas de código y tests: 174 (límite: 400).

## Qué se hizo
- **Menú de tema** (`ThemeMenu` e `icons.tsx`, T-010): botón circular con un sol mientras está el
  tema claro y una luna mientras está el oscuro, también cuando el tema viene del sistema operativo.
  El menú ofrece «Claro» y «Oscuro» con el activo marcado; elegir aplica el tema al momento, lo
  guarda, cierra el menú y deja el foco en el botón, sin perder lo escrito.
- **Tema en la barra superior** (`TopBar`, T-011): la barra de todas las pantallas tiene el menú de
  idioma y, a su derecha, el de tema.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-010 | Menú de tema | `f2a28e8` |
| T-011 | Tema en la barra superior | `440846d` |

## Cómo ejecutarlo y probarlo
Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver todos en verde (422). Levanta el frontend:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/register y pulsa el sol, arriba a la derecha. Elige «Oscuro»: la página
cambia al momento y el botón muestra la luna. Recarga: sigue oscura desde el primer instante. Prueba
también con el teclado: Tab hasta el botón, Intro, flecha abajo e Intro.
