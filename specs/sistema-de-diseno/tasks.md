# Tareas: sistema-de-diseno
Estado: aprobado

Rutas relativas a `frontend/src/` salvo que se indique. Los tests van junto al archivo que prueban.
«Suite verde» = `pnpm --filter frontend test:coverage` (líneas ≥ 80 %), `typecheck`, `lint` y
`exec prettier --check .` sin errores. En cada tarea se prueba al menos un mutante del código que
introduce y debe hacer fallar sus tests. Cada pieza lleva en su elemento raíz el `data-ui` de las
referencias (`docs/referencia/README.md`) y usa los nombres de clase y medidas de esas páginas (D-01).
Las tareas de «Catálogo» añaden una sección en `showcase/sections/` y la registran en
`showcase/ShowcasePage.tsx`. Las reglas de elementos sueltos de `base.css` se conservan como
transitorias hasta T-051 (D-12).

## E-01 Paleta Pizarra
- [x] T-001 Tokens v2 y base transitoria
  RF: RF-001, RF-004, RF-029 | Depende de: — | Archivos: 4
  Archivos: `styles/tokens.css`, `styles/tokens.test.ts`, `styles/base.css`, `vite.config.ts`.
  Hecho cuando: `tokens.test.ts` compara cada variable con las tablas claro y oscuro de la guía
  (falla al cambiar un valor) y comprueba la regla de movimiento reducido; ya no existe ningún
  `--color-*`; `base.css` usa los tokens nuevos; suite verde; la página de muestra se ve en Pizarra
  con `pnpm --filter frontend dev`.
  Excepción: `vite.config.ts` solo añade `base.css` a los CSS que Vitest procesa, para que
  `tokens.test.ts` pueda leerlo (aprobada por el usuario al detenerse la tarea).
  Decisiones: `--font` y `--mono` nombran las familias de las fuentes de npm («Manrope Variable»,
  «JetBrains Mono Variable») con la familia sin sufijo y la del sistema como reserva — [Probable] —
  revertir: dejar solo «Manrope» y «JetBrains Mono» (no cargarían con el paquete variable). Las
  reglas de elementos de `base.css` (`button`, `input`, `main`, `form`, `section`) se reescriben con
  los tokens nuevos y se marcan como transitorias; el aspecto temporal de las piezas existentes
  (bloque con borde gris de 1 px, botón de radio 6 px) es una aproximación mía hasta T-011/T-015 —
  [Suposición] — revertir: restaurar `base.css` del commit anterior (usaba `--color-*`, que ya no
  existen). Mutantes: cambiar `--grid` oscuro y sustituir `transition: none !important` fallan el
  test.

## E-02 Módulo de tema y textos
- [x] T-002 Módulo de tema
  RF: RF-001, RF-003 | Depende de: T-001 | Archivos: 2
  Archivos: `theme/theme.ts`, `theme/theme.test.ts`.
  Hecho cuando: sin valor guardado devuelve el tema del sistema; con `light` u `oscuro-inválido` se
  ignora y se borra; `toggle` guarda y aplica `data-theme` en `<html>`; suite verde.
  Decisiones: `initTheme` solo escribe `data-theme` si hay un tema guardado válido; sin él, el CSS
  sigue al sistema operativo con la regla de `tokens.css` — [Cierto] — revertir: escribir siempre el
  atributo. `toggleTheme` añade la clase `theme-anim` a `<html>` durante 0,4 s (el CSS que la usa va
  en T-004) y un segundo cambio reinicia ese plazo — [Probable] — revertir: quitar la clase y su
  temporizador. La clave guardada es `confiabilidad.theme`, como la del idioma — [Probable] —
  revertir: cambiar `THEME_STORAGE_KEY`. Mutantes muertos: duración 500 ms, no borrar el valor
  inválido, no alternar, no reiniciar el plazo.
- [x] T-003 Textos del tema en tres idiomas
  RF: RF-030 | Depende de: T-001 | Archivos: 4
  Archivos: `i18n/locales/en.ts`, `es.ts`, `pt-BR.ts`, `locales.test.ts`.
  Hecho cuando: existen `theme.light`, `theme.dark` y `theme.toggle` en los tres idiomas y
  `locales.test.ts` y `keys.test.ts` pasan; suite verde.
  Excepción: los tres archivos de idioma son una unidad (`es` y `pt-BR` se tipan contra `en`), y
  `locales.test.ts` lista los grupos de claves de esos mismos archivos y debe añadir `theme`.
  Decisiones: claves `theme.light`, `theme.dark`, `theme.toggle` (nombre accesible del botón),
  `theme.announceLight` y `theme.announceDark` (aviso al lector tras cambiar) — [Probable] — revertir:
  borrar el grupo `theme` de los tres idiomas y de `locales.test.ts`. Mutante muerto: quitar una
  clave de `es` falla `locales.test.ts` y `tsc`. Se amplió el texto de la Excepción a
  `locales.test.ts` sin detenerme, por ser el mismo conjunto de archivos — [Suposición] — revertir:
  pedir una Excepción aparte.
