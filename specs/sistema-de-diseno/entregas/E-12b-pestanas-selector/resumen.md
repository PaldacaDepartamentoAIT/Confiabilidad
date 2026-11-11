# Entrega E-12b · Pestañas que no caben: selector

Rama: `feat/sistema-de-diseno-pestanas-selector` (sale de `feat/sistema-de-diseno`) · PR: [#91](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/91) ·
Líneas de código y tests: 385 (límite: 400).

## Qué se hizo
- Si las pestañas no caben en la barra superior, se desvanecen todas y aparece, pegado a la
  derecha del área de pestañas, un selector con el nombre de la pestaña activa y un chevron hacia
  abajo. Al abrirlo despliega una lista con todas las pestañas (alineada a su borde derecho y con
  la animación de los demás menús), y elegir una la activa. Cuando vuelve a haber sitio, vuelven las
  pestañas y se esconde el selector.
- El área se recalcula al montarse, al cambiar el tamaño de la ventana o del propio área, y al
  cambiar las pestañas. El control que se esconde deja de estar en el teclado y en el lector de
  pantalla, y si tenía el foco, este pasa al control que se ve. El selector se llama, por ejemplo,
  «Secciones de la pantalla: Inventario».
- Para ello, el área de pestañas (y su recorte) pasó de la barra superior al propio componente de
  pestañas: el selector tiene que vivir fuera del recorte para que su lista no se corte.
- Verificado en un navegador real en la pantalla de ejemplo del catálogo: a 1200 px caben (área de
  612 px, pestañas de 261 px); a 820 px no caben (área de 232 px) y aparece el selector con su lista
  alineada al borde derecho; elegir «Alarmas» muestra su sección.
- La lista del selector se muestra por encima del panel lateral móvil: mientras está abierta, la barra
  superior sube sobre el panel, queda sin fondo y esconde sus otros controles para no tapar el panel.
  Verificado en un navegador real a 500 px: la lista queda por encima del panel.
- Esta parte salió de las pestañas adaptables (796 líneas), dividida en tres por la regla de
  `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-039 | Pestañas que no caben | `471bbb7` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 50 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Diseño con sesión» y estrecha la ventana poco a poco: cuando
las pestañas dejan de caber, pasan a ser un selector; ábrelo, elige una sección y ensancha la ventana
para ver cómo vuelven las pestañas.

## Marco teórico
- **`inert`:** atributo que saca un trozo de la página del teclado, del ratón y del lector de
  pantalla a la vez. Se usa para que la lista de pestañas escondida no pueda recibir el foco aunque
  siga en el documento.
- **Medir si cabe:** el navegador no avisa de que algo «no cabe»; se compara el ancho que ocupa el
  contenido (`scrollWidth`) con el que tiene a su disposición (`clientWidth`) cada vez que cambia
  el tamaño.
