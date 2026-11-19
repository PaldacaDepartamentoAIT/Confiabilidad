# Plan: casilla-con-documento
Estado: aprobado

## Módulos

### M-01 Modal de documento (`components/DocumentModal.tsx`, `DocumentModal.css`)
Responsabilidad: ventana modal sobre un `<dialog>` nativo, pintada fuera del formulario (portal a
`document.body`). Muestra la cortina y la caja con la «x», el documento en Markdown con desplazamiento y un
pie que recibe la casilla; se cierra con la «x», Escape y clic en la cortina; bloquea la página de detrás;
lleva el nombre accesible; da su tamaño según la guía. Los enlaces del documento se abren en pestaña nueva.
RF: RF-002, RF-003, RF-005, RF-006, RF-007, RF-008, RF-009, RF-016

### M-02 Casilla con documento (`components/fields/DocumentCheckbox.tsx`, `DocumentCheckbox.css`)
Responsabilidad: componente reutilizable, sin nada propio del registro (recibe etiqueta, contenido, nombre,
obligatoria, error, ayuda y los manejadores del formulario), cuyo texto es un enlace que abre M-01. Guarda el estado marcado y lo comparte con la
casilla del pie del modal (la de siempre, `Checkbox`). Sin documento, se comporta como `Checkbox`. Al cerrar
el modal devuelve el foco al enlace y avisa a la validación del formulario. Conserva obligatoria, ayuda y
error con su reserva de espacio.
RF: RF-001, RF-004, RF-005, RF-006, RF-010, RF-011, RF-016

### M-03 Registro (`registration/RegisterPage.tsx`)
Responsabilidad: cada casilla del registro que lleva un documento —los términos (obligatoria) y el marketing
(opcional, si hay documento)— pasa a usar M-02, una encima de la otra, en lugar de los desplegables; mismos nombres de campo, validaciones y datos
enviados. Se retiran las claves de texto de los desplegables que dejan de usarse.
RF: RF-012

### M-04 Textos en tres idiomas (`i18n/locales/*`)
Responsabilidad: clave del nombre del botón de cerrar del modal en `es`, `pt-BR` y `en`, con la paridad que ya
exigen los tests.
RF: RF-014

### M-05 Catálogo y guía (`showcase/sections/*`, `docs/identidad-visual.md`)
Responsabilidad: sección del catálogo con la casilla obligatoria, opcional, con error y sin documento; y las
filas nuevas de la guía para el modal (negros, medidas, umbral de 700 px, fundido, color de los enlaces).
RF: RF-013, RF-002, RF-009

### M-06 Prueba en navegador real (`frontend/visual/document-modal.visual.test.ts`)
Responsabilidad: en Chromium, comprueba lo que jsdom no puede: foco atrapado, página de detrás sin
desplazamiento, cierre por las tres vías con el foco devuelto, medidas y colores, recálculo al cambiar el
tamaño, y contraste y accesibilidad con el modal abierto en ambos temas. Usa el proyecto de pruebas visuales
de `sistema-de-diseno`, sin dependencias nuevas.
RF: RF-002, RF-006, RF-007, RF-009, RF-015, RF-016

## Modelo de datos
No hay: es solo frontend. El estado «marcado» vive en M-02 y el formulario sigue leyendo la casilla por su
nombre.

## Decisiones

### D-01 El modal es un `<dialog>` nativo abierto con `showModal()`
Elegida: elemento `<dialog>` nativo. El navegador ya atrapa el foco, deja inerte la página de detrás, atiende
Escape y lo pinta por encima de todo (sin pelear con los `z-index`), y su `::backdrop` es la cortina.
Descartada: un `div` con `role="dialog"` y atrapar el foco a mano.
Motivo: menos código y menos casos límite (Tab que se escapa, lectores de pantalla). El coste es que jsdom no
implementa `showModal()`: los tests unitarios usan un doble mínimo y lo que depende del navegador (foco, bloqueo,
medidas) se comprueba en Chromium (M-06).

### D-02 El texto de la casilla es un `<a href="#">` con `aria-haspopup="dialog"`
Elegida: un enlace, como pide el usuario y RF-001; su clic llama a `preventDefault` y abre el modal.
Descartada: un `<button>` con aspecto de enlace, que sería lo más habitual para abrir un diálogo.
Motivo: el usuario pidió un enlace. Se compensa con `aria-haspopup="dialog"` para que el lector anuncie que
abre un diálogo; Enter lo activa.

### D-03 La casilla de fuera no envuelve su texto en `<label>`
Elegida: la casilla se nombra con `aria-labelledby` apuntando al enlace, y la fila no tiene más acciones que el
cuadro y el enlace.
Descartada: reutilizar `Checkbox`, que envuelve el texto en `<label>`.
Motivo: un `<label>` marcaría la casilla al pulsar cualquier parte de la fila y RF-001 exige que el resto no
haga nada. Se reutilizan sus clases (`check`, `cb`) para que se vea igual.

### D-04 M-02 es dueño del estado marcado y ambas casillas son controladas
Elegida: un estado `checked` en M-02; la casilla de fuera y la del modal se controlan con él.
Descartada: que la casilla del modal lea y escriba la de fuera por referencia al DOM.
Motivo: es la forma sencilla de mantenerlas sincronizadas (RF-004) y de testearlas. La casilla de fuera
conserva el `name`, así que el formulario la lee como siempre; la del modal no tiene `name` y, al pintarse
fuera del formulario (portal), nunca entra en sus datos.

