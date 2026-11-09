# Tareas: sistema-de-diseno
Estado: borrador

Rutas relativas a `frontend/src/` salvo que se indique. Los tests van junto al archivo que prueban.
«Suite verde» = `pnpm --filter frontend test:coverage` (líneas ≥ 80 %), `typecheck`, `lint` y
`exec prettier --check .` sin errores. En cada tarea se prueba al menos un mutante del código que
introduce y debe hacer fallar sus tests. Cada pieza lleva en su elemento raíz el `data-ui` de las
referencias (`docs/referencia/README.md`) y usa los nombres de clase y medidas de esas páginas (D-01).
Las tareas de «Catálogo» añaden una sección en `showcase/sections/` y la registran en
`showcase/ShowcasePage.tsx`. Las reglas de elementos sueltos de `base.css` se conservan como
transitorias hasta T-051 (D-12).

## E-01 Paleta Pizarra
- [ ] T-001 Tokens v2 y base transitoria
  RF: RF-001, RF-004, RF-029 | Depende de: — | Archivos: 3
  Archivos: `styles/tokens.css`, `styles/tokens.test.ts`, `styles/base.css`.
  Hecho cuando: `tokens.test.ts` compara cada variable con las tablas claro y oscuro de la guía
  (falla al cambiar un valor) y comprueba la regla de movimiento reducido; ya no existe ningún
  `--color-*`; `base.css` usa los tokens nuevos; suite verde; la página de muestra se ve en Pizarra
  con `pnpm --filter frontend dev`.

## E-02 Tema con botón
- [ ] T-002 Módulo de tema
  RF: RF-001, RF-003 | Depende de: T-001 | Archivos: 2
  Archivos: `theme/theme.ts`, `theme/theme.test.ts`.
  Hecho cuando: sin valor guardado devuelve el tema del sistema; con `light` u `oscuro-inválido` se
  ignora y se borra; `toggle` guarda y aplica `data-theme` en `<html>`; suite verde.
- [ ] T-003 Textos del tema en tres idiomas
  RF: RF-030 | Depende de: T-001 | Archivos: 3
  Archivos: `i18n/locales/en.ts`, `es.ts`, `pt-BR.ts`.
  Hecho cuando: existen `theme.light`, `theme.dark` y `theme.toggle` en los tres idiomas y
  `locales.test.ts` y `keys.test.ts` pasan; suite verde.
  Excepción: los tres archivos son una unidad (`es` y `pt-BR` se tipan contra `en`).
- [ ] T-004 Botón de tema
  RF: RF-002 | Depende de: T-002, T-003 | Archivos: 3
  Archivos: `theme/ThemeButton.tsx`, `ThemeButton.css`, `ThemeButton.test.tsx`.
  Hecho cuando: pulsarlo alterna el tema, cambia su icono y etiqueta, anuncia el estado al lector
  y pasa `axe-core`; suite verde.
- [ ] T-005 Aplicar el tema al arrancar y mostrar el botón
  RF: RF-001, RF-002, RF-027 | Depende de: T-004 | Archivos: 3
  Archivos: `main.tsx`, `showcase/ShowcasePage.tsx`, `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: la página de muestra tiene el botón y el tema elegido sobrevive a recargar; suite
  verde.

## E-03 Bloques, chips y formas
- [ ] T-006 `lucide-react` y módulo de iconos
  RF: RF-020 | Depende de: — | Archivos: 4
  Archivos: `frontend/package.json`, `pnpm-lock.yaml`, `icons/index.ts`, `icons/icons.test.ts`.
  Hecho cuando: `lucide-react` está en `dependencies`; el módulo reexporta por nombre los iconos
  de la guía a 16 px y trazo 2; suite verde.
  Excepción: `pnpm-lock.yaml` lo regenera `pnpm add`.
- [ ] T-007 Formas de alarma
  RF: RF-020, RF-025 | Depende de: T-006 | Archivos: 2
  Archivos: `icons/shapes.tsx`, `icons/shapes.test.tsx`.
  Hecho cuando: P1 es un cuadrado, P2 un triángulo, advertencia un rombo y neutro un cuadrado
  vacío, con nombre accesible y sin depender del color; suite verde.
- [ ] T-008 Bloque
  RF: RF-014 | Depende de: T-001 | Archivos: 3
  Archivos: `components/Block.tsx`, `Block.css`, `Block.test.tsx`.
  Hecho cuando: variantes normal, destacado y en alerta, con cabecera opcional (título, contador,
  acciones); suite verde.
- [ ] T-009 Chip
  RF: RF-023 | Depende de: T-001 | Archivos: 3
  Archivos: `components/Chip.tsx`, `Chip.css`, `Chip.test.tsx`.
  Hecho cuando: renderiza el texto en el chip de la guía y pasa `axe-core`; suite verde.
- [ ] T-010 Catálogo: bloques, chips y formas
  RF: RF-027 | Depende de: T-007, T-008, T-009 | Archivos: 3
  Archivos: `showcase/sections/BlocksSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: la página de muestra exhibe las tres variantes de bloque, chips y las cuatro
  formas en ambos temas; suite verde.

