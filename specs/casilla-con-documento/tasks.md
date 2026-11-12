# Tareas: casilla-con-documento
Estado: aprobado

«Suite verde» = `pnpm --filter frontend test:coverage` (líneas ≥ 80 %), `typecheck`, `lint` y
`exec prettier --check .` sin errores, y, desde T-007, también `pnpm --filter frontend test:visual`.
En cada tarea se prueba al menos un mutante del código que introduce y debe hacer fallar sus tests.
Las rutas son relativas a `frontend/src/` salvo que se indique otra cosa.

## E-01 Modal de documento
- [ ] T-001 Doble de `<dialog>` para los tests de jsdom
  RF: RF-008 | Depende de: — | Archivos: 2
  Archivos: `setupTests.ts`, `dialogStub.test.ts`.
  Hecho cuando: en jsdom, `showModal()` pone el atributo `open`, `close()` lo quita y emite `close`, y
  `dialogStub.test.ts` lo comprueba; suite verde.
- [ ] T-002 Texto de «Cerrar» del modal en tres idiomas
  RF: RF-014 | Depende de: — | Archivos: 3
  Archivos: `i18n/locales/en.ts`, `es.ts`, `pt-BR.ts`.
  Hecho cuando: existe `documentModal.close` en `es`, `pt-BR` y `en` y `keys.test.ts` y `locales.test.ts`
  (paridad de claves) siguen en verde.
- [ ] T-003 Modal: estructura, documento y nombre accesible
  RF: RF-002, RF-003, RF-008 | Depende de: T-001, T-002 | Archivos: 3
  Archivos: `components/DocumentModal.tsx`, `DocumentModal.css`, `DocumentModal.test.tsx`.
  Hecho cuando: `DocumentModal` abierto muestra, fuera del formulario (portal), un diálogo con nombre
  accesible, con la «x», el documento en Markdown con sus enlaces abiertos en pestaña nueva
  (`target="_blank"` y `rel="noopener noreferrer"`) y un pie con lo que reciba, en ese orden; cerrado,
  no pinta nada; el aspecto mínimo (caja negra de la guía) ya está; suite verde.
- [ ] T-004 Modal: cierre por «x», Escape y cortina
  RF: RF-006 | Depende de: T-003 | Archivos: 3
  Archivos: `components/DocumentModal.tsx`, `DocumentModal.css`, `DocumentModal.test.tsx`.
  Hecho cuando: la «x», la tecla Escape y un clic en la cortina llaman a `onClose`, y un clic dentro de
  la caja no; el modal no se cierra solo por otros motivos; suite verde.
- [ ] T-005 Catálogo: modal de ejemplo
  RF: RF-013 | Depende de: T-004 | Archivos: 3
  Archivos: `showcase/sections/DocumentSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo tiene una sección con un botón que abre el modal con un documento de ejemplo
  (con títulos, listas y un enlace) y una casilla en el pie, y se cierra por sus tres vías; suite verde.

## E-02 Aspecto del modal y prueba en navegador
- [ ] T-006 Aspecto del modal según la guía
  RF: RF-002, RF-007, RF-009 | Depende de: T-004 | Archivos: 3
  Archivos: `components/DocumentModal.css`, `components/documentModalCss.test.ts`,
  `docs/identidad-visual.md`.
  Hecho cuando: la cortina es `::backdrop` negro al 50 %; la caja usa `--black-fill` con texto blanco y
  borde de 1 px de línea; mide 640 px como máximo y `min(80 dvh, 100 dvh − 32 px)` de alto, con el ancho
  completo menos 32 px por debajo de 700 px; solo el contenido se desplaza; la página de detrás no se
  desplaza (`body:has(dialog[open])`); aparece con un fundido de 0,2 s; los enlaces del documento son
  `#7f94b5` sin subrayado; `docs/identidad-visual.md` recoge estas medidas en filas nuevas; el test lee
  el CSS y las comprueba; suite verde.
