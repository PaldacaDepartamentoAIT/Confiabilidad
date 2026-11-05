# Tareas: registro-diseno-visual
Estado: aprobado

Rutas relativas a `frontend/src/`, salvo que se indique otra. «Suite verde» =
`pnpm --filter frontend test` + `pnpm --filter frontend typecheck` + `pnpm lint` +
`prettier --check` sin errores. En cada tarea de código, antes de marcarla, se prueba al menos un
mutante del código que introduce, que debe hacer fallar sus tests (archivo de tests completo).
Los estilos de los componentes nuevos van en `styles/components.css` (M-15); los tests no procesan
ese CSS, así que lo visual se comprueba en la revisión manual de cada entrega.

## E-01 Barra superior con idioma

- [x] T-001 Guía visual ampliada
  RF: RF-022 (M-01, D-10, D-11, D-12, D-14) | Depende de: — | Archivos: 1
  Archivos: `docs/identidad-visual.md`.
  Hecho cuando: la guía describe la barra superior, el botón con menú, el indicador de pasos, el
  botón «?» y su globo, el selector propio, la ventana de documento (fondo, D-10), la zona de
  mensajes, el hueco de error, el asterisco (D-11), el radio de los campos (D-12), la transición
  entre pasos y el tema elegido; el usuario aprueba el texto (parada obligatoria: es una decisión de
  diseño que el plan deja abierta).
  Decisiones: indicador en relleno fuerte y no en color de acción (M-11 actualizado en el plan),
  fondo opaco de la ventana (D-10), asterisco y errores de campo en P1 (D-11) y radio de 4 px
  (D-12), elegidos por el usuario — [Cierto] — revertir: editar la sección «Componentes» de la guía.

- [x] T-002 Textos de la barra superior
  RF: RF-002, RF-003 (M-14) | Depende de: — | Archivos: 4
  Archivos: `i18n/locales/es.ts`, `i18n/locales/en.ts`, `i18n/locales/pt-BR.ts`,
  `i18n/locales/locales.test.ts`.
  Hecho cuando: existen `topBar.label`, `topBar.language`, `topBar.theme`, `topBar.light` y
  `topBar.dark` en los tres idiomas y `locales.test.ts` sigue en verde (mismas claves en todos);
  suite verde.
  Excepción: `i18n/locales/locales.test.ts` fija la lista de grupos de textos y debe cambiar con
  cada grupo nuevo (aprobado por el usuario al implementar T-002).
  Decisiones: además de las claves previstas, `topBar.themeLabel` («Tema») para nombrar el menú de
  tema, como `language.label` nombra el de idioma — [Probable] — revertir: borrar la clave.

- [x] T-003 Botón con menú
  RF: RF-005 (M-04, D-05) | Depende de: — | Archivos: 4
  Archivos: `components/MenuButton.tsx`, `components/MenuButton.test.tsx`,
  `styles/components.css` (nuevo, con los estilos del botón circular y el menú), `main.tsx`
  (importa `components.css`).
  Hecho cuando: los tests comprueban `aria-haspopup`, `aria-expanded`, `menuitemradio` con
  `aria-checked`; abrir con Intro, Espacio y flecha abajo con el foco en la opción marcada;
  recorrer con flechas, Inicio y Fin; elegir con Intro, Espacio y clic (cierra y llama a
  `onSelect`); Escape cierra sin elegir y devuelve el foco al botón; Tab, clic fuera y foco fuera
  cierran sin elegir; con dos menús, abrir el segundo cierra el primero; suite verde.
  Excepción: `components.css` nace aquí y hay que importarlo una vez en `main.tsx`; separar la
  importación dejaría un archivo de estilos sin cargar.
  Decisiones: el menú se cierra solo con `focusout` (sin escucha de clics en el documento ni rama
  para Tab): con el menú abierto el foco está siempre en una opción, y un clic fuera, Tab o mover
  el foco lo sacan — [Probable] — revertir: añadir un escucha de `mousedown` en el documento. El
  clic en el botón también abre con el foco en la opción marcada, como el teclado — [Probable] —
  revertir: abrir sin mover el foco.

