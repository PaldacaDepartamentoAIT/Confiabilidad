# Entrega E-01 · Botón desactivado

Rama: `feat/presentacion-registro-desactivado` (sale de `feat/presentacion-registro`) · PR: pendiente ·
Líneas de código y tests: 68 (límite: 400).

## Qué se hizo
- Un botón bloqueado vuelve a verse desactivado: atenuado al 60 % de opacidad, con el cursor de acción no
  permitida y sin cambiar de color al pasar el puntero. Vale para todos los botones del sistema, tanto los
  bloqueados con el atributo `disabled` (por ejemplo, «Enviar otro código» durante la cuenta atrás) como los que
  están procesando (`aria-disabled`).
- Era un fallo: al retirar las reglas transitorias de `base.css` (E-15c de `sistema-de-diseno`) se perdió el
  aspecto de desactivado de `button:disabled`, y los botones bloqueados con `disabled` se veían como activos.
  Ahora el aspecto vive en el propio botón (`Button.css`), no en `base.css`.
- El catálogo muestra un botón desactivado primario y uno secundario («Guardar bloqueado» y «Cancelar
  bloqueado»), y la guía (`docs/identidad-visual.md`) tiene una fila «Desactivado» en la tabla de botones.
- Un test lee `Button.css` y fija estas reglas (atenuado, cursor y hover solo en botones no bloqueados).
- Verificado en un navegador real: el botón desactivado mantiene su fondo al pasar el puntero y el activo se
  oscurece.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Aspecto de botón desactivado | `42a73c0` |
| T-002 | Catálogo y guía: botones desactivados | `c2de7ec` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 62 archivos de test en verde (796 tests).

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y baja hasta «Botones y avisos»: verás, bajo los botones normales, «Guardar bloqueado» y
«Cancelar bloqueado» atenuados; pasa el puntero por encima: no cambian de color y el cursor muestra que no se
puede pulsar. Pasa el puntero por «Guardar»: se oscurece.

## Marco teórico
- **`disabled` y `aria-disabled`:** el primero es el atributo nativo que bloquea un botón y lo saca del orden de
  Tab; el segundo solo avisa a las tecnologías de apoyo y deja el botón en el orden de Tab, que es lo que se usa
  mientras procesa para no perder el foco. Los dos deben verse igual de desactivados.
- **Por qué el estilo va en el botón y no en una regla general:** una regla como `button:disabled` en la hoja
  general afecta a cualquier botón, también a los que no queremos tocar; por eso cada pieza trae sus propias
  clases (decisión D-12 de `sistema-de-diseno`).