## E-02b Botón de tema
- [x] T-004 Botón de tema
  RF: RF-002 | Depende de: T-002, T-003 | Archivos: 3
  Archivos: `theme/ThemeButton.tsx`, `ThemeButton.css`, `ThemeButton.test.tsx`.
  Hecho cuando: pulsarlo alterna el tema, cambia su icono y etiqueta, anuncia el estado al lector
  y pasa `axe-core`; suite verde.
  Decisiones: el botón usa `data-ui="sidebar-button"`, la clase `sb-btn hov` de las referencias y
  muestra la etiqueta del tema activo con el nombre accesible «Tema claro. Cambiar tema» — [Probable]
  — revertir: cambiar los textos de `theme.*`. Las clases comunes `hov`, `sb-btn`, `svg.i` y la
  transición `theme-anim` viven por ahora en `ThemeButton.css`; el menú lateral (T-029) las moverá a
  un archivo compartido — [Suposición] — revertir: moverlas antes. Sol y luna están dibujados en el
  componente hasta que exista el módulo de iconos (T-006); migrarlos queda para una tarea de
  limpieza — [Suposición] — revertir: importar los iconos de `icons/` y borrar los dibujos. El
  contraste no se prueba en jsdom (lo hará T-054). Mutantes muertos: sin aviso, sin estado, icono
  cambiado, sin `data-ui`.
- [x] T-005 Aplicar el tema al arrancar y mostrar el botón
  RF: RF-001, RF-002, RF-027 | Depende de: T-004 | Archivos: 3
  Archivos: `main.tsx`, `showcase/ShowcasePage.tsx`, `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: la página de muestra tiene el botón y el tema elegido sobrevive a recargar; suite
  verde.
  Decisiones: el botón se coloca bajo el selector de idioma, a todo el ancho, porque la página de
  muestra aún no tiene barra superior ni menú (E-08 y siguientes la colocan en su sitio) —
  [Cierto] — revertir: quitar la línea de `ShowcasePage.tsx`. `main.tsx` no tiene test (está fuera de
  la cobertura); se comprobó en un navegador real con Playwright: el tema alterna, sobrevive a
  recargar y un valor guardado inválido se borra — [Cierto] — revertir: no aplica. Mutante muerto:
  no pasar el almacenamiento al botón.

## E-03 Iconos, formas y chip
- [x] T-006 `lucide-react` y módulo de iconos
  RF: RF-020 | Depende de: — | Archivos: 4
  Archivos: `frontend/package.json`, `pnpm-lock.yaml`, `icons/index.ts`, `icons/icons.test.ts`.
  Hecho cuando: `lucide-react` está en `dependencies`; el módulo reexporta por nombre los iconos
  de la guía a 16 px y trazo 2; suite verde.
  Excepción: `pnpm-lock.yaml` lo regenera `pnpm add`.
  Decisiones: se instaló `lucide-react` 1.70.0 (aprobada por el usuario en la definición de la
  feature). El módulo exporta 22 componentes `IconXxx` (los de las referencias) que envuelven los de
  lucide con `size` 16, `strokeWidth` 2 y `aria-hidden`, sustituibles por props — [Probable] —
  revertir: importar directamente de `lucide-react`. Nombres: `Building2` para edificio, `FileText`
  para archivo, `CircleAlert` para alerta, `ChevronsUpDown` para los chevrons dobles,
  `PanelLeftClose`/`PanelLeftOpen` para el panel — [Suposición], no comparé el dibujo con el de las
  referencias — revertir: cambiar el icono de lucide en `icons/index.ts`. El test es `.tsx`, no `.ts`
  como decía la tarea, porque renderiza componentes — [Cierto]. Mutante equivalente: quitar
  `aria-hidden` no cambia nada porque lucide ya lo añade cuando el icono no lleva etiqueta; se
  mantiene explícito para no depender de ese detalle. Mutantes muertos: tamaño, trazo, orden de
  `props`.
- [x] T-007 Formas de alarma
  RF: RF-020, RF-025 | Depende de: T-006 | Archivos: 2
  Archivos: `icons/shapes.tsx`, `icons/shapes.test.tsx`.
  Hecho cuando: P1 es un cuadrado, P2 un triángulo, advertencia un rombo y neutro un cuadrado
  vacío, con nombre accesible y sin depender del color; suite verde.
  Decisiones: componente `AlarmShape` con `kind` (`p1`, `p2`, `warning`, `neutral`), `label`
  opcional (con él es `role="img"`; sin él, `aria-hidden`), `size`, `className` y `style`; cada
  forma lleva su color por defecto (`--p1`, `--p2`, `--warn`, `--text2`) y `data-shape` — [Probable] —
  revertir: cambiar `shapes.tsx`. La geometría se copió de los símbolos `s-p1`, `s-p2`, `s-wn` y
  `s-nu` de `activos.html` — [Cierto]. Mutantes muertos: triángulo por rombo, color de P2, `aria-hidden`
  fijo, orden de `style`.
- [x] T-009 Chip
  RF: RF-023 | Depende de: T-001 | Archivos: 3
  Archivos: `components/Chip.tsx`, `Chip.css`, `Chip.test.tsx`.
  Hecho cuando: renderiza el texto en el chip de la guía y pasa `axe-core`; suite verde.
  Decisiones: `Chip` es un `span` con la clase `chip` y `data-ui="chip"` que acepta los atributos
  de `span` — [Cierto] — revertir: cambiar `Chip.tsx`. Mutantes muertos: `data-ui`, atributos extra,
  clase base.
## E-03b Bloque y catálogo
- [x] T-008 Bloque
  RF: RF-014 | Depende de: T-001 | Archivos: 3
  Archivos: `components/Block.tsx`, `Block.css`, `Block.test.tsx`.
  Hecho cuando: variantes normal, destacado y en alerta, con cabecera opcional (título, contador,
  acciones); suite verde.
  Decisiones: `Block` admite `variant` (`default`, `featured`, `alert`), `as` (`div`, `section`,
  `aside`; los dos últimos quedan etiquetados por su título), `title`, `headingLevel` (2 a 4),
  `count` con `countLabel` y `actions`; la cabecera `.blk-h` solo aparece si hay título, contador o
  acciones — [Probable] — revertir: simplificar `Block.tsx`. `Counter` se exporta desde `Block.tsx`
  porque el menú lateral (T-029) lo reutiliza — [Probable] — revertir: moverlo a su propio archivo.
  El bloque en alerta pone fondo `--black-fill` y texto blanco; la cifra en el color de la prioridad
  es del indicador (T-043) — [Cierto]. Los títulos de nivel 3 y 4 usan el mismo estilo que el de
  nivel 2 — [Suposición] — revertir: estilar solo `h2`. Mutantes muertos: contador en cero, `sp`,
  `data-ui`, `aria-labelledby`, clase `default`, `div` etiquetado.
- [x] T-010 Catálogo: bloques, chips y formas
  RF: RF-027 | Depende de: T-007, T-008, T-009 | Archivos: 4
  Archivos: `showcase/sections/BlocksSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: la página de muestra exhibe las tres variantes de bloque, chips y las cuatro
  formas en ambos temas; suite verde.
  Excepción: `showcase/sections/sections.css` (espaciado del catálogo) es un archivo más; lo
  reutilizan todas las tareas de catálogo siguientes. Lo añadí sin detenerme, por ser el único
  archivo de estilo que necesitan todas — [Suposición] — revertir: pedir una Excepción aparte.
  Decisiones: el contenido de ejemplo del catálogo va escrito en español con `lang="es"` en su
  contenedor, porque son textos inventados (S-03) y traducirlos exigiría añadir claves a los tres
  idiomas en cada tarea de catálogo — [Suposición] — revertir: moverlos a las claves de idioma. El
  contenedor es `div role="region"` y no `section`, para no heredar la regla transitoria de
  `section` de `base.css` — [Cierto]. Verificado en un navegador real en claro y oscuro. Mutantes
  muertos: sin `lang`, sin variante de alerta, sin una forma, sin chips.