- [x] T-004 Menú de idioma
  RF: RF-002 (M-05, D-05) | Depende de: T-002, T-003 | Archivos: 2
  Archivos: `components/LanguageSwitcher.tsx` → `components/LanguageMenu.tsx`,
  `components/LanguageSwitcher.test.tsx` → `components/LanguageMenu.test.tsx` (renombrados).
  Hecho cuando: el botón muestra «ES», «EN» o «PT» y su nombre accesible incluye el idioma activo;
  el menú lista «Español», «Português (Brasil)» y «English» con su `lang` y la activa marcada;
  elegir una cambia el idioma sin recargar, la guarda (RF-005 de `componentes-base-accesibles`),
  cierra el menú, deja el foco en el botón y conserva lo escrito en un campo; recorrer con las
  flechas no cambia el idioma; suite verde.
  Decisiones: `LanguageMenu` se crea como archivo nuevo y `LanguageSwitcher` se borra en T-006, en
  lugar de renombrarlo aquí: renombrar rompía las cuatro pantallas que lo importan y dejaba este
  commit en rojo. El diff de la entrega es el mismo — [Cierto] — revertir: no aplica. El nombre
  accesible del botón es «Idioma: Español (ES)», con la abreviatura visible dentro (WCAG 2.5.3) —
  [Probable] — revertir: pasar solo el nombre del idioma a `topBar.language`.

- [x] T-005 Barra superior en toda la aplicación
  RF: RF-001 (M-05) | Depende de: T-004 | Archivos: 3
  Archivos: `components/TopBar.tsx`, `App.tsx`, `App.test.tsx`.
  Hecho cuando: en `/`, `/register`, `/register/continue` y `/register/done` hay un único
  `<header>` con el menú de idioma, fuera de `<main>`; suite verde.

- [ ] T-006 Las pantallas dejan de pintar su selector
  RF: RF-001 (M-05) | Depende de: T-005 | Archivos: 4
  Archivos: `registration/RegisterPage.tsx`, `registration/VerifyPage.tsx`,
  `registration/DonePage.tsx`, `showcase/ShowcasePage.tsx`.
  Hecho cuando: ninguna pantalla importa el selector de idioma ni recibe `storage` solo para él;
  los tests de las pantallas y de accesibilidad siguen en verde con la barra de `App`; suite verde.
  Excepción: es la retirada del mismo componente en las cuatro pantallas que lo usan; dividirla
  dejaría pantallas con dos selectores de idioma en la rama.

## E-02 Tema claro y oscuro

- [ ] T-007 Tema guardado y tema en uso
  RF: RF-003, RF-004 (M-03, D-13) | Depende de: — | Archivos: 2
  Archivos: `theme/theme.ts`, `theme/theme.test.ts`.
  Hecho cuando: se lee el tema guardado y uno no válido se borra y se ignora; elegir lo guarda y
  pone `data-theme` en `<html>`; con el almacenamiento bloqueado no falla; `useTheme` devuelve el
  elegido o, sin elección, el de `matchMedia`, y se actualiza cuando cambia el del sistema; suite
  verde.

- [ ] T-008 Paleta oscura por elección o por sistema
  RF: RF-003, RF-004 (M-03) | Depende de: — | Archivos: 2
  Archivos: `styles/tokens.css`, `styles/tokens.test.ts`.
  Hecho cuando: el test comprueba que la paleta oscura está bajo `:root[data-theme="dark"]` y bajo
  `@media (prefers-color-scheme: dark)` con `:root:not([data-theme="light"])`, con los mismos
  valores; suite verde.

- [ ] T-009 Tema aplicado antes del primer pintado
  RF: RF-004 (M-03, D-04) | Depende de: T-007 | Archivos: 2
  Archivos: `frontend/index.html`, `theme/initialTheme.test.ts`.
  Hecho cuando: el test ejecuta el script en línea de `index.html` en jsdom y comprueba que pone
  `data-theme="dark"` o `"light"` según lo guardado, que no pone nada sin valor o con uno no válido
  y que no falla con el almacenamiento bloqueado; el script está antes de la carga de estilos y usa
  la misma clave que `theme.ts`; suite verde.

- [ ] T-010 Menú de tema
  RF: RF-003 (M-02, M-05) | Depende de: T-002, T-003, T-007 | Archivos: 3
  Archivos: `components/ThemeMenu.tsx`, `components/ThemeMenu.test.tsx`, `components/icons.tsx`
  (nuevo: sol y luna).
  Hecho cuando: el botón muestra el sol con el tema claro en uso y la luna con el oscuro (también
  cuando viene del sistema); el menú ofrece «Claro» y «Oscuro» con el activo marcado; elegir aplica
  el tema, lo guarda, cierra el menú, deja el foco en el botón y conserva lo escrito; suite verde.

