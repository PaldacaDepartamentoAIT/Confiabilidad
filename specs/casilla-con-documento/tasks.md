# Tareas: casilla-con-documento
Estado: aprobado

«Suite verde» = `pnpm --filter frontend test:coverage` (líneas ≥ 80 %), `typecheck`, `lint` y
`exec prettier --check .` sin errores, y, desde T-007, también `pnpm --filter frontend test:visual`.
En cada tarea se prueba al menos un mutante del código que introduce y debe hacer fallar sus tests.
Las rutas son relativas a `frontend/src/` salvo que se indique otra cosa.

## E-01 Modal de documento (componente)
- [x] T-001 Doble de `<dialog>` para los tests de jsdom
  RF: RF-008 | Depende de: — | Archivos: 2
  Archivos: `setupTests.ts`, `dialogStub.test.ts`.
  Hecho cuando: en jsdom, `showModal()` pone el atributo `open`, `close()` lo quita y emite `close`, y
  `dialogStub.test.ts` lo comprueba; suite verde.
  Decisiones: el doble solo se instala si jsdom no trae `showModal`, y no imita el foco ni la inertización:
  eso lo comprueba Chromium (T-007) — [Cierto]. `close()` en un diálogo cerrado no emite nada, como el
  navegador — [Probable]. Mutante muerto: `close()` sin emitir el evento.
- [x] T-002 Texto de «Cerrar» del modal en tres idiomas
  RF: RF-014 | Depende de: — | Archivos: 3
  Archivos: `i18n/locales/en.ts`, `es.ts`, `pt-BR.ts`.
  Hecho cuando: existe `button.close` en `es`, `pt-BR` y `en` y `keys.test.ts` y `locales.test.ts`
  (paridad de claves) siguen en verde.
  Decisiones: la clave se llama `button.close` ("Close", "Cerrar", "Fechar") y no `documentModal.close`, como
  decía el texto de la tarea: `locales.test.ts` enumera los grupos de primer nivel y un grupo nuevo habría
  obligado a tocar ese test, un archivo que la tarea no prevé; un «Cerrar» genérico en el grupo de los
  botones además sirve a otras piezas — [Probable] — revertir: mover la clave a un grupo propio y añadirlo a
  la lista de `locales.test.ts`. Mutante muerto: texto vacío en `pt-BR` (falla «no empty texts»).
- [x] T-003 Modal: estructura, documento y nombre accesible
  RF: RF-002, RF-003, RF-008 | Depende de: T-001, T-002 | Archivos: 3
  Archivos: `components/DocumentModal.tsx`, `DocumentModal.css`, `DocumentModal.test.tsx`.
  Hecho cuando: `DocumentModal` abierto muestra, fuera del formulario (portal), un diálogo con nombre
  accesible, con la «x», el documento en Markdown con sus enlaces abiertos en pestaña nueva
  (`target="_blank"` y `rel="noopener noreferrer"`) y un pie con lo que reciba, en ese orden; cerrado,
  no pinta nada; el aspecto mínimo (caja negra de la guía) ya está; suite verde.
  Decisiones: `DocumentModal({open, name, content, onClose, children})`; cerrado devuelve `null` (no hay
  `<dialog>` en el documento) y abierto lo pinta en `document.body` y llama a `showModal()` en un efecto.
  La «x» es el carácter «×» (con `aria-hidden`) en un botón con el nombre «Cerrar» de `button.close`, y no
  un icono de `lucide-react`: añadir `IconX` toca `icons/index.ts` y su test, fuera de los tres archivos de
  la tarea — [Probable] — revertir: añadir `IconX` y sustituir el carácter. El contenido con
  desplazamiento lleva `tabIndex={0}` para llegar a él con el teclado (RF-007, RF-015) — [Probable].
  `onClose` ya está en las propiedades pero se usa en T-004. El `<dialog>` ocupa toda la pantalla y la caja
  va dentro, para que T-004 detecte el clic en la cortina — [Cierto]. Mutantes muertos: sin `target`, se
  pinta cerrado, sin nombre accesible.