## E-04 Botón y avisos
- [ ] T-011 Botón restilizado
  RF: RF-018 | Depende de: T-001 | Archivos: 3
  Archivos: `components/Button.tsx`, `Button.css`, `Button.test.tsx`.
  Hecho cuando: variantes principal y secundario con hover, foco y procesando de la guía; los
  tests previos de `Button` siguen pasando; suite verde.
- [ ] T-012 Aviso
  RF: RF-019 | Depende de: T-006 | Archivos: 3
  Archivos: `components/Notice.tsx`, `Notice.css`, `Notice.test.tsx`.
  Hecho cuando: borde izquierdo de 4 px, icono e interlineado de la guía; suite verde.
- [ ] T-013 Aviso de alarma
  RF: RF-019, RF-020 | Depende de: T-007, T-011 | Archivos: 3
  Archivos: `components/AlarmNotice.tsx`, `AlarmNotice.css`, `AlarmNotice.test.tsx`.
  Hecho cuando: muestra la forma de su prioridad, título, texto y una acción opcional; suite verde.
- [ ] T-014 Catálogo: botones y avisos
  RF: RF-027 | Depende de: T-012, T-013 | Archivos: 3
  Archivos: `showcase/sections/ButtonsSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe botones y avisos en todos sus estados; suite verde.

## E-05 Campos de texto y casilla
- [ ] T-015 Campo de texto restilizado
  RF: RF-015 | Depende de: T-006 | Archivos: 3
  Archivos: `components/fields/TextField.tsx`, `fields/field.css`, `TextField.test.tsx`.
  Hecho cuando: borde de 1 px al pasar el cursor, de 2 px con foco sin mover el contenido y error
  con icono; los tests previos de `TextField` siguen pasando; suite verde.
- [ ] T-016 Contraseña, código y leyenda de obligatorios
  RF: RF-015 | Depende de: T-015 | Archivos: 3
  Archivos: `components/fields/PasswordField.tsx`, `CodeField.tsx`, `RequiredLegend.tsx`.
  Hecho cuando: usan las clases de `field.css`; los tests previos de ambos campos siguen pasando
  sin cambios; suite verde.
- [ ] T-017 Casilla de verificación
  RF: RF-017 | Depende de: T-006 | Archivos: 3
  Archivos: `components/fields/Checkbox.tsx`, `Checkbox.css`, `Checkbox.test.tsx`.
  Hecho cuando: icono de verificación centrado, etiqueta y ayuda opcional; suite verde.
- [ ] T-018 Catálogo: campos
  RF: RF-027 | Depende de: T-016, T-017 | Archivos: 3
  Archivos: `showcase/sections/FieldsSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe campos, error y casilla; suite verde.

## E-06 Menú desplegable y botón de idioma
- [ ] T-019 Menú desplegable compartido
  RF: RF-011, RF-016 | Depende de: T-001 | Archivos: 3
  Archivos: `components/menu/Menu.tsx`, `Menu.css`, `Menu.test.tsx`.
  Hecho cuando: abre con animación de 0,18 s, navega con flechas, Inicio y Fin, cierra con
  Escape y clic fuera y devuelve el foco al disparador; suite verde.
- [ ] T-020 Botón de idioma
  RF: RF-005, RF-007, RF-030 | Depende de: T-019 | Archivos: 3
  Archivos: `components/LanguageButton.tsx`, `LanguageButton.css`, `LanguageButton.test.tsx`.
  Hecho cuando: muestra el código del idioma activo, abre un menú con los tres idiomas por su
  nombre y cambia y guarda el idioma como `LanguageSwitcher`; suite verde.
