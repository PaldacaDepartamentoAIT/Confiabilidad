# Plan: registro-diseno-visual
Estado: aprobado

Feature solo de `frontend/` (y de `docs/identidad-visual.md`). No toca el backend ni la API: los
datos, las validaciones y las respuestas siguen siendo los de `registro-flujo`. No añade
dependencias: los iconos son SVG propios, y la animación, el menú, el selector, el globo y la
ventana se hacen con React, CSS, la Web Animations API y `<dialog>`.

## Módulos

### M-01 Guía visual ampliada
Responsabilidad: añadir a `docs/identidad-visual.md` las piezas que aún no cubre: barra superior,
botón con menú, indicador de pasos, botón «?» con su globo, selector propio, ventana de documento,
zona de mensajes, transición entre pasos y la regla del tema elegido. Va antes que el código (D-14)
y la aprueba el usuario (CF-5).
RF: RF-022 (y CF-5)

### M-02 Iconos
Responsabilidad: `frontend/src/components/icons.tsx`, componentes SVG en línea con
`aria-hidden="true"` y `currentColor`: sol, luna, ojo, ojo tachado, flecha abajo, flecha derecha,
check y cerrar. Sin texto propio: el nombre accesible lo pone el control que los contiene.
RF: RF-003, RF-006, RF-008, RF-012, RF-017, RF-018

### M-03 Tema
Responsabilidad: `frontend/src/theme/theme.ts` con la misma forma que `i18n/language.ts`: los temas
`light` y `dark`, la clave `confiabilidad.theme`, leer (borrando un valor no válido), guardar y
aplicar el tema como `data-theme` en `<html>`. Si no hay tema guardado, `<html>` no lleva
`data-theme` y manda `prefers-color-scheme`. Un hook `useTheme` da el tema en uso (el elegido o el
del sistema, que escucha con `matchMedia`) y la función para elegirlo. `tokens.css` pasa a tener
la paleta oscura en dos selectores: `:root[data-theme="dark"]` y
`@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) }`. Un script en línea en
`index.html`, antes de la hoja de estilos, aplica el tema guardado antes del primer pintado (D-04).
RF: RF-003, RF-004

### M-04 Botón con menú
Responsabilidad: `frontend/src/components/MenuButton.tsx`, botón circular con
`aria-haspopup="menu"` y `aria-expanded`, que despliega un `role="menu"` con opciones
`role="menuitemradio"` y `aria-checked`. Teclado: Intro, Espacio o flecha abajo abren y enfocan la
opción marcada; las flechas, Inicio y Fin recorren; Intro o Espacio eligen; Escape cierra y
devuelve el foco al botón; Tab cierra. Se cierra sin cambios al hacer clic fuera o al salir el
foco (`focusout` con `relatedTarget` fuera del componente). Como abrir otro menú mueve el foco
fuera del primero, nunca hay dos abiertos (RF-005) sin un estado compartido. Al desplegarse,
muestra bajo las opciones, fuera de `role="menu"` y con `aria-hidden="true"`, una pista de teclado
traducida: «↑ ↓ moverte · Intro elegir · Esc cerrar». El lector de pantalla no la lee porque ya
anuncia cómo se usa un menú.
RF: RF-002, RF-003, RF-005

### M-05 Barra superior
Responsabilidad: `frontend/src/components/TopBar.tsx` (`<header>`), con `LanguageMenu` (sustituye a
`LanguageSwitcher`: el botón muestra «ES», «EN» o «PT» y el menú los nombres de
`LANGUAGE_NAMES` con su `lang`) y `ThemeMenu` (sol o luna según `useTheme`; opciones «Claro» y
«Oscuro»). Se monta una vez en `App`, fuera de las pantallas, y las pantallas dejan de pintar
`LanguageSwitcher` (registro, cuenta creada, enlace no válido y muestra). Al elegir, el foco
vuelve al botón (RF-004 de `componentes-base-accesibles`).
RF: RF-001, RF-002, RF-003

### M-06 Envoltorio de campo
Responsabilidad: `frontend/src/components/fields/FieldShell.tsx`, la estructura común de
`TextField`, `PasswordField`, `CodeField` y `SelectField`: fila de etiqueta (nombre, asterisco con
`aria-hidden` y, si se pasa `help`, el `HelpTip`), el control, la ayuda visible (reglas de la
contraseña) y el hueco del error con `min-height` de una línea, siempre presente, que crece si el
texto no cabe (D-09). `Checkbox` usa el mismo hueco. Los ID de la ayuda, la descripción del «?» y
el error se juntan en `aria-describedby`.
RF: RF-013, RF-015, RF-016