## E-04 Botón y aviso
- [x] T-011 Botón restilizado
  RF: RF-018 | Depende de: T-001 | Archivos: 3
  Archivos: `components/Button.tsx`, `Button.css`, `Button.test.tsx`.
  Hecho cuando: variantes principal y secundario con hover, foco y procesando de la guía; los
  tests previos de `Button` siguen pasando; suite verde.
  Decisiones: `Button` recibe `variant` (`primary` por defecto, `secondary`) y `className`; pone las
  clases `btn btn-primary` o `btn btn-ghost hov` y `data-ui="button-primary"` o
  `"button-secondary"` de las referencias — [Probable] — revertir: quitar la prop y las clases. El
  hover del secundario (`.hov`) se duplica en `Button.css` porque `ThemeButton.css` solo se carga si
  hay un botón de tema; el menú lateral (T-029) lo moverá a un archivo compartido — [Suposición] —
  revertir: importar `ThemeButton.css` desde `Button.tsx`. El estado «procesando»
  (`aria-disabled`) se ve con `cursor: not-allowed` y opacidad 0,6, valores heredados del estilo
  provisional anterior porque la guía no los define — [Suposición] — revertir: quitar la regla
  `.btn[aria-disabled]`. Los botones existentes de las pantallas siguen siendo principales.
  Mutantes muertos: variantes intercambiadas, `data-ui` fijo, variante por defecto, `className`.
  Corrección: `.hov` de `ThemeButton.css` (que se carga después) quitaba el borde del botón
  secundario; el borde usa la especificidad `.btn.btn-ghost`, comprobado en un navegador real
  (borde de 1 px, 36 px de alto, radio 6 px) — [Cierto]. Los estilos no se prueban en jsdom; lo
  cubrirá la comprobación visual (T-053).
- [x] T-012 Aviso
  RF: RF-019 | Depende de: T-006 | Archivos: 3
  Archivos: `components/Notice.tsx`, `Notice.css`, `Notice.test.tsx`.
  Hecho cuando: borde izquierdo de 4 px, icono e interlineado de la guía; suite verde.
  Decisiones: `Notice` es un `div` con rol `status` por defecto (cambiable con `role`), clase `notice`
  y `data-ui="notice"`; `kind` elige el icono (`info` por defecto, `success` con verificación) y
  ambos usan el color de texto secundario — [Probable] — revertir: simplificar `Notice.tsx`. La
  referencia de «Crear empresa» no marca su aviso con `data-ui` (está oculto); no se añadió a la
  referencia — [Cierto]. Mutantes muertos: iconos intercambiados, rol por defecto, atributos extra,
  `data-ui`, clase base.