- [x] T-004 Modal: cierre por «x», Escape y cortina
  RF: RF-006 | Depende de: T-003 | Archivos: 3
  Archivos: `components/DocumentModal.tsx`, `DocumentModal.css`, `DocumentModal.test.tsx`.
  Hecho cuando: la «x», la tecla Escape y un clic en la cortina llaman a `onClose`, y un clic dentro de
  la caja no; el modal no se cierra solo por otros motivos; suite verde.
  Decisiones: el modal es controlado: «x», Escape y cortina solo llaman a `onClose`; quien lo usa deja de
  pasar `open` para cerrarlo. Escape llega como el evento `cancel` nativo, cuyo comportamiento por defecto
  (cerrar el diálogo) se anula con `preventDefault` — [Cierto]. La prueba de Escape lanza ese evento en
  jsdom; que el navegador real lo emita con la tecla se comprueba en Chromium (T-007) — [Probable]. Un test
  mal escrito (la barra espaciadora sobre la «x» enfocada sí la pulsa) se corrigió. Mutantes muertos: la
  cortina cierra también con clic dentro, Escape sin `preventDefault`, la «x» sin manejador.
## E-01b Catálogo: modal de ejemplo
- [x] T-005 Catálogo: modal de ejemplo
  RF: RF-013 | Depende de: T-004 | Archivos: 3
  Archivos: `showcase/sections/DocumentSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo tiene una sección con un botón que abre el modal con un documento de ejemplo
  (con títulos, listas y un enlace) y una casilla en el pie, y se cierra por sus tres vías; suite verde.
  Decisiones: sección «Documento en un modal» con un botón secundario «Abrir el documento», un documento de
  ejemplo con títulos, listas, un enlace y texto de relleno para que haga scroll, y la casilla de siempre
  (`Checkbox`, sin estado compartido todavía) en el pie. El contenido no lleva `lang` propio porque el
  modal se pinta en `document.body`, fuera de la región con `lang="es"` — [Probable]. Verificado en un
  navegador real a 1000 px en claro y a 420 px en oscuro: abre, la caja mide 640 px (388 px a 420 px), el
  foco queda en la «x» y Escape lo cierra — [Cierto]. Se ve que falta lo de T-006: la etiqueta de la casilla
  del pie sale en tinta sobre negro (no se lee), los enlaces en el color principal y la cortina por defecto
  del navegador — [Cierto]. Mutante muerto: `onClose` vacío.

## E-02 Aspecto del modal y foco
- [x] T-006 Aspecto del modal según la guía
  RF: RF-002, RF-007, RF-009 | Depende de: T-004 | Archivos: 3
  Archivos: `components/DocumentModal.css`, `components/documentModalCss.test.ts`,
  `docs/identidad-visual.md`.
  Hecho cuando: la cortina es `::backdrop` negro al 50 %; la caja usa `--black-fill` con texto blanco y
  borde de 1 px de línea; mide 640 px como máximo y `min(80 dvh, 100 dvh − 32 px)` de alto, con el ancho
  completo menos 32 px por debajo de 700 px; solo el contenido se desplaza; la página de detrás no se
  desplaza (`body:has(dialog[open])`); aparece con un fundido de 0,2 s; los enlaces del documento son
  `#7f94b5` sin subrayado; `docs/identidad-visual.md` recoge estas medidas en filas nuevas; el test lee
  el CSS y las comprueba; suite verde.
  Excepción: 4 archivos en lugar de 3. Vitest solo procesa los CSS de `css.include` en `vite.config.ts` y
  sin eso el test que lee `DocumentModal.css` recibe un texto vacío; añadir ese CSS son una línea en
  `frontend/vite.config.ts`. Aprobada por el usuario el 12-nov.
  Decisiones: las reglas de la guía están en `DocumentModal.css` y en una sección nueva «Modal de documento»
  de `docs/identidad-visual.md` (más una fila en la tabla de movimiento). La caja usa `width: 640px` y
  `max-width: calc(100% - 32px)`, y por debajo de 700 px `width: calc(100% - 32px)`; el alto es
  `max-height: min(80dvh, calc(100dvh - 32px))`; la cortina y la caja aparecen con el mismo fundido de 0,2 s;
  el sombreado al pasar el ratón por la «×» (blanco al 12 %) y el foco con el contorno global no vienen de
  la spec — [Probable]. Verificado en un navegador real a 1000 px en claro (cortina visible, etiqueta de la
  casilla y enlaces legibles) y a 420 px en oscuro (caja de 388 px con 16 px de margen) — [Cierto]. En el
  tema oscuro la cortina negra se nota menos porque la página ya es oscura; el borde de 1 px separa la caja —
  [Cierto]. Mutantes muertos: cortina 0,5 → 0,4 y enlace `#7f94b5` → `#546c8c`.