- [ ] T-021 Catálogo: menú e idioma
  RF: RF-027 | Depende de: T-020 | Archivos: 3
  Archivos: `showcase/sections/MenuSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe el botón de idioma; suite verde.

## E-07 Selector propio
- [ ] T-022 Detección de puntero táctil
  RF: RF-031 | Depende de: — | Archivos: 2
  Archivos: `components/fields/useCoarsePointer.ts`, `useCoarsePointer.test.ts`.
  Hecho cuando: devuelve verdadero si `matchMedia("(pointer: coarse)")` coincide y reacciona a su
  cambio; suite verde.
- [ ] T-023 Selector propio
  RF: RF-016 | Depende de: T-015, T-019 | Archivos: 3
  Archivos: `components/fields/SelectField.tsx`, `SelectField.css`, `ChoiceFields.test.tsx`.
  Hecho cuando: el disparador `<button role="combobox" name value>` abre la lista, se maneja con
  Enter, Espacio, flechas, Inicio, Fin, Escape y escritura, marca la opción, muestra el error y
  anuncia valor y estado; `useFormValidation` lo lee y enfoca; suite verde con `RegisterPage`.
- [ ] T-024 Selector nativo en dispositivos táctiles
  RF: RF-031 | Depende de: T-022, T-023 | Archivos: 2
  Archivos: `components/fields/SelectField.tsx`, `ChoiceFields.test.tsx`.
  Hecho cuando: con puntero táctil se muestra el `<select>` nativo con la misma etiqueta, valor,
  opciones y error; suite verde.
- [ ] T-025 Catálogo: selector
  RF: RF-027 | Depende de: T-024 | Archivos: 3
  Archivos: `showcase/sections/FieldsSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe el selector con valor y con error; suite verde.

## E-08 Diseño público en el registro
- [ ] T-026 Diseño público
  RF: RF-005 | Depende de: T-004, T-020 | Archivos: 3
  Archivos: `layouts/PublicLayout.tsx`, `PublicLayout.css`, `PublicLayout.test.tsx`.
  Hecho cuando: barra de 64 px con nombre del sistema, botón de idioma y de tema, sin menú lateral;
  suite verde.
- [ ] T-027 Registro y acceso usan el diseño público
  RF: RF-026 | Depende de: T-026, T-011, T-016, T-023 | Archivos: 3
  Archivos: `registration/RegisterPage.tsx`, `VerifyPage.tsx`, `DonePage.tsx`.
  Hecho cuando: las tres pantallas se ven con el diseño público y los tests previos de registro
  siguen pasando sin cambios; suite verde.
- [ ] T-028 Página de muestra en el diseño público
  RF: RF-026, RF-027 | Depende de: T-026 | Archivos: 2
  Archivos: `showcase/ShowcasePage.tsx`, `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: la página de muestra usa `PublicLayout`; suite verde.

## E-09 Menú lateral
- [ ] T-029 Menú lateral
  RF: RF-007, RF-008 | Depende de: T-004, T-020 | Archivos: 3
  Archivos: `layouts/Sidebar.tsx`, `Sidebar.css`, `Sidebar.test.tsx`.
  Hecho cuando: recibe los elementos como datos, marca el activo, muestra contador, pie con tema,
  idioma y usuario (acción opcional) y contrae de 232 a 60 px con `aria-expanded` y «<»/«>»;
  suite verde.
- [ ] T-030 Catálogo: menú lateral
  RF: RF-027 | Depende de: T-029 | Archivos: 3
  Archivos: `showcase/sections/SidebarSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe el menú abierto y contraído; suite verde.

## E-10 Diseño con sesión y menú en pantallas pequeñas
- [ ] T-031 `useMediaQuery`
  RF: RF-009 | Depende de: — | Archivos: 2
  Archivos: `layouts/useMediaQuery.ts`, `useMediaQuery.test.ts`.
  Hecho cuando: devuelve y actualiza el resultado de una consulta; suite verde.
- [ ] T-032 Panel superpuesto del menú
  RF: RF-009 | Depende de: T-029, T-031 | Archivos: 3
  Archivos: `layouts/Sidebar.tsx`, `Sidebar.css`, `Sidebar.test.tsx`.
  Hecho cuando: bajo 768 px se oculta, se abre con velo, se cierra con velo, Escape o al elegir
  un elemento, sin estado contraído y devolviendo el foco al botón que lo abrió; suite verde.
- [ ] T-033 Diseño con sesión
  RF: RF-006 | Depende de: T-032 | Archivos: 3
  Archivos: `layouts/AppLayout.tsx`, `AppLayout.css`, `AppLayout.test.tsx`.
  Hecho cuando: compone menú, barra superior (hueco) y contenido con las medidas de la guía;
  suite verde.