### M-07 Botón de ayuda «?»
Responsabilidad: `frontend/src/components/fields/HelpTip.tsx`, botón circular «?» con nombre
accesible «Ayuda (<campo>)» y un globo `role="tooltip"` con la descripción. El globo se muestra con
`pointerenter`, `focus` o un toque, y se oculta con `pointerleave`, `blur`, un segundo toque o
Escape. El texto del globo está siempre en el DOM (oculto con CSS cuando no se ve), así el campo
puede tenerlo en su `aria-describedby` aunque el globo esté cerrado (D-08).
RF: RF-014

### M-08 Contraseña con ojo
Responsabilidad: cambiar el control de `PasswordField` a un botón de icono dentro del campo (ojo u
ojo tachado según `aria-pressed`), en posición absoluta a la derecha, con relleno a la derecha en
el `<input>` para que el texto no quede debajo. Conserva el `aria-label` y el `aria-pressed` de
D-10 de `componentes-base-accesibles` y la gestión de la salida de D-16.
RF: RF-018

### M-09 Selector propio
Responsabilidad: reescribir `SelectField` según el patrón «combobox de solo selección» de las guías
WAI-ARIA, sin `<select>` nativo. El control es un `<button type="button" role="combobox"
name=… value=…>` (D-06), con `aria-expanded`, `aria-controls`, `aria-activedescendant`,
`aria-required` y `aria-invalid`, y una lista `role="listbox"` con `role="option"` y
`aria-selected`. Teclado: Intro, Espacio, Alt+flecha abajo o flecha abajo abren; las flechas,
Inicio, Fin, Re Pág y Av Pág recorren; teclear salta a la primera opción que empieza por lo
escrito, sin distinguir mayúsculas ni tildes, acumulando las teclas pulsadas en menos de 500 ms;
Intro elige; Escape cierra sin cambios; Tab elige la resaltada y sale (patrón de la guía). La
opción resaltada se lleva a la vista dentro de la lista. La flecha gira 180° con una transición de
CSS sobre `[aria-expanded="true"]`. El clic en una opción usa `mousedown` con `preventDefault` para
que el foco no salga del control.
`useFormValidation.readValue` acepta también un `HTMLButtonElement` y lee su `value`, y `onBlur`
acepta su evento: es el único cambio en código compartido con otras features (D-06).
RF: RF-017

### M-10 Casillas de documentos y ventana
Responsabilidad: `frontend/src/components/DocumentDialog.tsx` con `<dialog>` y `showModal()`
(D-07): título, cuerpo con `overflow-y: auto` y el Markdown de `react-markdown`, y un botón de
cerrar. Se cierra con su botón, con Escape (evento `cancel`) y con un clic sobre el fondo
(`click` cuyo `target` es el propio `<dialog>`), y al cerrar devuelve el foco al enlace que lo
abrió. En `RegisterPage`, los `<details>` se sustituyen por el texto de la casilla con
`<Trans>` de `react-i18next`: «Acepto los <doc>términos y condiciones</doc>», donde `<doc>` es un
`<button type="button">` con aspecto de enlace subrayado (un botón dentro de una `<label>` no
marca la casilla al pulsarlo). Lo mismo para marketing, sin asterisco.
RF: RF-019, RF-020, RF-021

### M-11 Indicador de pasos
Responsabilidad: `frontend/src/registration/StepIndicator.tsx`, una lista `<ol>` de tres
elementos (número o check en un círculo, nombre visible del paso y línea de unión). Estados (colores de `docs/identidad-visual.md`, «Indicador de pasos»): completado (círculo en
relleno fuerte con check y borde de 2 px en tinta), actual (círculo en relleno fuerte con su número,
borde de 2 px en tinta y nombre en peso 600, `aria-current="step"`) y pendiente (círculo con borde
punteado de línea fuerte y su número). Un texto oculto a la vista da «Paso 2 de 3: Verificación», y cada elemento lleva el estado
en texto oculto («completado», «pendiente»). Recibe `current: 1 | 2 | 3 | "done"`; con `"done"`
los tres están completados. La línea se colorea con una transición de `transform: scaleX` y el
círculo con una de `background-color` y `border-color`.
RF: RF-006, RF-007, RF-008