- [x] T-016 Corrección: el modal devuelve el foco al elemento que lo abrió
  Tipo: corrección | Origen: prueba en Chromium de T-007
  RF: RF-006 | Depende de: T-004 | Archivos: 2
  Archivos: `components/DocumentModal.tsx`, `components/DocumentModal.test.tsx`.
  Causa: el diálogo se desmonta en vez de cerrarse con `close()` y el navegador no restaura el foco al
  quitarlo del documento.
  Hecho cuando: el modal recuerda el elemento enfocado al abrirse y le devuelve el foco al cerrarse, por
  cualquier vía; el test de jsdom lo comprueba y, en Chromium, las seis pruebas de cierre de T-007 pasan;
  suite verde.
  Decisiones: el efecto que abre el diálogo guarda `document.activeElement` y su limpieza le devuelve el foco
  si sigue en el documento — [Cierto]. Se podía haber llamado a `dialog.close()` antes de desmontar, que sí
  restaura el foco, pero el modal es controlado y se desmonta al dejar de pasar `open`; recordar al elemento
  es más sencillo — [Probable] — revertir: cerrar con `close()` en la limpieza. Verificado en Chromium con las pruebas de cierre de T-007 (entrega E-02b), que fallaban antes del
  arreglo y pasan después — [Cierto]. Mutante muerto: no devolver el foco. Mutante equivalente: quitar la comprobación `isConnected` (enfocar un elemento que ya no está en el
  documento no hace nada).
## E-02b Prueba del modal en Chromium
- [x] T-007 Prueba del modal en Chromium
  RF: RF-002, RF-006, RF-007, RF-009, RF-015, RF-016 | Depende de: T-005, T-006, T-016 | Archivos: 1
  Archivos: `frontend/visual/document-modal.visual.test.ts`.
  Hecho cuando: en Chromium, en claro y oscuro, el catálogo abre el modal; Tab no sale de él; la página
  de detrás no se desplaza; se cierra por «x», Escape y cortina devolviendo el foco al botón que lo abrió;
  la caja mide 640 px (y ancho completo menos 32 px a 600 px de ancho) y no pasa del 80 % del alto; al
  cambiar el tamaño de la ventana se recalcula con el modal abierto; `axe` (con contraste) no halla
  violaciones con el modal abierto, incluido el enlace de `#7f94b5`; `pnpm --filter frontend test:visual`
  pasa.
  Decisiones: 20 pruebas por tema (40): cortina `rgba(0, 0, 0, 0.5)`, caja `rgb(27, 30, 34)` y `rgb(0, 0, 0)`
  con texto blanco, borde de 1 px y radio de 4 px; enlaces `rgb(127, 148, 181)` sin subrayado y en pestaña
  nueva; Tab y Mayús+Tab no llevan el foco a la página; la página de detrás no se desplaza (la rueda sobre la
  cortina no mueve `scrollY` y el `body` queda en `overflow: hidden`); cierre por «x», Escape y cortina con
  el foco devuelto al botón; 640 px, 568 px a 600 px de ancho y 388 px tras reducir la ventana a 420 px con
  el modal abierto; con 120 px de alto la caja no pasa de 88 px y «x» y casilla siguen a la vista; solo se
  desplaza el contenido; y `axe` con contraste sin violaciones con el modal abierto, incluido el enlace
  `#7f94b5` — [Cierto]. Descubrió el defecto de T-016. Al salir del último elemento, el navegador puede llevar
  el foco a su propia interfaz (no hay elemento activo en la página), así que lo que se afirma es que no
  caiga en la página de detrás — [Cierto]. Mutantes (del código que la prueba vigila): el de T-016 y los de
  T-006 (cortina y color del enlace) los matan estas pruebas.

## E-03 Casilla con enlace y casilla del modal
- [x] T-008 Casilla con enlace al documento
  RF: RF-001, RF-010 | Depende de: T-004 | Archivos: 3
  Archivos: `components/fields/DocumentCheckbox.tsx`, `DocumentCheckbox.css`, `DocumentCheckbox.test.tsx`.
  Hecho cuando: con documento, el texto de la casilla es un enlace (`aria-haspopup="dialog"`) que abre el
  modal sin cambiar la casilla; pulsar el cuadro la marca sin abrir el modal; pulsar el hueco de la fila no
  hace nada; la casilla se nombra con el texto del enlace y no está envuelta en `<label>`; sin contenido
  es una casilla normal sin enlace; suite verde.
  Decisiones: `DocumentCheckbox({label, document, ...inputProps})`: `label` es un texto (se usa como enlace y
  como nombre del modal) y `document` el Markdown; sin `document` pinta un `Checkbox` normal. La fila no es un
  `<label>` ni lleva la clase `check` (que da `cursor` y hover a toda la fila): usa `doc-check` y el hover solo
  sobre el cuadro — [Probable]. El enlace es `<a href="#">` que llama a `preventDefault`. El pie del modal va
  vacío hasta T-009. Mutantes muertos: fila envuelta en `<label>`, el enlace marca la casilla y sin documento
  sigue habiendo enlace. Nota: en jsdom un `<label>` que envuelve la fila no marcaba la casilla al pulsar la
  fila, así que la prueba «pulsar el resto de la fila no hace nada» no distingue ese mutante; lo distingue la
  de estructura (sin `<label>`) y lo comprobará Chromium — [Cierto].
