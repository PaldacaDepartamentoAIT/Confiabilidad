# Entrega E-05 · Campos de texto, contraseña y código

Rama: `feat/sistema-de-diseno-campos-texto` · PR: pendiente ·
Líneas de código y tests: 205 (límite: 400).

## Qué se hizo
- Los campos de texto, de contraseña y de código de verificación tienen la identidad nueva:
  etiqueta pequeña en texto secundario con asterisco para los obligatorios, campo de 36 px con
  borde de 1 px, ayuda de 12 px debajo y, si hay error, borde y icono en el rojo de P1 con el mensaje
  en tinta. Al pasar el cursor el borde pasa a 1 px en el color principal; con el foco, a 2 px, sin
  que el texto se mueva.
- El botón «Mostrar contraseña» es ahora un botón secundario, y el código de verificación se
  escribe en la fuente monoespaciada. La leyenda de obligatorios usa el estilo de ayuda.
- Los campos de las pantallas de registro y de la página de muestra ya se ven así, sin cambiar su
  comportamiento ni sus validaciones: los tests previos de todos ellos siguen pasando.
- Las reglas de separación entre campos de un formulario (`form > .fld`) son transitorias y se
  retiran cuando se limpie `base.css` (T-051).
- Esta entrega nació como parte de una sola entrega de campos y casilla (467 líneas); por el
  límite de 400 se dividió en esta y E-05b (casilla y sección «Campos» del catálogo).
- En AGENTS.md queda escrito cómo dividir una entrega que rebasa el límite de líneas: en dos, sin
  volver a preguntar, procurando que ambas muestren algo de funcionalidad.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-015 | Campo de texto restilizado | `def02fd` |
| T-016 | Contraseña, código y leyenda de obligatorios | `4aaf8e3` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 38 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, pasa el cursor por un campo (borde azul grisáceo de 1 px), haz clic en
él (borde de 2 px) y pulsa «Verify» sin rellenar nada: cada campo debe mostrar su error con borde
rojizo, icono y mensaje.

## Marco teórico
- **Borde de 2 px sin mover el texto:** al enfocar, el borde crece de 1 a 2 px y el relleno interior
  baja de 11 a 10 px, de modo que el texto no se desplaza ni un píxel.
- **Campo con error:** el color rojizo solo aparece en el borde y en el icono; el mensaje va en tinta
  porque el rojo de P1 no alcanza el contraste necesario para texto pequeño en el tema claro.