### M-12 Asistente de registro y transición
Responsabilidad:
- `frontend/src/registration/RegistrationLayout.tsx`: el armazón de las rutas `/register`,
  `/register/continue` y `/register/done`, montado en `App`. Pinta el `StepIndicator` (fijo) y una
  zona de contenido con `overflow: hidden` donde va cada paso, con su `<h1>` (con `tabIndex={-1}`)
  y su tarjeta. Da a las pantallas, por contexto, el paso actual (`setStep`) y la función
  `goTo(direction, update)`.
- `frontend/src/registration/stepTransition.ts`: `runStepTransition(container, direction,
  update)`, con la misma forma que `document.startViewTransition` (D-02): copia el DOM del paso
  actual (`cloneNode(true)`), ejecuta `update` con `flushSync`, coloca la copia encima con `inert`
  y `aria-hidden`, y anima con `element.animate()` la copia (de 0 a ∓100 %) y el contenido nuevo
  (de ±100 % a 0) en 280 ms con `ease-out`; al acabar quita la copia. Sin animación si
  `prefers-reduced-motion: reduce` o si `element.animate` no existe (el paso cambia igual). Después
  lleva el foco al `<h1>` del paso nuevo, salvo que `update` haya dejado el foco dentro del
  contenido nuevo (errores de RF-003 y RF-011 de `registro-flujo`).
- Puntos de cambio de paso: formulario → verificación y contraseña → cuenta creada (al `navigate`),
  verificación → contraseña (al aceptar el código) y contraseña → verificación (al rechazar el
  código). Un escucha de `popstate` en el armazón, registrado antes que el del enrutador, copia el
  paso actual con «Atrás» y anima hacia atrás tras el pintado (D-03).
- Reorganización de pantallas: `RegisterPage`, `VerifyPage` (con su `CodeForm` e `InvalidLink`),
  `PasswordStep` y `DonePage` dejan de pintar `<main>` y el selector de idioma y pintan su título y
  su tarjeta dentro del armazón. En el paso de contraseña ya no se ven el título ni el texto de la
  verificación: el paso tiene su propio `<h1>` (el `<h2>` actual pasa a `<h1>`). El enlace no válido
  muestra el indicador en el paso 2.
- Botón principal: `Button` admite `icon="next"` (flecha derecha tras el texto, `aria-hidden`) y
  `variant`. Cada paso alinea su botón principal a la derecha; el de reenvío es secundario (borde y
  texto de acción, sin relleno).
RF: RF-007, RF-009, RF-010, RF-011, RF-012

### M-13 Zona de mensajes del paso
Responsabilidad: `frontend/src/components/MessageZone.tsx`, un contenedor con `min-height` de una
línea, siempre presente, encima del botón principal de cada paso, que agrupa el mensaje general
(`FormMessage`), el aviso de espera por límite, el de bloqueo y el de código caducado. El tiempo
restante del código («El código caduca en 12:30») va también en ella, porque se sustituye por el de
caducado y así no salta. No cambia los textos, el foco ni los anuncios de `registro-flujo`.
RF: RF-023

### M-14 Textos de ayuda y nombres nuevos
Responsabilidad: claves nuevas en `es`, `en` y `pt-BR`: `topBar.*` (nombres de los botones y las
opciones de tema), `steps.*` (nombres de los pasos, «Paso {{current}} de {{total}}», estados),
`help.*` (nombre del «?» y una descripción por campo, S-03), `dialog.close`, y los textos de las
casillas con su marca `<doc>`. Descripciones en español (las otras dos lenguas, con el mismo
sentido):
- Nombre completo: «Tal como quieres que aparezca en tu cuenta.»
- Fecha de nacimiento: «Se usa para comprobar que tienes la edad mínima para registrarte.»
- Correo: «Lo usarás para iniciar sesión. Si puedes registrarte con él, recibirás en él un código de
  verificación.»
- País: «El país donde resides.»
- Código: «Los 6 dígitos del correo de verificación. Puedes pegarlo entero.»
- Contraseña: «La usarás para iniciar sesión. Debajo del campo tienes las reglas que debe cumplir.»
RF: RF-014, RF-019, RF-020