- [ ] T-011 Tema en la barra superior
  RF: RF-001, RF-003 (M-05) | Depende de: T-005, T-010 | Archivos: 3
  Archivos: `components/TopBar.tsx`, `App.test.tsx`, `styles/components.css`.
  Hecho cuando: la barra de todas las pantallas tiene el menú de idioma y el de tema; suite verde.

## E-03 Campos con hueco de error, ojo y zona de mensajes

- [ ] T-012 Envoltorio de campo
  RF: RF-013, RF-016 (M-06, D-09) | Depende de: — | Archivos: 3
  Archivos: `components/fields/FieldShell.tsx`, `components/fields/FieldShell.test.tsx`,
  `styles/components.css`.
  Hecho cuando: el nombre va antes del control con el asterisco `aria-hidden` en los obligatorios;
  el hueco del error existe siempre, vacío sin error y con el mensaje con error; la ayuda visible y
  el error se unen en `aria-describedby`; hay una ranura para un control dentro del campo, a la
  derecha; suite verde.

- [ ] T-013 Texto, código y contraseña con el envoltorio
  RF: RF-013, RF-016 (M-06) | Depende de: T-012 | Archivos: 2
  Archivos: `components/fields/TextField.tsx`, `components/fields/TextField.test.tsx`.
  Hecho cuando: `TextField` (y con él `CodeField` y `PasswordField`) usa `FieldShell`; el hueco
  está presente con y sin error; los tests existentes de los tres siguen en verde; suite verde.

- [ ] T-014 Casilla y selector con el envoltorio
  RF: RF-016 (M-06) | Depende de: T-012 | Archivos: 3
  Archivos: `components/fields/Checkbox.tsx`, `components/fields/SelectField.tsx`,
  `components/fields/ChoiceFields.test.tsx`.
  Hecho cuando: la casilla y el selector tienen el hueco del error siempre presente, con y sin
  error; suite verde.

- [ ] T-015 Ojo dentro del campo de contraseña
  RF: RF-015, RF-018 (M-02, M-08) | Depende de: T-013 | Archivos: 3
  Archivos: `components/icons.tsx` (ojo, ojo tachado y la flecha abajo que usará T-027),
  `components/fields/PasswordField.tsx`,
  `components/fields/PasswordField.test.tsx`.
  Hecho cuando: el control está en la ranura interior del campo, con el ojo y `aria-pressed="false"`
  si la contraseña está oculta y el ojo tachado y `aria-pressed="true"` si está visible; el nombre
  accesible sigue siendo «Mostrar contraseña (<campo>)»; las reglas de la contraseña nueva siguen
  visibles; suite verde.

- [ ] T-016 Zona de mensajes
  RF: RF-023 (M-13) | Depende de: — | Archivos: 3
  Archivos: `components/MessageZone.tsx`, `components/MessageZone.test.tsx`,
  `styles/components.css`.
  Hecho cuando: la zona existe siempre, vacía o con sus hijos; suite verde.

- [ ] T-017 Mensajes del formulario y de la contraseña en la zona
  RF: RF-023 (M-13) | Depende de: T-016 | Archivos: 3
  Archivos: `registration/RegisterPage.tsx`, `registration/PasswordStep.tsx`,
  `registration/PasswordStep.test.tsx`.
  Hecho cuando: el mensaje general y el aviso de espera de las dos pantallas van en la zona,
  encima del botón principal, que existe también sin mensaje; los tests de `RegisterPage` y
  `PasswordStep` siguen en verde (mismo foco y anuncios); suite verde.

- [ ] T-018 Mensajes de la verificación en la zona
  RF: RF-023 (M-13) | Depende de: T-016 | Archivos: 2
  Archivos: `registration/VerifyPage.tsx`, `registration/VerifyPage.test.tsx`.
  Hecho cuando: el tiempo restante, el código caducado, el bloqueo, el aviso de espera y el
  mensaje general van en la zona, encima del botón de verificar; los tests de `VerifyPage` siguen
  en verde; suite verde.

## E-04 Ayuda «?» en los campos del registro