- [x] T-009 Casilla del modal sincronizada
  RF: RF-004, RF-005 | Depende de: T-008 | Archivos: 3
  Archivos: `components/fields/DocumentCheckbox.tsx`, `DocumentCheckbox.css`, `DocumentCheckbox.test.tsx`.
  Hecho cuando: el pie del modal lleva una casilla con el mismo texto (y el asterisco si es obligatoria,
  sin ayuda ni error) cuyo texto sí la marca; marcar o desmarcar una refleja el estado en la otra; el modal
  sigue abierto al hacerlo; la casilla del modal no entra en los datos del formulario; suite verde.
  Decisiones: `DocumentCheckbox` es dueña de `checked` (arranca con `defaultChecked`) y controla las dos
  casillas con él; el `onChange` que recibe se llama desde cualquiera de las dos. La del modal es un
  `Checkbox` sin `name` y pintado en el portal, así que nunca entra en los datos del formulario. Admite la
  propiedad `required` (el asterisco del pie); la marca en la casilla de fuera, la ayuda y el error son de
  T-010. Se deja de aceptar `checked` desde fuera: el estado es de la casilla — [Probable] — revertir:
  aceptar `checked` y usarlo si llega. Mutantes muertos: el modal se cierra al marcar, la del modal arranca
  siempre sin marcar, la del modal hereda el `name` y sin asterisco en la del modal.
## E-03b Error, revalidación y catálogo de la casilla
- [ ] T-010 Cierre, error y revalidación
  RF: RF-006, RF-011 | Depende de: T-009 | Archivos: 3
  Archivos: `components/fields/DocumentCheckbox.tsx`, `DocumentCheckbox.css`, `DocumentCheckbox.test.tsx`.
  Hecho cuando: al cerrar el modal el foco vuelve al enlace y la casilla conserva su estado; la casilla
  muestra marca de obligatoria, ayuda y error con su reserva de espacio; con la casilla en error, marcarla
  desde el modal no retira el error hasta cerrar el modal, y al cerrar se pide la revalidación al formulario
  (`onBlur`) con el estado actual; suite verde.