### M-15 Estilos
Responsabilidad: `base.css` deja de dar fondo de bloque a cualquier `main`, `form` y `section`, y
lo da a `.card`. Estilos nuevos por componente (clases con prefijo del componente, en
`frontend/src/styles/components.css`) con las variables de `tokens.css`: barra, menú, indicador,
campos (alto 40 px, nombre encima, asterisco en el color de error de alarma P1 junto al nombre, como
en la imagen), globo, selector, ventana, zona de mensajes y botones con icono. Ancho máximo de la
tarjeta, 640 px.
RF: RF-022

## Modelo de datos
Sin cambios en el servidor. En el navegador:
- `localStorage["confiabilidad.theme"]`: `"light"` o `"dark"`; ausente si nunca se eligió.
- `<html data-theme="light|dark">`: solo cuando hay tema elegido.
- Estado del asistente (en memoria, en `RegistrationLayout`): paso actual `1 | 2 | 3 | "done"`.

## Decisiones

### D-01 Animación propia con la Web Animations API
Elegida: copiar el paso saliente y animar copia y paso nuevo con `element.animate()`.
Descartada: `document.startViewTransition` (*view transitions*).
Motivo: la spec exige el mismo desplazamiento en todos los navegadores y en el escritorio (RF-009,
C-03). El motor web de Tauri en Linux (WebKitGTK) y Firefox anteriores a la 144 no la admiten,
mientras que la Web Animations API funciona en todos ellos.

### D-02 Copia del DOM en lugar de mantener montados los dos pasos
Elegida: `runStepTransition` hace una copia del DOM saliente (inerte y oculta al lector) antes de
aplicar el cambio con `flushSync`, la misma estrategia que sigue `startViewTransition` con su
instantánea.
Descartada: mantener montado el componente React del paso anterior durante la animación.
Motivo: el paso anterior pertenece a otra ruta o a otro estado de `VerifyPage`; mantenerlo montado
obligaría a duplicar su estado y podría repetir peticiones. La copia es solo imagen: sin
manejadores, `inert` (nada enfocable, RF-011) y con `aria-hidden`. La copia no lleva los valores
escritos (`cloneNode` copia atributos, no propiedades), lo que es irrelevante en 280 ms y evita
copiar la contraseña al DOM.

### D-03 «Atrás» del navegador con un escucha previo al del enrutador
Elegida: el armazón se suscribe a `popstate` antes de que el enrutador vuelva a pintar, copia el
paso en ese momento y anima hacia atrás en el efecto de diseño tras el pintado.
Descartada: no animar «Atrás».
Motivo: la spec pide transición hacia atrás también con «Atrás» del navegador (RF-007, RF-009). El
enrutador vuelve a pintar de forma asíncrona tras el evento, así que la copia se toma antes del
cambio.

### D-04 Script en línea para el tema antes del primer pintado
Elegida: un script mínimo en `index.html`, antes del CSS, que lee `confiabilidad.theme` y, si es
`light` o `dark`, pone `data-theme` en `<html>`, dentro de un `try` (almacenamiento bloqueado =
sin tema guardado).
Descartada: aplicarlo desde React al arrancar.
Motivo: React pinta después de cargar el JS, y antes se vería el tema del sistema (RF-004, C-08).
La app de escritorio tiene `csp: null`, así que el script en línea no se bloquea; si se activa una
CSP, habrá que añadir su hash.

### D-05 Botón con menú de opciones exclusivas para idioma y tema
Elegida: `menu` con `menuitemradio`; el idioma cambia solo al elegir una opción.
Descartada: mantener el grupo de botones del idioma (D-06 de `componentes-base-accesibles`) o usar
un `listbox`.
Motivo: la spec pide un botón con la abreviatura que despliega las opciones (RF-002). El menú
conserva lo que justificaba D-06: recorrer con las flechas no cambia el idioma, solo Intro, Espacio
o clic (WCAG 3.2.2).

### D-06 Selector como botón con `role="combobox"` y `name`
Elegida: el control del selector es un `<button>` con `name` y `value`, así que aparece en
`form.elements` y `useFormValidation` lo encuentra, lee su valor y le da el foco por su `name`, como
a los demás campos.
Descartada: un `<div role="combobox">` con un `<input type="hidden">` aparte.
Motivo: el campo oculto no admite el foco, así que llevar el foco al primer error (RF-003 de
`registro-flujo`) exigiría cambiar `useFormValidation` con un caso especial. HTML permite
`role="combobox"` en un `<button>`. Coste: se pierde el autocompletado de país del navegador
(`autocomplete="country"`), que solo funciona en `<select>` e `<input>`.