- [ ] T-019 Descripciones de los campos
  RF: RF-014 (M-14, S-03) | Depende de: — | Archivos: 4
  Archivos: `i18n/locales/es.ts`, `i18n/locales/en.ts`, `i18n/locales/pt-BR.ts`,
  `i18n/locales/locales.test.ts`.
  Hecho cuando: existen `help.label` y una descripción por campo (nombre, fecha, correo, país,
  código y contraseña) en los tres idiomas, con los textos en español del plan; suite verde.
  Excepción: `i18n/locales/locales.test.ts` fija la lista de grupos de textos y debe cambiar con
  cada grupo nuevo (aprobado por el usuario al implementar T-002).

- [ ] T-020 Botón «?» con globo
  RF: RF-014 (M-07, D-08) | Depende de: T-019 | Archivos: 3
  Archivos: `components/fields/HelpTip.tsx`, `components/fields/HelpTip.test.tsx`,
  `styles/components.css`.
  Hecho cuando: el botón se llama «Ayuda (<campo>)»; el globo `role="tooltip"` se muestra al pasar
  el puntero, al enfocar y al tocar, y se oculta al irse el puntero o el foco, al volver a tocar y
  con Escape; su texto está siempre en el DOM; suite verde.

- [ ] T-021 El campo lleva su «?» y lee su descripción
  RF: RF-014 (M-06, M-07) | Depende de: T-020, T-013 | Archivos: 3
  Archivos: `components/fields/FieldShell.tsx`, `components/fields/FieldShell.test.tsx`,
  `components/fields/TextField.tsx`.
  Hecho cuando: con `help`, el «?» va junto al nombre y la descripción entra en el
  `aria-describedby` del control junto a la ayuda visible y el error; sin `help`, no hay «?»;
  suite verde.

- [ ] T-022 «?» en el selector
  RF: RF-014 | Depende de: T-021, T-014 | Archivos: 2
  Archivos: `components/fields/SelectField.tsx`, `components/fields/ChoiceFields.test.tsx`.
  Hecho cuando: el selector acepta `help` como los demás campos; la casilla no lo acepta; suite
  verde.

- [ ] T-023 «?» en el formulario de registro
  RF: RF-014 | Depende de: T-022 | Archivos: 2
  Archivos: `registration/RegisterPage.tsx`, `registration/RegisterPage.test.tsx`.
  Hecho cuando: nombre, fecha, correo y país tienen su «?» con su descripción; las casillas no;
  suite verde.

- [ ] T-024 «?» en el código y la contraseña
  RF: RF-014, RF-015 | Depende de: T-021 | Archivos: 3
  Archivos: `registration/VerifyPage.tsx`, `registration/PasswordStep.tsx`,
  `registration/a11y.test.tsx`.
  Hecho cuando: el código y la contraseña tienen su «?»; la contraseña sigue mostrando sus reglas;
  la página de muestra no tiene ningún «?»; las auditorías de `axe-core` siguen en verde; suite
  verde.

## E-05 Selector propio

- [ ] T-025 Búsqueda al teclear
  RF: RF-017 (M-09) | Depende de: — | Archivos: 2
  Archivos: `forms/typeahead.ts`, `forms/typeahead.test.ts`.
  Hecho cuando: encuentra la primera opción que empieza por lo tecleado sin distinguir mayúsculas
  ni tildes («peru» → «Perú»), acumula las teclas en menos de 500 ms y vuelve a empezar después;
  repetir una misma letra recorre las opciones que empiezan por ella; suite verde.

- [ ] T-026 La validación lee un botón con valor
  RF: RF-017 (M-09, D-06) | Depende de: — | Archivos: 2
  Archivos: `forms/useFormValidation.ts`, `forms/useFormValidation.test.tsx`.
  Hecho cuando: `readValue` y `onBlur` aceptan un `<button name value>`, el envío lee su valor y,
  con error, le da el foco como al primer campo no válido; suite verde.

- [ ] T-027 Selector con lista propia
  RF: RF-017 (M-02, M-09) | Depende de: T-025, T-026, T-014, T-015 | Archivos: 3
  Archivos: `components/fields/SelectField.tsx`, `components/fields/ChoiceFields.test.tsx`,
  `styles/components.css` (la flecha abajo es la de `icons.tsx`, creada en T-015).
  Hecho cuando: no hay `<select>`; el control es un botón `role="combobox"` con `name` y `value`,
  `aria-expanded`, `aria-controls`, `aria-activedescendant`, `aria-required` y `aria-invalid`; la
  lista es `listbox` con `option` y `aria-selected`; abren Intro, Espacio, flecha abajo y
  Alt+flecha abajo; recorren las flechas, Inicio, Fin, Re Pág y Av Pág; teclear salta (T-025);
  Intro elige; Escape cierra sin cambios; Tab elige la resaltada y sale; el clic elige sin quitar
  el foco; al cerrar, el foco está en el control; suite verde.