## E-04b Aviso de alarma y catálogo
- [x] T-013 Aviso de alarma
  RF: RF-019, RF-020 | Depende de: T-007, T-011 | Archivos: 3
  Archivos: `components/AlarmNotice.tsx`, `AlarmNotice.css`, `AlarmNotice.test.tsx`.
  Hecho cuando: muestra la forma de su prioridad, título, texto y una acción opcional; suite verde.
  Decisiones: `AlarmNotice` recibe `kind` (`p1`, `p2`, `warning`, `neutral`), `title` en negrita,
  texto y `action` opcional; pone el color en la variable `--c` (borde izquierdo) y en la forma, y el
  texto queda en tinta — [Cierto]. La forma va oculta al lector porque el título o el texto ya dicen
  la prioridad — [Probable] — revertir: pasar `label` a `AlarmShape`. No lleva rol por defecto, para
  que una lista de alarmas no se anuncie de golpe; quien lo use puede pasar `role="alert"` —
  [Suposición] — revertir: poner `role="status"` por defecto. Un `style` externo manda sobre `--c`
  — [Probable] — revertir: invertir el orden. Mutantes muertos: color de P2, acción, negrita,
  `data-ui`, orden del estilo, forma.
- [x] T-014 Catálogo: botones y avisos
  RF: RF-027 | Depende de: T-012, T-013 | Archivos: 3
  Archivos: `showcase/sections/ButtonsSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe botones y avisos en todos sus estados; suite verde.
  Excepción: sin cambios; `sections.css` ya existe desde T-010.
  Decisiones: la sección «Botones y avisos» va en español con `lang="es"` (como la de bloques); sus
  avisos informativos llevan `role="note"` para no añadir regiones `status` que choquen con el
  anunciador de la aplicación — [Probable] — revertir: dejar el rol por defecto y ajustar
  `ShowcasePage.test.tsx`. Verificado en un navegador real en claro y oscuro (el fallo del borde del botón secundario que apareció aquí se corrigió en E-04). Los estilos no se prueban en jsdom; lo cubrirá la
  comprobación visual (T-053). Mutantes muertos: sin `lang`, sin botón procesando, forma cambiada,
  sin aviso de éxito.

## E-05 Campos de texto
- [x] T-015 Campo de texto restilizado
  RF: RF-015 | Depende de: T-006 | Archivos: 3
  Archivos: `components/fields/TextField.tsx`, `fields/field.css`, `TextField.test.tsx`.
  Hecho cuando: borde de 1 px al pasar el cursor, de 2 px con foco sin mover el contenido y error
  con icono; los tests previos de `TextField` siguen pasando; suite verde.
  Decisiones: `TextField` usa la estructura de las referencias (`.fld` con `label`, `input.field`,
  `.help` y `.error-msg` con icono de alerta), añade `data-ui="field-label"` y `"field"` y suma
  `className` a la clase `field` — [Probable] — revertir: volver al marcado anterior. Las reglas de
  `field.css` para `form > .fld + .fld` y `form > .btn` son transitorias (separación en formularios
  sin rejilla) y se retiran en T-051 — [Suposición]. Verificado en un navegador real: reposo 36 px
  con borde de 1 px, hover en el principal, foco con borde de 2 px y relleno de 10 px sin mover el
  texto, y error con borde, icono y mensaje en tinta — [Cierto]. Mutantes muertos: `className`,
  `data-ui`, icono de error, clase `req`, clase `fld`, clase `help`.
- [x] T-016 Contraseña, código y leyenda de obligatorios
  RF: RF-015 | Depende de: T-015 | Archivos: 4
  Archivos: `components/fields/PasswordField.tsx`, `CodeField.tsx`, `RequiredLegend.tsx`,
  `TextField.test.tsx`.
  Hecho cuando: usan las clases de `field.css`; los tests previos de ambos campos siguen pasando
  sin cambios; suite verde.
  Excepción: se añadió `TextField.test.tsx` (un bloque con tres tests nuevos de estas tres piezas)
  para respetar el test primero; no cabía en los tests previos, que se conservan sin cambios. Lo
  añadí sin detenerme — [Suposición] — revertir: pedir una Excepción aparte.
  Decisiones: el botón de mostrar contraseña es un botón secundario (`btn btn-ghost hov`) dentro del
  campo, a su ancho natural — [Probable]; el código de verificación usa `mono`; la leyenda de
  obligatorios usa la clase `help` (12 px, texto secundario) y conserva su texto —  [Cierto] —
  revertir: quitar las clases. `PasswordField.tsx` importa `Button.css` para no depender de que otro
  componente cargue los estilos del botón — [Cierto]. Mutantes muertos: sin las tres clases.
## E-05b Casilla y catálogo de campos
- [x] T-017 Casilla de verificación
  RF: RF-017 | Depende de: T-006 | Archivos: 3
  Archivos: `components/fields/Checkbox.tsx`, `Checkbox.css`, `Checkbox.test.tsx`.
  Hecho cuando: icono de verificación centrado, etiqueta y ayuda opcional; suite verde.
  Decisiones: `Checkbox` envuelve la caja y el icono de verificación en `label.check`; la ayuda y el
  error van fuera de la etiqueta, bajo el texto, para que el nombre accesible de la casilla sea solo
  su etiqueta (como pedían los tests previos) — [Probable] — revertir: meter la ayuda en `.txt`. Por petición del usuario durante la revisión de E-05b, la ayuda y el error no llevan sangría
  (sin margen izquierdo): quedan alineados con el borde de la caja — [Cierto] — revertir: añadir de
  nuevo `margin-left: 28px` a esas dos clases dentro de `.check-field`. El
  icono de verificación mide 14 px con trazo 3 y la caja es nativa con `appearance: none` —
  [Cierto]. Los estilos no se verificaron aún en un navegador: `/register` necesita el backend para
  cargar los términos; se verifica en el catálogo (T-018) — [Cierto]. Mutantes muertos: `data-ui`,
  tamaño del icono, clase de la nota, clase `check`, asterisco.
- [x] T-018 Catálogo: campos
  RF: RF-027 | Depende de: T-016, T-017 | Archivos: 3
  Archivos: `showcase/sections/FieldsSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe campos, error y casilla; suite verde.
  Excepción: `showcase/sections/sections.css` (ya existente) recibe dos clases más, `catalog-grid` y
  `catalog-stack`; no es un archivo nuevo.
  Decisiones: la sección «Campos» va en español con `lang="es"`; sus etiquetas son «Razón social»,
  «Clave de acceso» y «Código» para no chocar con las de los tests existentes de la página —
  [Cierto]. La casilla con error muestra el mensaje con icono pero su borde no cambia a rojo, porque
  la guía solo define el borde de error para los campos de texto — [Suposición] — revertir: añadir
  una regla para `.cb input[aria-invalid="true"]`. Verificado en un navegador real en claro y
  oscuro: caja de 18 px con borde de 1 px, marcada con el principal y el icono visible; sin marcar con
  fondo del lienzo y el icono oculto. Mutantes muertos: sin `lang`, sin error del campo, sin casilla
  marcada, sin campo de código, sin error de la casilla.