- [ ] T-007 Prueba del modal en Chromium
  RF: RF-002, RF-006, RF-007, RF-009, RF-015, RF-016 | Depende de: T-005, T-006 | Archivos: 1
  Archivos: `frontend/visual/document-modal.visual.test.ts`.
  Hecho cuando: en Chromium, en claro y oscuro, el catálogo abre el modal; Tab no sale de él; la página
  de detrás no se desplaza; se cierra por «x», Escape y cortina devolviendo el foco al botón que lo abrió;
  la caja mide 640 px (y ancho completo menos 32 px a 600 px de ancho) y no pasa del 80 % del alto; al
  cambiar el tamaño de la ventana se recalcula con el modal abierto; `axe` (con contraste) no halla
  violaciones con el modal abierto, incluido el enlace de `#7f94b5`; `pnpm --filter frontend test:visual`
  pasa.

## E-03 Casilla con documento
- [ ] T-008 Casilla con enlace al documento
  RF: RF-001, RF-010 | Depende de: T-004 | Archivos: 3
  Archivos: `components/fields/DocumentCheckbox.tsx`, `DocumentCheckbox.css`, `DocumentCheckbox.test.tsx`.
  Hecho cuando: con documento, el texto de la casilla es un enlace (`aria-haspopup="dialog"`) que abre el
  modal sin cambiar la casilla; pulsar el cuadro la marca sin abrir el modal; pulsar el hueco de la fila no
  hace nada; la casilla se nombra con el texto del enlace y no está envuelta en `<label>`; sin contenido
  es una casilla normal sin enlace; suite verde.
- [ ] T-009 Casilla del modal sincronizada
  RF: RF-004, RF-005 | Depende de: T-008 | Archivos: 3
  Archivos: `components/fields/DocumentCheckbox.tsx`, `DocumentCheckbox.css`, `DocumentCheckbox.test.tsx`.
  Hecho cuando: el pie del modal lleva una casilla con el mismo texto (y el asterisco si es obligatoria,
  sin ayuda ni error) cuyo texto sí la marca; marcar o desmarcar una refleja el estado en la otra; el modal
  sigue abierto al hacerlo; la casilla del modal no entra en los datos del formulario; suite verde.
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

- E-01 Se puede abrir y cerrar un modal con un documento desde el catálogo.
  Tareas: T-001, T-002, T-003, T-004, T-005 | Líneas estimadas: 390 | Rama: feat/casilla-con-documento-modal
  Cómo probarlo: `pnpm --filter frontend dev`, abrir http://localhost:5173/ y, en la sección del modal, abrir
  el documento y cerrarlo con la «x», Escape y la cortina.
- E-02 El modal tiene el aspecto de la guía y se comprueba en un navegador real.
  Tareas: T-006, T-007 | Líneas estimadas: 230 | Rama: feat/casilla-con-documento-aspecto
  Cómo probarlo: `pnpm --filter frontend test:visual`; en el catálogo, abrir el modal y comprobar que la
  página de detrás no se desplaza, que Tab no sale de él y que se adapta a una ventana estrecha.
- E-03 La casilla con enlace abre el documento y se sincroniza con la del modal.
  Tareas: T-008, T-009, T-010, T-011 | Líneas estimadas: 390 | Rama: feat/casilla-con-documento-casilla
  Cómo probarlo: `pnpm --filter frontend dev`, abrir http://localhost:5173/ y, en la sección de casillas
  con documento, marcar desde el modal, cerrarlo y ver que la casilla de fuera sigue marcada; el caso con
  error se revalida al cerrar.
- E-04 El registro usa la casilla con documento para los términos y el marketing.
  Tareas: T-012, T-013, T-014, T-015 | Líneas estimadas: 250 | Rama: feat/casilla-con-documento-registro
  Cómo probarlo: `pnpm --filter frontend dev` con el backend levantado, abrir
  http://localhost:5173/register, pulsar el enlace de los términos, leerlos, marcar y cerrar.
  Nota: E-01 y E-03 rozan las 400 líneas; si una entrega ya implementada las rebasa, se divide en dos
  (E-XX y E-XXb) según `AGENTS.md`.

## RF sin tarea
Ninguno.