### D-07 Ventana con `<dialog>` nativo
Elegida: `<dialog>` con `showModal()`.
Descartada: una ventana propia con trampa de foco y `inert` en el resto.
Motivo: `showModal()` ya deja inerte el resto de la página, retiene el foco y cierra con Escape
(RF-021), en todos los navegadores admitidos y en WebKitGTK. En los tests (jsdom) se añade un
sustituto mínimo de `showModal` y `close` en `setupTests.ts`.

### D-08 Descripción del «?» siempre presente y referenciada
Elegida: el texto del globo está siempre en el DOM; el campo y el botón «?» lo referencian con
`aria-describedby`. Al lector le llega al entrar en el campo aunque nunca se abra el globo.
Descartada: crear el globo solo al mostrarlo.
Motivo: RF-014 pide que la descripción se lea al llegar al campo, no solo al abrir el globo.

### D-09 Hueco de error con altura mínima
Elegida: `min-height` igual a una línea del mensaje (`1lh`, con `1.5em` de reserva) en el
contenedor del error, siempre pintado, y el `<p>` dentro solo si hay error.
Descartada: una altura fija con el texto cortado.
Motivo: la spec pide que crezca sin cortar (RF-016, decisión del usuario). El `<p>` sigue
apareciendo y desapareciendo, así que `aria-describedby` y los anuncios no cambian.

### D-10 Fondo de la ventana opaco
Elegida: fondo del `<dialog>` (`::backdrop`) en el color de lienzo, opaco, y la ventana como una
tarjeta de bloque.
Descartada: un fondo semitransparente que deja ver el formulario.
Motivo: la guía prohíbe las transparencias. Si el usuario prefiere ver el formulario detrás, es
una desviación de la guía que debe aprobar en M-01.

### D-11 Asterisco en color de alarma P1
Elegida: el asterisco junto al nombre, en el color de alarma P1, como en la imagen.
Descartada: asterisco en texto secundario.
Motivo: la imagen lo pinta en rojo, y alarma P1 es el único rojo de la paleta. Choca con «los
colores de alarma no se usan para nada más»: aceptado por el usuario en T-001, junto con los errores
de campo en P1, como excepción escrita en la guía. La obligatoriedad no depende del color: está el
asterisco y la leyenda.

### D-12 Campos con radio de 4 px
Elegida: mantener el radio de 4 px que ya tienen los campos.
Descartada: los 8 px de la imagen o la píldora.
Motivo: la guía solo pide píldora para el buscador y no regula los campos; cambiarlo afectaría a
toda la aplicación y a una regla que no está en esta spec. Se anota en M-01 para que quede escrito.

### D-13 El tema en uso se lee de `matchMedia` cuando no hay elección
Elegida: `useTheme` devuelve el elegido o, si no hay, el de `matchMedia("(prefers-color-scheme:
dark)")`, y escucha su cambio.
Descartada: copiar el tema del sistema en `localStorage` al arrancar.
Motivo: copiarlo convertiría el tema del sistema en una elección del usuario y dejaría de seguir al
sistema operativo, en contra de RF-004.

### D-14 La guía visual se actualiza antes que el código
Elegida: la primera tarea (M-01) redacta las piezas nuevas en `docs/identidad-visual.md` y el
usuario las aprueba antes de implementar estilos.
Descartada: documentarlas al final.
Motivo: `AGENTS.md` pide preguntar y actualizar la guía cuando un caso no está cubierto; así las
excepciones de D-10, D-11 y D-12 se deciden antes de escribir el CSS.

## Estrategia de tests
- **Unitario (Vitest)**: `theme.ts` (leer, guardar, borrar un valor no válido, aplicar
  `data-theme`), el script de `index.html` (se ejecuta su texto en jsdom con distintos valores
  guardados), la búsqueda al teclear del selector (sin tildes, acumulada), `runStepTransition`
  (copia `inert` y `aria-hidden`, sin animación con movimiento reducido o sin `animate`, foco al
  título salvo que el foco ya esté en el contenido nuevo, la copia se quita al terminar) y
  `tokens.css` (la paleta oscura bajo `data-theme` y bajo la consulta del sistema, como el test
  actual).