## E-06 Menú desplegable
- [x] T-019 Menú desplegable compartido
  RF: RF-011, RF-016 | Depende de: T-001 | Archivos: 3
  Archivos: `components/menu/Menu.tsx`, `Menu.css`, `Menu.test.tsx`.
  Hecho cuando: abre con animación de 0,18 s, navega con flechas, Inicio y Fin, cierra con
  Escape y clic fuera y devuelve el foco al disparador; suite verde.
  Decisiones: `Menu` sigue el patrón «select-only combobox»: el disparador lo pinta quien lo usa con
  `renderTrigger` (recibe `role="combobox"`, `aria-expanded`, `aria-controls`,
  `aria-activedescendant` y los manejadores del teclado) y el foco no sale de él; las opciones son
  `li role="option"` con `lang` opcional y un chevron «>» que solo se ve en la seleccionada — [Probable]
  — revertir: rehacer el componente. Las flechas se detienen en los extremos, sin dar la vuelta —
  [Suposición] — revertir: usar módulo en `ArrowDown` y `ArrowUp`. La escritura para saltar a una
  opción (RF-016) no está aquí: la añade T-058 sobre este menú — [Cierto]. Se cierra con Escape,
  al salir del foco y con un clic fuera; abre con animación (la clase `open` aparece en el
  siguiente fotograma) y cierra sin animación — [Cierto]. Un disparador con rol `combobox` necesita
  nombre accesible propio (`aria-label`): `axe` lo exige porque ese rol no toma el nombre de su
  texto — [Cierto]. Mutantes muertos: topes de las flechas, Escape, foco de las opciones, cierre al
  salir, alineación, opción inicial, animación, `aria-activedescendant`, clic fuera y soltar la barra
  espaciadora.
## E-06b Botón de idioma y catálogo
- [x] T-020 Botón de idioma
  RF: RF-005, RF-007, RF-030 | Depende de: T-019 | Archivos: 3
  Archivos: `components/LanguageButton.tsx`, `LanguageButton.css`, `LanguageButton.test.tsx`.
  Hecho cuando: muestra el código del idioma activo, abre un menú con los tres idiomas por su
  nombre y cambia y guarda el idioma como `LanguageSwitcher`; suite verde.
  Decisiones: `LanguageButton` usa `Menu`; su nombre accesible es «Idioma: Español» (la clave
  `language.label` más el nombre del idioma activo en su idioma), sin claves de texto nuevas, y
  muestra el código de dos letras («ES», «PT», «EN») — [Probable] — revertir: cambiar
  `LanguageButton.tsx`. Repite las cuatro líneas de `choose` de `LanguageSwitcher` en lugar de
  compartirlas, para no tocar ese componente (fuera de la tarea) — [Suposición] — revertir: extraer
  una función común a `i18n/language.ts`. Importa `ThemeButton.css` porque de ahí vienen `sb-btn`
  y `hov` hasta que el menú lateral (T-029) los mueva a un archivo común — [Suposición]. Mutantes
  muertos: sin guardar, código del idioma, `lang`, `data-ui`, opción seleccionada, sin cambio de
  idioma, nombre accesible.
