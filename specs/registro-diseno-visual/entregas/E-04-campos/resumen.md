# Entrega E-04 · Campos con hueco de error y ojo en la contraseña

Rama: `feat/registro-diseno-visual-campos` (apilada sobre `feat/registro-diseno-visual-menu-tema`,
E-03) · PR: [PaldacaDepartamentoAIT/Confiabilidad#63](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/63) · Líneas de código y tests: 473 (límite: 400; ver «Excepción» de E-04 en
`tasks.md`).

## Qué se hizo
- **Envoltorio de campo** (`FieldShell`, T-012): estructura común de los campos. El nombre va
  encima, con el asterisco de los obligatorios en alarma P1 y oculto al lector de pantalla. Bajo el
  campo hay siempre un hueco de una línea para el error, haya o no error, así que aparecer o
  desaparecer un error de una línea no cambia el alto del formulario; si el error ocupa más, se ve
  entero. Con error, el borde del campo pasa a 2 px en alarma P1.
- **Texto, código, contraseña, selector y casilla** (T-013, T-014): todos usan ese hueco. Los campos
  de texto, código, contraseña y selección usan el envoltorio completo; la casilla, solo el hueco,
  porque su texto va a su derecha.
- **Ojo dentro de la contraseña** (T-015): el botón de mostrar u ocultar es un icono dentro del
  campo, a la derecha: un ojo mientras la contraseña está oculta y un ojo tachado mientras se ve. Su
  nombre para el lector de pantalla no cambia («Mostrar contraseña (Contraseña)», con «presionado»).
  Las reglas de la contraseña nueva siguen visibles bajo el campo.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-012 | Envoltorio de campo | `0325dd9` |
| T-013 | Texto, código y contraseña con el envoltorio | `7d28825` |
| T-014 | Casilla y selector con el envoltorio | `3a30b3a` |
| T-015 | Ojo dentro del campo de contraseña | `6a6a0b0` |

## Cómo ejecutarlo y probarlo
Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver todos en verde (434). Levanta el frontend:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ (la página de muestra) y pulsa «Verificar» con todo vacío: cada campo
muestra su error en el hueco que ya tenía reservado, con el borde en rojo de alarma, y el resto del
formulario no se mueve más que el alto de esas líneas. Escribe algo en la contraseña y pulsa el ojo:
se ve el texto y el icono pasa a ojo tachado. En http://localhost:5173/register verás los mismos
campos.