- **Componente (Testing Library + user-event, teclado simulado como D-12 de
  `componentes-base-accesibles`)**: `MenuButton`, `LanguageMenu`, `ThemeMenu`, `TopBar`,
  `HelpTip`, `FieldShell` (hueco siempre presente), `PasswordField` (iconos y `aria-pressed`),
  `SelectField` (todo el teclado, el clic, el giro por `aria-expanded`, `name` y `value`),
  `DocumentDialog` (abrir, Escape, clic en el fondo, foco de vuelta, la casilla no cambia),
  `StepIndicator` (estados, `aria-current`, «Paso N de 3», `"done"`) y `MessageZone`.
- **Integración de pantallas**: los tests actuales de `RegisterPage`, `VerifyPage` y
  `PasswordStep` se adaptan a la nueva estructura sin cambiar lo que comprueban de
  `registro-flujo`. Se añaden los recorridos formulario → verificación → contraseña → cuenta
  creada, contraseña → verificación por rechazo y «Atrás» del navegador, comprobando el indicador,
  la dirección de la animación (con `element.animate` simulado), el foco en el título y que no
  queda nada enfocable de la copia.
- **Accesibilidad automática**: los tests de `axe-core` existentes (`registration/a11y.test.tsx`,
  `showcase/a11y.test.tsx`) se amplían con la barra superior, el menú abierto, el selector
  desplegado, el globo visible y la ventana abierta, en `data-theme="light"` y `"dark"` (CF-2).
- **Manual**: CF-3 (recorrido completo solo con teclado) y CF-4 (revisión visual en ambos temas,
  tres idiomas y con y sin movimiento reducido, también en la app de escritorio) quedan en el
  `HUMAN_TODO.md` de la feature, porque jsdom no pinta ni mide.
- **Mutación**: cada tarea cierra con su mutante, como en el resto de features.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-05 | Componente (`TopBar`) e integración en `App` |
| RF-002 | M-04, M-05 | Componente (`MenuButton`, `LanguageMenu`) |
| RF-003 | M-02, M-03, M-04, M-05 | Componente (`ThemeMenu`) y unitario (`theme.ts`) |
| RF-004 | M-03 | Unitario (`theme.ts`, script de `index.html`, `tokens.css`) |
| RF-005 | M-04 | Componente (`MenuButton`: Escape, clic fuera, foco fuera, dos menús) |
| RF-006 | M-11 | Componente (`StepIndicator`) |
| RF-007 | M-11, M-12 | Integración de pantallas (avance y retroceso) |
| RF-008 | M-11, M-12 | Componente (`"done"`) e integración (cuenta creada) |
| RF-009 | M-12 | Unitario (`runStepTransition`) e integración (dirección) |
| RF-010 | M-12, M-15 | Unitario (sin animación con movimiento reducido) y manual (CF-4) |
| RF-011 | M-12 | Unitario e integración (foco al título, copia inerte) |
| RF-012 | M-02, M-12 | Integración (un botón principal por paso, sin «Anterior») |
| RF-013 | M-06 | Componente (`FieldShell`) |
| RF-014 | M-07, M-14 | Componente (`HelpTip`) e integración (campos del registro sí, casillas y muestra no) |
| RF-015 | M-06 | Componente (`PasswordField`: reglas visibles junto al «?») |
| RF-016 | M-06 | Componente (`FieldShell`, `Checkbox`: hueco presente con y sin error) y manual (CF-4) |
| RF-017 | M-09 | Componente (`SelectField`) y unitario (búsqueda al teclear) |
| RF-018 | M-02, M-08 | Componente (`PasswordField`) |
| RF-019 | M-10, M-14 | Integración (`RegisterPage`: sin texto desplegado, enlace abre la ventana) |
| RF-020 | M-10, M-14 | Integración (`RegisterPage` con y sin documento de marketing) |
| RF-021 | M-10 | Componente (`DocumentDialog`) |
| RF-022 | M-01, M-15 | Accesibilidad automática en ambos temas (CF-2) y manual (CF-4, CF-5) |
| RF-023 | M-13 | Componente (`MessageZone`) e integración (mensajes en la zona) |

## RF sin cobertura
Ninguno.