- [ ] T-034 Catálogo: diseño con sesión
  RF: RF-027 | Depende de: T-033 | Archivos: 3
  Archivos: `showcase/sections/AppLayoutSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe una pantalla con sesión de ejemplo; suite verde.

## E-11 Barra superior
- [ ] T-035 Pestañas
  RF: RF-010 | Depende de: T-001 | Archivos: 3
  Archivos: `layouts/Tabs.tsx`, `Tabs.css`, `Tabs.test.tsx`.
  Hecho cuando: se manejan con flechas, Inicio y Fin, y la línea de 2 px se desplaza a la pestaña
  nueva en 0,25 s (medidas simuladas); suite verde.
- [ ] T-036 Buscador
  RF: RF-010 | Depende de: T-006, T-015 | Archivos: 3
  Archivos: `layouts/SearchBox.tsx`, `SearchBox.css`, `SearchBox.test.tsx`.
  Hecho cuando: campo de 220 × 36 px con lupa, solo visual (no filtra ni emite); suite verde.
- [ ] T-037 Barra superior
  RF: RF-010 | Depende de: T-035, T-036, T-033 | Archivos: 3
  Archivos: `layouts/TopBar.tsx`, `TopBar.css`, `TopBar.test.tsx`.
  Hecho cuando: pestañas a la izquierda y buscador a la derecha; `AppLayout` la usa; suite verde.
- [ ] T-038 Catálogo: barra superior
  RF: RF-027 | Depende de: T-037 | Archivos: 3
  Archivos: `showcase/sections/AppLayoutSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: la pantalla de ejemplo muestra la barra con pestañas; suite verde.

## E-12 Pestañas que no caben y cambio de sección
- [ ] T-039 Pestañas que no caben
  RF: RF-011 | Depende de: T-035, T-019 | Archivos: 3
  Archivos: `layouts/Tabs.tsx`, `Tabs.css`, `Tabs.test.tsx`.
  Hecho cuando: si no caben se desvanecen y aparece el selector con la pestaña activa que
  despliega las demás (medidas simuladas); suite verde.
- [ ] T-040 Cambio de sección con fundido
  RF: RF-013 | Depende de: T-035 | Archivos: 3
  Archivos: `layouts/TabPanel.tsx`, `TabPanel.css`, `TabPanel.test.tsx`.
  Hecho cuando: solo una sección es visible y la nueva aparece con fundido de 0,2 s; suite verde.
- [ ] T-041 Buscador reducido en pantallas pequeñas
  RF: RF-012 | Depende de: T-036, T-031 | Archivos: 3
  Archivos: `layouts/SearchBox.tsx`, `SearchBox.css`, `SearchBox.test.tsx`.
  Hecho cuando: bajo 560 px es un botón con lupa que despliega el campo sobre las pestañas y lo
  cierra con Escape; suite verde.
- [ ] T-042 Catálogo: pestañas completas
  RF: RF-027 | Depende de: T-039, T-040, T-041 | Archivos: 3
  Archivos: `showcase/sections/AppLayoutSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: la pantalla de ejemplo cambia de sección con fundido; suite verde.

## E-13 Indicadores y tabla
- [ ] T-043 Indicador y su rejilla
  RF: RF-021 | Depende de: T-008 | Archivos: 3
  Archivos: `components/data/Indicator.tsx`, `Indicator.css`, `Indicator.test.tsx`.
  Hecho cuando: variantes normal, destacado y en alerta (cifra en el color de la prioridad) y
  rejilla de 190 px mínimo; suite verde.
- [ ] T-044 Tabla
  RF: RF-022 | Depende de: T-007, T-009 | Archivos: 3
  Archivos: `components/data/Table.tsx`, `Table.css`, `Table.test.tsx`.
  Hecho cuando: columnas de texto, código y estado con icono de forma, desplazamiento horizontal y
  mensaje de vacío sin filas; suite verde.
- [ ] T-045 Catálogo: indicadores y tabla
  RF: RF-027 | Depende de: T-043, T-044 | Archivos: 3
  Archivos: `showcase/sections/DataSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe indicadores y tabla; suite verde.