- [ ] T-028 País con el selector propio
  RF: RF-017 | Depende de: T-027 | Archivos: 2
  Archivos: `registration/RegisterPage.tsx`, `registration/RegisterPage.test.tsx`.
  Hecho cuando: los tests de `RegisterPage` eligen el país con el selector nuevo (clic y teclado),
  el envío lleva el código del país, el error de país lleva el foco al selector; suite verde.

## E-06 Términos y marketing en ventana

- [ ] T-029 Textos de las casillas y de la ventana
  RF: RF-019, RF-020 (M-14) | Depende de: — | Archivos: 4
  Archivos: `i18n/locales/es.ts`, `i18n/locales/en.ts`, `i18n/locales/pt-BR.ts`,
  `i18n/locales/locales.test.ts`.
  Hecho cuando: `register.termsLabel` y `register.marketingLabel` llevan la marca `<doc>` alrededor
  del nombre del documento en los tres idiomas y existe `dialog.close`; suite verde.
  Excepción: `i18n/locales/locales.test.ts` fija la lista de grupos de textos y debe cambiar con
  cada grupo nuevo (aprobado por el usuario al implementar T-002).

- [ ] T-030 Ventana de documento
  RF: RF-021 (M-10, D-07) | Depende de: T-029 | Archivos: 3
  Archivos: `components/DocumentDialog.tsx`, `components/DocumentDialog.test.tsx`,
  `setupTests.ts` (sustituto de `showModal` y `close` en jsdom).
  Hecho cuando: se abre con su título y el Markdown; se cierra con su botón, con Escape y con un
  clic en el fondo, y no con un clic dentro; al cerrar, el foco vuelve a quien la abrió; suite
  verde.

- [ ] T-031 Casillas con enlace a su documento
  RF: RF-019, RF-020, RF-021 (M-10) | Depende de: T-030 | Archivos: 3
  Archivos: `registration/RegisterPage.tsx`, `registration/RegisterPage.test.tsx`,
  `styles/components.css`.
  Hecho cuando: no queda ningún `<details>`; la casilla de términos dice «Acepto los términos y
  condiciones *» con «términos y condiciones» como botón con aspecto de enlace que abre la ventana
  sin marcar la casilla; con marketing vigente, su casilla igual y sin asterisco; sin marketing,
  no hay casilla; lo escrito se conserva al cerrar la ventana; suite verde.

## E-07 Asistente con indicador de pasos

- [ ] T-032 Textos de los pasos
  RF: RF-006 (M-14) | Depende de: — | Archivos: 4
  Archivos: `i18n/locales/es.ts`, `i18n/locales/en.ts`, `i18n/locales/pt-BR.ts`,
  `i18n/locales/locales.test.ts`.
  Hecho cuando: existen los nombres de los tres pasos, «Paso {{current}} de {{total}}: {{name}}»,
  «completado» y «pendiente», y el nombre accesible del indicador, en los tres idiomas; suite
  verde.
  Excepción: `i18n/locales/locales.test.ts` fija la lista de grupos de textos y debe cambiar con
  cada grupo nuevo (aprobado por el usuario al implementar T-002).

- [ ] T-033 Indicador de pasos
  RF: RF-006, RF-008 (M-11) | Depende de: T-032 | Archivos: 3
  Archivos: `registration/StepIndicator.tsx`, `registration/StepIndicator.test.tsx`,
  `styles/components.css`.
  Hecho cuando: con `current` 1, 2 y 3 el actual tiene `aria-current="step"`, los anteriores el
  check y «completado» y los siguientes su número y «pendiente», y se lee «Paso N de 3: <nombre>»;
  con `"done"` los tres están completados y ninguno es el actual; suite verde.

- [ ] T-034 Botón principal con flecha
  RF: RF-012 (M-02, M-12) | Depende de: — | Archivos: 3
  Archivos: `components/Button.tsx`, `components/Button.test.tsx`, `components/icons.tsx`
  (flecha derecha).
  Hecho cuando: con `icon="next"` el botón pinta la flecha tras el texto, `aria-hidden`, y su
  nombre accesible es solo el texto; `variant="secondary"` cambia solo el aspecto; suite verde.