### D-05 La validación se pide al cerrar el modal con un evento de enfoque construido desde la casilla de fuera
Elegida: al cerrar, M-02 llama al `onBlur` que recibe con un evento cuyo objetivo es la casilla de fuera.
Descartada: enfocar y desenfocar la casilla de fuera para provocarlo.
Motivo: RF-011 pide revalidar al cerrar y RF-006 que el foco acabe en el enlace; enfocar la casilla un
instante movería el foco dos veces y lo anunciaría el lector de pantalla. El error se retira solo cuando se
cierra, como pide RF-011.

### D-06 El bloqueo de la página y la cortina son CSS
Elegida: `body:has(dialog[open]) { overflow: hidden }` y `dialog::backdrop` al 50 % de negro.
Descartada: cambiar el estilo del `body` desde el código al abrir y cerrar.
Motivo: no puede quedarse bloqueada si algo falla al cerrar, y `:has()` ya se usa en el proyecto. El clic en
la cortina se detecta porque el `<dialog>` ocupa toda la pantalla y la caja va dentro: un clic cuyo objetivo
es el propio `<dialog>` cierra.

### D-07 Medidas y colores del modal salen de la guía, que se amplía
Elegida: caja con el relleno negro del sistema (`--black-fill`) y texto blanco, borde de 1 px de línea en
ambos temas, 640 px de ancho máximo y `min(80 dvh, 100 dvh - 32 px)` de alto; por debajo de 700 px, el ancho
completo menos 32 px; fundido de 0,2 s; los enlaces del documento, **sin subrayado** y en un
azul grisáceo propio del modal (`#7f94b5`).
Descartada: color principal para los enlaces, como en el resto de la aplicación; y enlaces blancos.
Motivo: el principal no alcanza 4,5:1 sobre el negro y RF-015 exige contraste AA. Sin subrayado, un enlace
blanco sería idéntico al texto blanco y no se distinguiría (WCAG 1.4.1: el enlace debe distinguirse por algo
más que no sea solo el color del texto, o tener 3:1 de contraste con el texto que lo rodea). `#7f94b5` da
unos 5,4:1 sobre el relleno negro del tema claro, 6,8:1 sobre el negro del oscuro y 3,1:1 respecto al blanco
del texto; es un valor calculado, que las pruebas de accesibilidad en Chromium (M-06) confirman o corrigen.
Las filas nuevas de `docs/identidad-visual.md` las aprueba el usuario con el plan.

### D-08 Los textos del documento llegan de la pantalla; el componente solo trae su propio texto
Elegida: la pantalla pasa la etiqueta y el contenido; el componente aporta solo el nombre del botón de cerrar
(clave nueva en los tres idiomas).
Descartada: que el componente pida el documento al servidor.
Motivo: S-01 (el documento llega ya cargado). Evita acoplar la pieza a la API y es el mismo criterio que ya
siguen `Table`, `BarChart` y `StatusGrid`.

### D-09 La rama de integración sale de `feat/sistema-de-diseno`, no de `main`
Elegida: `feat/casilla-con-documento` parte de `feat/sistema-de-diseno`.
Descartada: partir de `main`, como pide `AGENTS.md`.
Motivo: la feature usa piezas que aún no están en `main` (S-05). Su PR a `main` espera a que se fusione el de
`sistema-de-diseno`; hasta entonces, sus PR de entrega van contra `feat/casilla-con-documento`.

## Estrategia de tests
- **Unitario (Vitest + jsdom, P-04 y P-05):** `DocumentModal`, `DocumentCheckbox`, el registro y las claves de
  idioma. jsdom no implementa `<dialog>.showModal()`: `setupTests.ts` añade un doble mínimo que marca y
  desmarca el atributo `open` y emite `close`. Se prueban estructura, sincronización, cierre, foco devuelto,
  sin documento, error y revalidación, enlaces en pestaña nueva, textos al cambiar de idioma y accesibilidad
  con `axe`.
- **Navegador real (proyecto de pruebas visuales, Chromium):** foco atrapado, página de detrás sin
  desplazamiento, medidas (640 px, 80 %, 700 px, margen de 16 px), colores de la cortina y la caja en ambos
  temas, recálculo al cambiar el tamaño, contraste y accesibilidad con el modal abierto. Entra en el CI que ya
  ejecuta `test:visual`.
- **Catálogo:** test de `ShowcasePage` con la sección nueva.
- **Mutantes:** cada tarea prueba al menos uno (por ejemplo, el modal que se cierra al marcar, o la casilla
  de fuera envuelta en `<label>`).
- **Sin cambios:** la comparación exacta con las referencias no cambia, porque el modal no está en ninguna
  referencia (RF-028 omite las piezas que no existen en la referencia).

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-02 | unitario |
| RF-002 | M-01, M-05, M-06 | unitario, navegador |
| RF-003 | M-01 | unitario |
| RF-004 | M-02 | unitario |
| RF-005 | M-01, M-02 | unitario |
| RF-006 | M-01, M-02, M-06 | unitario, navegador |
| RF-007 | M-01, M-06 | navegador |
| RF-008 | M-01 | unitario |
| RF-009 | M-01, M-05, M-06 | navegador |
| RF-010 | M-02 | unitario |
| RF-011 | M-02 | unitario |
| RF-012 | M-03 | unitario |
| RF-013 | M-05 | unitario |
| RF-014 | M-04 | unitario |
| RF-015 | M-01, M-02, M-06 | unitario (axe), navegador (axe, teclado) |
| RF-016 | M-01, M-02, M-06 | unitario, navegador |

## RF sin cobertura
Ninguno.