- [x] T-021 Catálogo: menú e idioma
  RF: RF-027 | Depende de: T-020 | Archivos: 3
  Archivos: `showcase/sections/MenuSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe el botón de idioma; suite verde.
  Excepción: `showcase/sections/sections.css` (ya existente) recibe la clase `catalog-narrow`; no es
  un archivo nuevo.
  Decisiones: la sección «Menú e idioma» va en español con `lang="es"`; muestra el botón de idioma
  real y un menú genérico de plantas con elección guardada en el propio estado — [Probable] —
  revertir: quitar el menú genérico. Verificado en un navegador real en claro y oscuro: el menú se
  abre bajo el disparador a 4 px, con la opción activa en negrita con chevron y resaltada. Mutantes
  muertos: sin `lang`, sin guardar la elección, sin botón de idioma.
  Corrección pedida por el usuario durante la revisión de E-06b: los disparadores de los menús de
  selección ocupan todo el ancho de su contenedor. `Menu.css` da al contenedor `.select` el 100 % de
  ancho y al disparador (`[role="combobox"]`) el 100 %; la sección del catálogo usa una rejilla en
  lugar de anchos fijos de 200 px; el `<select>` nativo transitorio de `base.css` también ocupa el
  100 %; la guía lo recoge en la tabla «Menú de selección». Comprobado en un navegador real
  (disparador 402 px en un contenedor de 402 px, menú desplegado de 402 px y `<select>` nativo de
  300 px en un contenedor de 300 px). Los estilos no se prueban en jsdom; lo cubrirá la
  comprobación visual (T-053) — [Cierto].

## E-07 Escritura en el menú
- [x] T-058 Escritura para saltar a una opción en el menú
  RF: RF-016 | Depende de: T-019 | Archivos: 2
  Archivos: `components/menu/Menu.tsx`, `menu/Menu.test.tsx`.
  Hecho cuando: con el menú abierto o cerrado, escribir una o varias letras resalta la siguiente
  opción cuyo texto empieza por ellas (por su valor si la etiqueta no es texto); repetir una letra
  recorre las que empiezan por ella; una pausa de 0,7 s las olvida; las combinaciones con Ctrl, Alt
  o Meta no cuentan como texto; suite verde.
  Decisiones: nació de T-023 al dividir E-07 por tamaño; se hizo sobre el menú compartido porque el
  selector (T-023), el botón de idioma y el selector de pestañas la comparten — [Cierto]. Mutantes
  muertos: ciclar, temporizador, olvidar tras la pausa, mayúsculas, Ctrl, abrir al escribir, texto
  frente a valor.
## E-07b Selector propio
- [x] T-023 Selector propio
  RF: RF-016 | Depende de: T-015, T-019, T-058 | Archivos: 3
  Archivos: `components/fields/CustomSelect.tsx`, `CustomSelect.css`, `ChoiceFields.test.tsx`.
  Hecho cuando: el disparador `<button role="combobox" name value>` abre la lista, se maneja con
  Enter, Espacio, flechas, Inicio, Fin, Escape y escritura, marca la opción, muestra el error y
  anuncia valor y estado; `useFormValidation` lo lee y enfoca; suite verde con `RegisterPage`.
  Decisiones (desvío del orden previsto): el selector propio se escribió en un componente nuevo,
  `CustomSelect`, y no sobre `SelectField`; `SelectField` pasa a elegir entre el propio y el nativo en
  T-024, donde se reescriben sus tests. Así `SelectField`, `RegisterPage` y sus tests siguen en verde
  entre una tarea y otra — [Probable] — revertir: mover el contenido a `SelectField.tsx`. El
  disparador es un `<button name value>` con `role="combobox"` etiquetado con un `<label htmlFor>`;
  no hay opción vacía en la lista, el texto de reserva solo se ve sin valor — [Suposición] —
  revertir: añadir una primera opción vacía. La escritura para saltar a una opción viene del
  menú (T-058, E-07). Mutantes muertos: `value`, `name`, valor controlado, aviso de cambio,
  `onBlur`, `ref`, texto de reserva, estado interno.

- [x] T-025 Catálogo: selector
  RF: RF-027 | Depende de: T-023 | Archivos: 3
  Archivos: `showcase/sections/FieldsSection.tsx`, `showcase/ShowcasePage.tsx`,
  `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el catálogo exhibe el selector con valor y con error; suite verde.
  Decisiones: la sección «Campos» muestra `CustomSelect` (con valor y con error) y no `SelectField`,
  que sigue siendo el nativo hasta T-024; por eso la tarea depende de T-023 y no de T-024 —
  [Cierto]. Se ajustó el test de la sección para contar solo los `input` con error (el selector con
  error añade otro disparador inválido). Verificado en un navegador real en claro y oscuro:
  disparador de 36 px a todo el ancho de su columna con borde de 1 px, hover en el principal, 2 px y
  relleno de 10 px abierto, y lista con la opción activa en negrita con chevron. Mutantes
  muertos: cubiertos por los de T-023.