- [ ] T-035 Armazón del asistente
  RF: RF-006, RF-007 (M-12, M-15) | Depende de: T-033 | Archivos: 3
  Archivos: `registration/RegistrationLayout.tsx`, `registration/RegistrationLayout.test.tsx`,
  `styles/base.css` (`.card` y la zona de contenido; `main`, `form` y `section` sin fondo).
  Hecho cuando: el armazón pinta el indicador con el paso que fija la pantalla por contexto y la
  zona de contenido; cambiar el paso actualiza el indicador hacia delante y hacia atrás; suite
  verde.

- [ ] T-036 Rutas del registro dentro del armazón
  RF: RF-007, RF-008 (M-12) | Depende de: T-035 | Archivos: 2
  Archivos: `App.tsx`, `App.test.tsx`.
  Hecho cuando: `/register`, `/register/continue` y `/register/done` se pintan dentro del armazón
  y `/` no; suite verde.

- [ ] T-037 Formulario y cuenta creada como pasos
  RF: RF-007, RF-008, RF-012 (M-12) | Depende de: T-034, T-036 | Archivos: 3
  Archivos: `registration/RegisterPage.tsx`, `registration/DonePage.tsx`,
  `registration/RegisterPage.test.tsx`.
  Hecho cuando: el formulario fija el paso 1 y la cuenta creada `"done"`; cada uno tiene su `<h1>`
  enfocable con `tabIndex={-1}` y su tarjeta; el formulario tiene un único botón principal con
  flecha y ninguno de volver; suite verde.

- [ ] T-038 Verificación y contraseña como pasos
  RF: RF-007, RF-012 (M-12) | Depende de: T-034, T-036 | Archivos: 3
  Archivos: `registration/VerifyPage.tsx`, `registration/PasswordStep.tsx`,
  `registration/VerifyPage.test.tsx`.
  Hecho cuando: la verificación fija el paso 2 y la contraseña el 3, y un rechazo del código vuelve
  al 2; la contraseña tiene su propio `<h1>` y no muestra el título ni el texto de la verificación;
  el enlace no válido muestra el paso 2; el botón principal lleva flecha y el de reenvío es
  secundario; suite verde.

## E-08 Transición lateral entre pasos

- [ ] T-039 Transición entre pasos
  RF: RF-009, RF-010, RF-011 (M-12, D-01, D-02) | Depende de: — | Archivos: 2
  Archivos: `registration/stepTransition.ts`, `registration/stepTransition.test.ts`.
  Hecho cuando: con `element.animate` simulado, la copia del paso saliente queda encima con `inert`
  y `aria-hidden`, sale hacia la izquierda y el nuevo entra desde la derecha al avanzar (al revés
  al retroceder), y la copia se quita al terminar; sin `animate` o con movimiento reducido, el
  cambio se aplica sin animar y sin copia; el foco va al `<h1>` nuevo salvo que ya esté dentro del
  contenido nuevo; suite verde.

- [ ] T-040 El armazón anima los cambios de paso y «Atrás»
  RF: RF-007, RF-009 (M-12, D-03) | Depende de: T-039, T-035 | Archivos: 2
  Archivos: `registration/RegistrationLayout.tsx`, `registration/RegistrationLayout.test.tsx`.
  Hecho cuando: `goTo(direction, update)` ejecuta la transición sobre la zona de contenido; un
  `popstate` copia el paso antes de que el enrutador vuelva a pintar y anima hacia atrás; el
  indicador no se desplaza; suite verde.

- [ ] T-041 Los pasos cambian con transición
  RF: RF-007, RF-009, RF-011 (M-12) | Depende de: T-040, T-037, T-038 | Archivos: 3
  Archivos: `registration/RegisterPage.tsx`, `registration/VerifyPage.tsx`,
  `registration/flow.test.tsx` (nuevo).
  Hecho cuando: el recorrido formulario → verificación → contraseña → cuenta creada anima hacia
  delante, contraseña → verificación por rechazo y «Atrás» desde la verificación animan hacia
  atrás; en cada cambio el foco termina en el `<h1>` del paso nuevo (o en el error, según RF-003 y
  RF-011 de `registro-flujo`) y no queda nada enfocable del anterior; suite verde.