## E-14 Gráfica de barras
- [ ] T-046 Escala de la gráfica
  RF: RF-024 | Depende de: — | Archivos: 2
  Archivos: `components/data/chartScale.ts`, `chartScale.test.ts`.
  Hecho cuando: el eje va de 0 al siguiente múltiplo de 30 (mínimo 30), el ancho de grupo se ajusta
  al número de grupos y los negativos o no numéricos se rechazan; suite verde.
- [ ] T-047 Gráfica de barras
  RF: RF-024 | Depende de: T-046 | Archivos: 3
  Archivos: `components/data/BarChart.tsx`, `BarChart.css`, `BarChart.test.tsx`.
  Hecho cuando: dibuja dos series, cuadrícula, ejes, leyenda y texto alternativo, escala al
  bloque y muestra el mensaje de vacío sin datos o con datos no válidos; suite verde.
- [ ] T-048 Catálogo: gráfica
  RF: RF-027 | Depende de: T-047 | Archivos: 3
  Archivos: `showcase/sections/DataSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe la gráfica; suite verde.

## E-15 Rejilla de estado y limpieza
- [ ] T-049 Rejilla de estado
  RF: RF-025 | Depende de: T-007 | Archivos: 3
  Archivos: `components/data/StatusGrid.tsx`, `StatusGrid.css`, `StatusGrid.test.tsx`.
  Hecho cuando: cuadros de 24 × 24 px con glifo de su forma, `title` y `aria-label`, y leyenda;
  suite verde.
- [ ] T-050 Catálogo: rejilla de estado
  RF: RF-027 | Depende de: T-049 | Archivos: 3
  Archivos: `showcase/sections/DataSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe todas las piezas de la feature; suite verde.
- [ ] T-051 Retirar las reglas transitorias de `base.css`
  RF: RF-001 | Depende de: T-050 | Archivos: 2
  Archivos: `styles/base.css`, `styles/tokens.test.ts`.
  Hecho cuando: `base.css` no estila `button`, `input`, `select`, `main`, `form` ni `section` y el
  test lo comprueba; las pantallas de registro y el catálogo se ven igual; suite verde.

## E-16 Comprobación visual
- [ ] T-052 Playwright y proyecto de test visual
  RF: RF-028 | Depende de: T-050 | Archivos: 4
  Archivos: `frontend/package.json`, `pnpm-lock.yaml`, `frontend/vitest.visual.config.ts`,
  `frontend/visual/smoke.visual.test.ts`.
  Hecho cuando: con tu permiso previo, `playwright` está en `devDependencies`, existe
  `test:visual` y la prueba abre el catálogo en Chromium; suite verde.
  Excepción: `pnpm-lock.yaml` lo regenera `pnpm add`. Se pide permiso antes de instalar.
- [ ] T-053 Comparación con las referencias
  RF: RF-028 | Depende de: T-052 | Archivos: 2
  Archivos: `frontend/visual/measure.ts`, `frontend/visual/compare.visual.test.ts`.
  Hecho cuando: compara con igualdad exacta las propiedades de RF-028 entre el catálogo y
  `docs/referencia/*.html` en claro y oscuro y falla al cambiar un valor de un componente
  (comprobado); `pnpm --filter frontend test:visual` pasa.
- [ ] T-054 Contraste y accesibilidad en ambos temas
  RF: RF-029 | Depende de: T-052 | Archivos: 2
  Archivos: `frontend/visual/contrast.visual.test.ts`, `frontend/visual/measure.ts`.
  Hecho cuando: `axe-core` no halla violaciones de contraste AA ni de accesibilidad en el
  catálogo en claro y oscuro; `test:visual` pasa.
- [ ] T-055 Comprobación visual en CI
  RF: RF-028, RF-029 | Depende de: T-053, T-054 | Archivos: 1
  Archivos: `.github/workflows/ci.yml`.
  Hecho cuando: un trabajo nuevo instala Chromium y ejecuta `test:visual`; el CI queda en verde en
  el PR.

## Entregas
Rama de integración: `feat/sistema-de-diseno` (los PR de las entregas van contra ella; ver `AGENTS.md`)

- E-01 La app se ve con la paleta Pizarra en claro y oscuro según el sistema operativo.
  Tareas: T-001 | Líneas estimadas: 330 | Rama: feat/sistema-de-diseno-paleta
  Cómo probarlo: `pnpm --filter frontend dev`, abrir http://localhost:5173/ y cambiar el tema del
  sistema operativo; `pnpm --filter frontend test`.
