# Entrega E-15c · Limpieza de base.css

Rama: `feat/sistema-de-diseno-limpieza` (sale de `feat/sistema-de-diseno`) · PR: pendiente ·
Líneas de código y tests: 290 (límite: 400).

## Qué se hizo
- `base.css` deja de estilar elementos sueltos. Ya no da relleno al `body`, ni caja con borde a `main`,
  `form` y `section`, ni aspecto de botón o de campo a `button`, `input` y `select`: cada pieza trae sus
  propias clases. Solo conserva el reinicio, la fuente, el foco y el movimiento reducido (y, para los
  controles, que heredan la fuente y el color y que el botón muestre la mano).
- Con ello se retiran también las reglas que compensaban las anteriores: el `margin: -22px` de la barra
  pública, los anulamientos de `.content` y de la columna pública y la separación transitoria de los
  formularios en `field.css`.
- El selector de idioma del catálogo usa ahora las clases del botón (principal el idioma activo,
  secundario los demás).
- La página del catálogo trae sus propias clases: una columna con el formulario de ejemplo dentro de un
  bloque, con sus campos apilados y las dos acciones a la derecha.
- Un test nuevo comprueba que `base.css` no estila `main`, `form` ni `section`, y que de los controles
  solo reinicia fuente, color y cursor. Falla con el `base.css` anterior.
- Comprobado con capturas antes y después (API simulada, claro y oscuro, 1000 y 420 px): las pantallas
  de registro son idénticas píxel a píxel. El catálogo cambia solo por perder la caja que envolvía toda
  la página y por el formulario de ejemplo en un bloque. El paso de la contraseña no se pudo ver en
  pantalla; sus tests pasan.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-074 | Selector de idioma con sus propias clases | `c6283c3` |
| T-073 | Catálogo sin reglas transitorias | `3409502` |
| T-051 | Retirar las reglas transitorias de `base.css` | `669f241` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 56 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y recorre el catálogo: el formulario de ejemplo está en un bloque y el selector
de idioma son tres botones. Abre http://localhost:5173/register y http://localhost:5173/register/done:
se ven igual que antes de esta entrega.

## Marco teórico
- **Estilos de elementos sueltos:** una regla como `button { … }` afecta a todos los botones de la página,
  también a los que no queremos tocar. Por eso cada pieza lleva sus propias clases y la hoja general
  solo contiene lo que de verdad es común a todo.
- **Comparar capturas:** para estar seguros de que una limpieza no cambia el aspecto, se capturan las
  pantallas antes y después y se comparan píxel a píxel; si son idénticas, no hay efectos secundarios.