- [ ] T-042 Auditoría de accesibilidad en ambos temas
  RF: RF-022 (CF-2) | Depende de: T-041 | Archivos: 2
  Archivos: `registration/a11y.test.tsx`, `showcase/a11y.test.tsx`.
  Hecho cuando: `axe-core` no encuentra fallos en cada paso, con un menú abierto, el selector
  desplegado, el globo visible y la ventana abierta, con `data-theme="light"` y `"dark"`; suite
  verde.

- [ ] T-043 Revisión manual de la feature
  RF: RF-010, RF-016, RF-022 (CF-3, CF-4) | Depende de: T-041 | Archivos: 1
  Archivos: `specs/registro-diseno-visual/HUMAN_TODO.md`.
  Hecho cuando: el archivo tiene la lista de comprobación del recorrido solo con teclado y de la
  revisión visual en ambos temas, tres idiomas, con y sin movimiento reducido, en el navegador y en
  la app de escritorio, con los comandos para levantarlo.

## Entregas
Rama de integración: `feat/registro-diseno-visual` (los PR de las entregas van contra ella; ver
`AGENTS.md`).

- E-01 La barra superior aparece en todas las pantallas y cambia el idioma desde su menú
  Tareas: T-001…T-006 | Líneas estimadas: 400 | Rama: `feat/registro-diseno-visual-barra-idioma`
  Cómo probarlo: levantar el frontend, abrir `/register`, pulsar «ES» y elegir «English» con el
  ratón y con el teclado; el menú se cierra con Escape y al hacer clic fuera.

- E-02 El tema se elige desde la barra, se recuerda y no parpadea al recargar
  Tareas: T-007…T-011 | Líneas estimadas: 330 | Rama: `feat/registro-diseno-visual-tema`
  Cómo probarlo: elegir «Oscuro» con el sol y recargar: la página sale oscura desde el primer
  instante y el botón muestra la luna; borrar `confiabilidad.theme` en el almacenamiento del
  navegador y cambiar el tema del sistema operativo: la página lo sigue.

- E-03 Los campos tienen el nombre arriba, el error no los mueve y la contraseña se muestra con un
  ojo
  Tareas: T-012…T-018 | Líneas estimadas: 360 | Rama: `feat/registro-diseno-visual-campos`
  Cómo probarlo: en `/register`, salir de un campo vacío y ver que el error aparece sin mover el
  resto; en la contraseña, pulsar el ojo.

- E-04 Cada campo del registro tiene su «?» con una descripción
  Tareas: T-019…T-024 | Líneas estimadas: 300 | Rama: `feat/registro-diseno-visual-ayuda`
  Cómo probarlo: pasar el puntero, tabular y tocar el «?» de cada campo del registro.

- E-05 El país se elige en una lista propia con flecha que gira
  Tareas: T-025…T-028 | Líneas estimadas: 470 | Rama: `feat/registro-diseno-visual-selector`
  Cómo probarlo: en `/register`, abrir el país con el ratón y con el teclado, teclear «pe» y elegir
  con Intro.
  Excepción: el patrón de combobox no se puede partir sin dejar en la rama un selector con el
  teclado incompleto, peor que el `<select>` nativo al que sustituye.

- E-06 Los términos y el marketing se leen en una ventana desde su casilla
  Tareas: T-029…T-031 | Líneas estimadas: 260 | Rama: `feat/registro-diseno-visual-documentos`
  Cómo probarlo: en `/register`, pulsar «términos y condiciones», desplazar el texto y cerrar con
  Escape, con el botón y haciendo clic fuera; la casilla no cambia.

- E-07 El registro se ve como un asistente de tres pasos con su indicador
  Tareas: T-032…T-038 | Líneas estimadas: 420 | Rama: `feat/registro-diseno-visual-indicador`
  Cómo probarlo: completar un registro de extremo a extremo (con el backend levantado y el código
  del correo de desarrollo) y ver el indicador en 1, 2, 3 y completado.
  Excepción: reorganizar las cuatro pantallas dentro del armazón cambia sus tests a la vez; partirlo
  dejaría pantallas fuera del asistente y otras dentro en la rama.

- E-08 Los pasos cambian deslizándose sin recargar
  Tareas: T-039…T-043 | Líneas estimadas: 330 | Rama: `feat/registro-diseno-visual-transicion`
  Cómo probarlo: repetir el registro y ver el desplazamiento al avanzar, al rechazar el código en
  la contraseña y con «Atrás»; activar «reducir movimiento» en el sistema y ver que cambia sin
  animar.

## RF sin tarea
Ninguno.