## E-07c Selector nativo en dispositivos táctiles
- [ ] T-022 Detección de puntero táctil
  RF: RF-031 | Depende de: — | Archivos: 2
  Archivos: `components/fields/useCoarsePointer.ts`, `useCoarsePointer.test.ts`.
  Hecho cuando: devuelve verdadero si `matchMedia("(pointer: coarse)")` coincide y reacciona a su
  cambio; suite verde.
- [ ] T-024 Selector nativo en dispositivos táctiles
  RF: RF-031 | Depende de: T-022, T-023 | Archivos: 2
  Archivos: `components/fields/SelectField.tsx`, `ChoiceFields.test.tsx`.
  Hecho cuando: con puntero táctil se muestra el `<select>` nativo con la misma etiqueta, valor,
  opciones y error; suite verde.

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

## E-05c Botón de ojo en la contraseña (cambio aprobado por el usuario)
- [x] T-056 Iconos de ojo en el módulo de iconos
  RF: RF-015 | Depende de: T-006 | Archivos: 2
  Archivos: `icons/index.ts`, `icons/icons.test.tsx`.
  Hecho cuando: el módulo exporta `IconEye` y `IconEyeOff` a 16 px y trazo 2, y su test los
  incluye; suite verde.
  Decisiones: se añadió además un test que distingue el ojo abierto del tachado, porque el test de
  contrato no detectaba que `IconEyeOff` dibujara el ojo abierto — [Cierto]. Mutante muerto: `EyeOff`
  sustituido por `Eye`.
- [x] T-057 Botón de ojo dentro del campo de contraseña
  RF: RF-015 | Depende de: T-056, T-016 | Archivos: 4
  Archivos: `components/fields/PasswordField.tsx`, `field.css`, `PasswordField.test.tsx`,
  `TextField.test.tsx`.
  Hecho cuando: el botón es un `<button>` real dentro del campo, a la derecha, con `IconEye`
  (contraseña oculta) o `IconEyeOff` (visible) y sin texto visible; mantiene el nombre accesible
  («Mostrar contraseña (Contraseña)») y `aria-pressed`; su área pulsable es de al menos 32 × 32 px;
  el foco, el teclado y la regla de que campo y botón cuentan como uno al validar al salir no
  cambian; los tests previos pasan salvo los que miran el texto visible del botón, que se
  actualizan; suite verde.
  Excepción: `TextField.test.tsx` contiene un test de T-016 que afirma que el botón es secundario
  con texto; deja de ser cierto y hay que cambiarlo en el mismo cambio. Lo añadí sin detenerme —
  [Suposición] — revertir: pedir una Excepción aparte.
  Decisiones: el botón mide 32 × 32 px (no 36) porque dentro de un campo de 36 px con borde de 1 px
  cubriría el borde — aprobado por el usuario en la propuesta — [Cierto]. Se coloca con CSS
  puro: sigue al input en el flujo y sube con un margen negativo (`-40px`, es decir, 36 px del input
  más los 6 px de separación menos 2 px de margen), sin envolver el input en otro elemento — [Suposición]:
  depende de que la separación de `.fld` siga siendo de 6 px; lo vigilará la comprobación visual
  (T-053) — revertir: envolver input y botón en un contenedor con `position: relative`, lo que
  obliga a tocar `TextField.tsx`. El input lleva la clase `has-action` para dejar sitio bajo el botón
  (38 px de relleno derecho, 37 px con foco). El área de 32 × 32 px no se puede probar en jsdom;
  se comprobó en un navegador real (32 × 32, dentro del input, 16 px de icono) — [Cierto]. Color en
  texto secundario y en tinta al pasar el cursor, en claro y oscuro — [Cierto]. Se corrigieron dos
  fallos que solo vio el navegador: el relleno del `button` transitorio de `base.css` aplastaba el
  icono y su regla de `aria-pressed` pisaba el color; la regla usa `.fld .field-action` y
  `padding: 0`. Mutantes muertos: iconos intercambiados, sin clase, sin `has-action`, sin
  `aria-pressed`, sin nombre accesible.

## Entregas
Rama de integración: `feat/sistema-de-diseno` (los PR de las entregas van contra ella; ver `AGENTS.md`)

- E-01 La app se ve con la paleta Pizarra en claro y oscuro según el sistema operativo.
  Tareas: T-001 | Líneas estimadas: 330 | Rama: feat/sistema-de-diseno-paleta
  Cómo probarlo: `pnpm --filter frontend dev`, abrir http://localhost:5173/ y cambiar el tema del
  sistema operativo; `pnpm --filter frontend test`.
- E-02 Módulo de tema y textos (sin botón visible aún).
  Tareas: T-002, T-003 | Líneas estimadas: 250 | Rama: feat/sistema-de-diseno-modulo-tema
  Cómo probarlo: `pnpm --filter frontend test`; los tests de `theme/theme.test.ts` cubren RF-001 a RF-003.
  Nota: E-02 se dividió en E-02 y E-02b porque la entrega completa medía 515 líneas (límite 400);
  el usuario lo aprobó al detenerse la cadena.
- E-02b Botón de tema que alterna claro y oscuro y se recuerda.
  Tareas: T-004, T-005 | Líneas estimadas: 265 | Rama: feat/sistema-de-diseno-boton-tema
  Cómo probarlo: pulsar el botón en la página de muestra, recargar y comprobar que se conserva.