- E-02 Botón de tema que alterna claro y oscuro y se recuerda.
  Tareas: T-002, T-003, T-004, T-005 | Líneas estimadas: 370 | Rama: feat/sistema-de-diseno-tema
  Cómo probarlo: pulsar el botón en la página de muestra, recargar y comprobar que se conserva.
- E-03 La página de muestra exhibe bloques, chips y formas de alarma.
  Tareas: T-006, T-007, T-008, T-009, T-010 | Líneas estimadas: 380 | Rama: feat/sistema-de-diseno-bloques
  Cómo probarlo: abrir la página de muestra y ver la sección de bloques en ambos temas.
- E-04 Botones y avisos con la identidad nueva.
  Tareas: T-011, T-012, T-013, T-014 | Líneas estimadas: 350 | Rama: feat/sistema-de-diseno-botones-avisos
  Cómo probarlo: página de muestra, sección de botones y avisos; `/register` mantiene su flujo.
- E-05 Campos de texto, contraseña, código y casilla con la identidad nueva.
  Tareas: T-015, T-016, T-017, T-018 | Líneas estimadas: 360 | Rama: feat/sistema-de-diseno-campos
  Cómo probarlo: página de muestra y `/register`: hover, foco y error de cada campo.
- E-06 Botón de idioma con menú.
  Tareas: T-019, T-020, T-021 | Líneas estimadas: 400 | Rama: feat/sistema-de-diseno-idioma
  Cómo probarlo: abrir el botón de idioma en el catálogo y cambiar de idioma con ratón y teclado.
- E-07 Selector propio (nativo en dispositivos táctiles).
  Tareas: T-022, T-023, T-024, T-025 | Líneas estimadas: 380 | Rama: feat/sistema-de-diseno-selector
  Cómo probarlo: `/register`, campo «país»: abrir y elegir con teclado; emular puntero táctil y
  comprobar que sale el selector nativo.
- E-08 Registro y acceso con el diseño público.
  Tareas: T-026, T-027, T-028 | Líneas estimadas: 250 | Rama: feat/sistema-de-diseno-publico
  Cómo probarlo: recorrer `/register`, `/register/continue` y `/register/done`.
- E-09 Menú lateral en el catálogo.
  Tareas: T-029, T-030 | Líneas estimadas: 340 | Rama: feat/sistema-de-diseno-menu-lateral
  Cómo probarlo: catálogo; contraer y expandir el menú.
- E-10 Diseño con sesión y panel de menú en pantallas pequeñas.
  Tareas: T-031, T-032, T-033, T-034 | Líneas estimadas: 390 | Rama: feat/sistema-de-diseno-con-sesion
  Cómo probarlo: catálogo, ventana de menos de 768 px y abrir el panel del menú.
- E-11 Barra superior con pestañas y buscador.
  Tareas: T-035, T-036, T-037, T-038 | Líneas estimadas: 400 | Rama: feat/sistema-de-diseno-barra-superior
  Cómo probarlo: catálogo, pantalla de ejemplo: moverse por las pestañas con teclado.
- E-12 Pestañas que no caben, fundido y buscador reducido.
  Tareas: T-039, T-040, T-041, T-042 | Líneas estimadas: 380 | Rama: feat/sistema-de-diseno-pestanas-adaptables
  Cómo probarlo: estrechar la ventana hasta que las pestañas pasen a un selector y el buscador a un botón.
- E-13 Indicadores y tabla.
  Tareas: T-043, T-044, T-045 | Líneas estimadas: 330 | Rama: feat/sistema-de-diseno-indicadores-tabla
  Cómo probarlo: sección de datos del catálogo.
- E-14 Gráfica de barras.
  Tareas: T-046, T-047, T-048 | Líneas estimadas: 330 | Rama: feat/sistema-de-diseno-grafica
  Cómo probarlo: sección de datos del catálogo; `pnpm --filter frontend test` para la escala.
- E-15 Rejilla de estado y limpieza de `base.css`.
  Tareas: T-049, T-050, T-051 | Líneas estimadas: 300 | Rama: feat/sistema-de-diseno-rejilla
  Cómo probarlo: catálogo completo; las pantallas de registro se ven igual que antes de la limpieza.
- E-16 Comprobación visual automática contra las referencias.
  Tareas: T-052, T-053, T-054, T-055 | Líneas estimadas: 300 | Rama: feat/sistema-de-diseno-visual
  Cómo probarlo: `pnpm --filter frontend test:visual`; debe pasar y fallar si se altera un estilo.

## RF sin tarea
Ninguno.