- [ ] T-011 Catálogo: casilla con documento
  RF: RF-013 | Depende de: T-010 | Archivos: 2
  Archivos: `showcase/sections/DocumentSection.tsx`, `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo sustituye el modal de ejemplo por la casilla con documento obligatoria,
  opcional, con error y sin documento, y abre el modal en las que lo tienen; suite verde.

## E-04 Registro con la casilla
- [ ] T-012 Casilla con documento: idioma y accesibilidad
  RF: RF-015, RF-016 | Depende de: T-010 | Archivos: 1
  Archivos: `components/fields/DocumentCheckbox.test.tsx`.
  Hecho cuando: con el modal abierto, cambiar el idioma actualiza el texto de la casilla, del enlace y del
  botón de cerrar sin cerrarlo y conservando el estado y el foco; `axe` no halla violaciones con el modal
  cerrado ni abierto; todo se puede hacer con el teclado (Enter en el enlace, Tab dentro del modal, Espacio,
  Escape); suite verde.
- [ ] T-013 Registro con la casilla con documento
  RF: RF-012 | Depende de: T-010 | Archivos: 2
  Archivos: `registration/RegisterPage.tsx`, `registration/RegisterPage.test.tsx`.
  Hecho cuando: el formulario de registro muestra los términos (obligatoria) y, si hay documento de
  marketing, el marketing (opcional) con `DocumentCheckbox`, una encima de la otra, sin los desplegables;
  los nombres de campo, la validación de los términos y los datos enviados (versión e idioma de cada
  documento) no cambian y sus tests previos pasan, salvo los de los desplegables, que se sustituyen; suite
  verde.
- [ ] T-014 Retirar los textos de los desplegables
  RF: RF-014 | Depende de: T-013 | Archivos: 3
  Archivos: `i18n/locales/en.ts`, `es.ts`, `pt-BR.ts`.
  Hecho cuando: `register.termsTitle` y `register.marketingTitle` ya no existen en ningún idioma, nada del
  código los usa y la paridad de claves sigue en verde; suite verde.
- [ ] T-015 Accesibilidad del registro con el modal abierto
  RF: RF-015 | Depende de: T-013 | Archivos: 1
  Archivos: `registration/a11y.test.tsx`.
  Hecho cuando: `axe` no halla violaciones en el registro con el modal de términos cerrado ni abierto;
  suite verde.

## Entregas
Rama de integración: feat/casilla-con-documento (los PR de las entregas van contra ella; ver `AGENTS.md`)

- E-01 El componente `DocumentModal` abre un documento en Markdown en un diálogo y se cierra con la «x», Escape
  y la cortina (se prueba con `pnpm --filter frontend test`; aún no se ve en el catálogo).
  Tareas: T-001, T-002, T-003, T-004 | Líneas estimadas: 382 | Rama: feat/casilla-con-documento-componente-modal
  Cómo probarlo: `pnpm --filter frontend test` (los 14 tests de `DocumentModal.test.tsx` y los de
  `dialogStub.test.ts`).
  Nota: E-01 medía 465 líneas con el catálogo; se dividió en E-01 y E-01b según `AGENTS.md`.
- E-01b Se puede abrir y cerrar el modal con un documento desde el catálogo.
  Tareas: T-005 | Líneas estimadas: 83 | Rama: feat/casilla-con-documento-modal
  Cómo probarlo: `pnpm --filter frontend dev`, abrir http://localhost:5173/ y, en la sección «Documento en un
  modal», abrir el documento y cerrarlo con la «x», Escape y la cortina.
- E-02 El modal tiene el aspecto de la guía y devuelve el foco al elemento que lo abrió.
  Tareas: T-006, T-016 | Líneas estimadas: 209 | Rama: feat/casilla-con-documento-aspecto-modal
  Cómo probarlo: `pnpm --filter frontend dev`, abrir http://localhost:5173/, abrir el documento de la sección
  «Documento en un modal» y comprobar la cortina, la caja negra, los enlaces azul grisáceo sin subrayado, la
  etiqueta de la casilla en blanco y que, al cerrarlo, el foco vuelve al botón que lo abrió.
  Nota: E-02 medía 425 líneas con la prueba en Chromium; se dividió en E-02 y E-02b según `AGENTS.md`.
- E-02b El modal se comprueba en un navegador real.
  Tareas: T-007 | Líneas estimadas: 216 | Rama: feat/casilla-con-documento-aspecto
  Cómo probarlo: `pnpm --filter frontend test:visual` (40 pruebas nuevas del modal, en claro y oscuro).
- E-03 La casilla con enlace abre el documento y se sincroniza con la casilla del modal (se prueba con
  `pnpm --filter frontend test`; aún no se ve en el catálogo).
  Tareas: T-008, T-009 | Líneas estimadas: 330 | Rama: feat/casilla-con-documento-casilla-enlace
  Cómo probarlo: `pnpm --filter frontend test` (los 21 tests de `DocumentCheckbox.test.tsx`).
  Nota: E-03 medía 670 líneas; se dividió en E-03 y E-03b según `AGENTS.md`.
- E-03b La casilla muestra su error y se revalida al cerrar, y el catálogo exhibe sus cuatro casos.
  Tareas: T-010, T-011 | Líneas estimadas: 340 | Rama: feat/casilla-con-documento-casilla
  Cómo probarlo: `pnpm --filter frontend dev`, abrir http://localhost:5173/ y, en la sección «Casillas con
  documento», marcar desde el modal, cerrarlo y ver que la casilla de fuera sigue marcada; el caso con error se
  revalida al cerrar.
- E-04 El registro usa la casilla con documento para los términos y el marketing.
  Tareas: T-012, T-013, T-014, T-015 | Líneas estimadas: 250 | Rama: feat/casilla-con-documento-registro
  Cómo probarlo: `pnpm --filter frontend dev` con el backend levantado, abrir
  http://localhost:5173/register, pulsar el enlace de los términos, leerlos, marcar y cerrar.
  Nota: E-01 y E-03 rozan las 400 líneas; si una entrega ya implementada las rebasa, se divide en dos
  (E-XX y E-XXb) según `AGENTS.md`.

## RF sin tarea
Ninguno.