- E-03 Iconos, formas de alarma y chip (sin nada visible aún).
  Tareas: T-006, T-007, T-009 | Líneas estimadas: 315 | Rama: feat/sistema-de-diseno-iconos
  Cómo probarlo: `pnpm --filter frontend test`; los tests de `icons/` y `components/Chip.test.tsx`.
  Nota: E-03 se dividió en E-03 y E-03b porque la entrega completa medía 665 líneas (límite 400);
  el usuario lo aprobó al detenerse la cadena.
- E-03b La página de muestra exhibe bloques, chips y formas de alarma.
  Tareas: T-008, T-010 | Líneas estimadas: 350 | Rama: feat/sistema-de-diseno-bloque-catalogo
  Cómo probarlo: abrir la página de muestra y ver la sección de bloques en ambos temas.
- E-04 Botón con variantes y aviso informativo (sin nada visible aún, salvo los botones del formulario).
  Tareas: T-011, T-012 | Líneas estimadas: 210 | Rama: feat/sistema-de-diseno-boton-aviso
  Cómo probarlo: `pnpm --filter frontend test`; en la página de muestra y en `/register` los botones
  usan el estilo nuevo.
  Nota: E-04 se dividió en E-04 y E-04b porque la entrega completa medía 428 líneas (límite 400);
  el usuario lo aprobó al detenerse la cadena.
- E-04b Aviso de alarma y sección de botones y avisos en el catálogo.
  Tareas: T-013, T-014 | Líneas estimadas: 220 | Rama: feat/sistema-de-diseno-aviso-alarma
  Cómo probarlo: página de muestra, sección «Botones y avisos», en ambos temas.
- E-05 Campos de texto, contraseña y código con la identidad nueva.
  Tareas: T-015, T-016 | Líneas estimadas: 205 | Rama: feat/sistema-de-diseno-campos-texto
  Cómo probarlo: página de muestra y `/register`: hover, foco y error de cada campo.
  Nota: E-05 se dividió en E-05 y E-05b porque la entrega completa medía 467 líneas (límite 400);
  se aplicó la regla de AGENTS.md sobre entregas que rebasan el límite.
- E-05b Casilla de verificación y sección «Campos» del catálogo.
  Tareas: T-017, T-018 | Líneas estimadas: 262 | Rama: feat/sistema-de-diseno-casilla
  Cómo probarlo: página de muestra, sección «Campos»: marcar y desmarcar las casillas, en ambos temas.
- E-05c Botón de ojo dentro del campo de contraseña (cambio aprobado por el usuario después de E-05).
  Tareas: T-056, T-057 | Líneas estimadas: 80 | Rama: feat/sistema-de-diseno-ojo-contrasena
  Cómo probarlo: página de muestra, campo «Clave de acceso»: pulsar el ojo para mostrar y ocultar.
- E-06 Menú desplegable compartido (sin nada visible aún: se prueba con tests).
  Tareas: T-019 | Líneas estimadas: 474 | Rama: feat/sistema-de-diseno-menu
  Cómo probarlo: `pnpm --filter frontend test`; los 18 tests de `components/menu/Menu.test.tsx`.
  Excepción: el menú con su teclado, su ratón, su animación y sus tests es un solo comportamiento
  y no se puede dividir sin dejar una versión que no se pueda usar; supera las 400 líneas y se
  queda en 474, por debajo de las 500 de la excepción. Nota: E-06 se dividió en E-06 y E-06b porque
  la entrega completa medía 725 líneas; el menú por sí solo ya supera 400 y no deja nada visible
  que enseñar dentro del límite.
- E-06b Botón de idioma con menú y su sección en el catálogo.
  Tareas: T-020, T-021 | Líneas estimadas: 251 | Rama: feat/sistema-de-diseno-boton-idioma
  Cómo probarlo: abrir el botón de idioma en el catálogo y cambiar de idioma con ratón y teclado.
- E-07 Escritura para saltar a una opción en los menús desplegables.
  Tareas: T-058 | Líneas estimadas: 186 | Rama: feat/sistema-de-diseno-escritura-menu
  Cómo probarlo: página de muestra, «Menú e idioma»: abrir el menú de plantas y escribir «s» o «e».
  Nota: E-07 se dividió en tres (E-07, E-07b y E-07c) porque la entrega completa medía 594 líneas y
  faltaba T-024; se aplicó la regla de AGENTS.md. T-058 nació de T-023 en esa división.
- E-07b Selector propio con su sección en el catálogo.
  Tareas: T-023, T-025 | Líneas estimadas: 330 | Rama: feat/sistema-de-diseno-selector-propio
  Cómo probarlo: página de muestra, «Campos»: abrir «Sector» y elegir con ratón, flechas y escribiendo.
- E-07c Selector nativo en dispositivos táctiles y selector propio en el registro.
  Tareas: T-022, T-024 | Líneas estimadas: 250 | Rama: feat/sistema-de-diseno-selector-tactil
  Cómo probarlo: `/register`, campo «País»: elegir con teclado; emular puntero táctil y comprobar
  que sale el selector nativo.
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
