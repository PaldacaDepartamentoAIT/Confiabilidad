# Tareas: presentacion-registro
Estado: aprobado

«Suite verde» = `pnpm --filter frontend test:coverage` (líneas ≥ 80 %), `typecheck`, `lint` y
`exec prettier --check .` sin errores, y, desde T-005, también `pnpm --filter frontend test:visual`.
En cada tarea se prueba al menos un mutante del código que introduce y debe hacer fallar sus tests.
Las rutas son relativas a `frontend/src/` salvo que se indique otra cosa.

## E-01 Botón desactivado
- [x] T-001 Aspecto de botón desactivado
  RF: RF-002 | Depende de: — | Archivos: 3
  Archivos: `components/Button.css`, `components/buttonCss.test.ts`, `frontend/vite.config.ts`.
  Hecho cuando: `.btn:disabled` y `.btn[aria-disabled="true"]` tienen `opacity: 0.6` y `cursor: not-allowed`; el
  hover del primario y del secundario solo se aplica a los botones que no están bloqueados; el test lee el CSS y
  lo comprueba (por eso `Button.css` entra en `css.include` de `vite.config.ts`); suite verde.
  Decisiones: el aspecto es el de antes de la limpieza de `base.css`: 60 % y cursor de no permitido, ahora en
  `Button.css` y para `disabled` y para `aria-disabled` (que ya lo tenía) — [Cierto]. El hover se excluye con
  `:not(:disabled):not([aria-disabled="true"])` en lugar de pisarlo después, para que un botón bloqueado no
  cambie ni siquiera durante la transición — [Probable]. El test quita los comentarios del CSS antes de
  analizarlo (un comentario delante de una regla se leía como parte de su selector). `Button.css` entra en
  `css.include` de Vitest como `field.css` y `DocumentModal.css`. Las 40 pruebas visuales, incluida la comparación
  exacta con las referencias, siguen pasando: el aspecto en reposo no cambia — [Cierto]. Mutantes muertos:
  opacidad 0,6 → 0,8, hover del principal sin excluir el bloqueado y sin la regla de `disabled` nativo.
- [x] T-002 Catálogo y guía: botones desactivados
  RF: RF-008 | Depende de: T-001 | Archivos: 3
  Archivos: `showcase/sections/ButtonsSection.tsx`, `showcase/ShowcasePage.test.tsx`, `docs/identidad-visual.md`.
  Hecho cuando: el catálogo muestra un botón desactivado primario y uno secundario, con `disabled`; la guía
  describe el aspecto de desactivado; suite verde.
  Decisiones: los dos botones del catálogo se llaman «Guardar bloqueado» y «Cancelar bloqueado» y van en una
  fila aparte, debajo de los botones normales y del que está procesando; la fila nueva de la guía se llama
  «Desactivado» y describe el 60 %, el cursor y la ausencia de hover — [Probable]. Verificado en un navegador
  real: ambos con opacidad 0,6, cursor de no permitido y sin cambio de color al pasar el puntero (fondo
  `rgb(84, 108, 140)` antes y después), mientras que el botón activo se oscurece y muestra la mano — [Cierto].
  Las 40 pruebas visuales siguen pasando, `axe` incluido: no evalúa el contraste de un botón desactivado.
  Mutante muerto: el secundario sin `disabled`.

## E-02 Verificación: botones en una fila y hueco reservado
- [x] T-003 Botones de la verificación en una fila
  RF: RF-001 | Depende de: T-001 | Archivos: 3
  Archivos: `registration/VerifyPage.tsx`, `registration/verify.css`, `registration/VerifyPage.test.tsx`.
  Hecho cuando: «Enviar otro código» y «Verificar» están en un contenedor `.form-actions` dentro del
  formulario del código, con el secundario antes que el principal; el de reenviar es `type="button"`, no envía el
  formulario y conserva su estado, su cuenta atrás y su bloqueo; el CSS alinea la fila a la derecha con 10 px y,
  por debajo de 480 px, la pone en columna invertida con los botones a todo el ancho; suite verde.
  Decisiones: `CodeForm` recibe el botón secundario como propiedad (`secondaryAction`) y lo pinta antes de
  «Verificar» en `.form-actions`; el estado, la cuenta atrás y el bloqueo del reenvío siguen en `VerifyPage` y
  el botón es `type="button"` (el de `Button` por defecto), así que no envía el código — [Cierto]. Las
  reglas de la fila (alineación a la derecha, 10 px, columna invertida a todo el ancho por debajo de 480 px)
  están en `registration/verify.css` y se fijan en Chromium en T-005, no en un test de jsdom, porque leer
  `verify.css` desde Vitest habría exigido tocar `vite.config.ts` (fuera de los 3 archivos de la tarea) —
  [Probable]. Verificado en un navegador real con la API simulada: a 1000 px los botones están en la misma fila,
  el secundario a la izquierda, 10 px entre ellos y pegados al borde derecho; a 420 px quedan en columna, ambos de
  290 px, con «Verificar» arriba (y a 46 px de distancia el reenviar) — [Cierto]. Se observa que el recuento
  «Códigos que aún puedes pedir» queda pegado a los botones: lo ajusta T-004. Mutantes muertos: orden invertido
  de la fila, el reenvío como botón de envío y la fila con otra clase.
- [x] T-004 Hueco reservado del mensaje de reenvío
  RF: RF-003 | Depende de: T-003 | Archivos: 3
  Archivos: `registration/VerifyPage.tsx`, `registration/verify.css`, `registration/VerifyPage.test.tsx`.
  Hecho cuando: debajo del recuento de códigos (o del aviso de que no quedan, con su enlace) hay un contenedor con
  `min-height: calc(2 * 1.45em)` que contiene el mensaje informativo, el de espera y el de error del reenvío; el
  aviso de bloqueo, el error del formulario y el de «no quedan códigos» siguen donde estaban; suite verde.
  Decisiones: el hueco es un `div.resend-slot` que está siempre, vacío, después del recuento (o del aviso de que
  no quedan códigos y su enlace) y contiene el `FormMessage` del reenvío y el estado de espera; el mensaje del
  reenvío ya no va encima del formulario. `min-height: calc(2 * 1.45em)` (unos 41 px a 14 px). El recuento
  lleva la clase `resend-count` con 14 px de margen superior, para que no quede pegado a los botones —
  [Probable]. La lectura de `verify.css` queda para Chromium (T-005), por lo mismo que en T-003. Verificado en
  un navegador real con la API simulada: a 1000 px y a 420 px el alto de la card es el mismo (376 px y 442 px)
  antes y después de que aparezca el mensaje informativo, y el hueco mide 41 px — [Cierto]. Mutantes muertos:
  el hueco solo existe con mensaje, otra clase para el hueco y el mensaje otra vez sobre el formulario. El
  fallo del primer intento de verificación en el navegador era de mi script (con `StrictMode` la pantalla pide
  el estado dos veces), no de la aplicación.

## E-02b Prueba de la verificación en Chromium
- [ ] T-005 Prueba en Chromium: botones, desactivado y altura de la verificación
  RF: RF-001, RF-002, RF-003 | Depende de: T-004 | Archivos: 2
  Archivos: `frontend/visual/registration.visual.test.ts`, `docs/identidad-visual.md`.
  Hecho cuando: en Chromium, en claro y oscuro y con la API simulada, la verificación muestra «Enviar otro
  código» a la izquierda y «Verificar» a la derecha en la misma fila, en dos filas a todo el ancho con «Verificar»
  arriba a 420 px; un botón bloqueado se ve con opacidad 0,6, cursor de no permitido y sin cambiar de color al
  pasar el puntero; la altura de la card es idéntica con y sin mensaje de reenvío; la guía recoge las acciones
  y el hueco; `pnpm --filter frontend test:visual` pasa.

## E-03 Registro con carga y fundido
- [ ] T-006 Fundido de la card y carga lista
  RF: RF-004, RF-005, RF-006 | Depende de: — | Archivos: 3
  Archivos: `layouts/PublicPage.tsx`, `layouts/PublicPage.css`, `layouts/PublicPage.test.tsx`.
  Hecho cuando: `PublicPage` con `ready={false}` no pinta nada y con `ready` (por defecto verdadero) pinta la card
  con una animación de entrada de 0,2 s (`@keyframes public-in`); el movimiento reducido lo anula la regla
  global de `base.css`; suite verde.
- [ ] T-007 Fundido de un contenido que cambia dentro de la card
  RF: RF-005 | Depende de: T-006 | Archivos: 3
  Archivos: `layouts/Fade.tsx`, `layouts/Fade.test.tsx`, `layouts/PublicPage.css`.
  Hecho cuando: `Fade` es un contenedor que, al cambiar su `key`, vuelve a montarse y repite la animación de
  entrada de 0,2 s, y no cambia el aspecto del contenido que envuelve; suite verde.
- [ ] T-008 Plazo de 10 s
  RF: RF-004 | Depende de: — | Archivos: 2
  Archivos: `registration/useDeadline.ts`, `registration/useDeadline.test.ts`.
  Hecho cuando: `useDeadline(activo, ms, alVencer)` llama a `alVencer` una vez pasados `ms` mientras `activo` sea
  verdadero, no la llama si `activo` pasa a falso antes ni tras desmontarse, y reinicia el plazo si `activo`
  vuelve a ser verdadero; suite verde.
- [ ] T-009 Registro con carga, plazo y fundido
  RF: RF-004, RF-005, RF-007 | Depende de: T-006, T-008 | Archivos: 2
  Archivos: `registration/RegisterPage.tsx`, `registration/RegisterPage.test.tsx`.
  Hecho cuando: mientras se cargan las opciones no hay card ni título; al llegar, la card entra con fundido; si
  la carga falla o pasan 10 s sin respuesta, la card aparece con el error de conexión y una respuesta que llegue
  después se ignora; el flujo, los textos, las validaciones y los datos enviados no cambian; suite verde.

## E-03b Verificación y cuenta creada con carga y fundido
- [ ] T-010 Verificación y enlace no válido con carga, plazo y fundido
  RF: RF-004, RF-005, RF-007 | Depende de: T-006, T-007, T-008 | Archivos: 2
  Archivos: `registration/VerifyPage.tsx`, `registration/VerifyPage.test.tsx`.
  Hecho cuando: mientras se carga el estado no hay card; al llegar entra con fundido; con error o pasados 10 s sin
  respuesta aparece con el error de conexión; el enlace no válido entra con fundido al pintarse; el cambio del
  código a la contraseña se anima con `Fade`; el flujo no cambia; suite verde.
- [ ] T-011 Cuenta creada con fundido
  RF: RF-005, RF-007 | Depende de: T-006 | Archivos: 2
  Archivos: `registration/DonePage.tsx`, `registration/DonePage.test.tsx`.
  Hecho cuando: la pantalla de cuenta creada entra con fundido en cuanto se pinta y su texto no cambia; suite
  verde.

## E-04 Barra superior compartida y comprobación final en navegador
- [ ] T-012 Barra superior compartida
  RF: RF-009, RF-007 | Depende de: T-009, T-010, T-011 | Archivos: 6
  Archivos: `App.tsx`, `App.test.tsx`, `registration/RegisterPage.tsx`, `registration/VerifyPage.tsx`,
  `registration/DonePage.tsx`, `registration/a11y.test.tsx`.
  Hecho cuando: `App` pinta un solo `PublicLayout` alrededor de las pantallas del registro y estas ya no lo
  pintan; hay una sola barra con banner, idioma y tema, que es el mismo nodo al pasar de una pantalla a otra; el
  catálogo conserva su propia barra; los tests previos pasan, con los de la barra movidos a `App`; suite verde.
  Excepción: 6 archivos en lugar de 3. Sacar la barra de las páginas y pintarla en `App` es un único cambio
  atómico: con solo uno de los dos habría dos barras o ninguna entre commits, y los tests de las páginas que
  miraban el banner pasan a `App`.
- [ ] T-013 Prueba en Chromium: carga, fundido, barra y movimiento reducido
  RF: RF-004, RF-005, RF-006, RF-009 | Depende de: T-005, T-012 | Archivos: 2
  Archivos: `frontend/visual/registration.visual.test.ts`, `docs/identidad-visual.md`.
  Hecho cuando: en Chromium, en claro y oscuro y con la API simulada y retenida, mientras se espera la
  respuesta de `/register` y de `/register/continue` no hay ninguna card ni título; al llegar, la opacidad de la
  card pasa de 0 a 1 en unos 0,2 s; pasados 10 s sin respuesta aparece con el error de conexión; la barra
  superior es el mismo nodo antes y después de navegar; con movimiento reducido no hay animación; `axe` con
  contraste no halla violaciones en las pantallas afectadas; la guía recoge el fundido; `pnpm --filter frontend
  test:visual` pasa.

## Entregas
Rama de integración: feat/presentacion-registro (los PR de las entregas van contra ella; ver `AGENTS.md`)

- E-01 Cualquier botón bloqueado se ve desactivado, y el catálogo lo muestra.
  Tareas: T-001, T-002 | Líneas estimadas: 130 | Rama: feat/presentacion-registro-desactivado
  Cómo probarlo: `pnpm --filter frontend dev`, abrir http://localhost:5173/ y, en la sección de botones, ver los
  dos botones desactivados atenuados y sin cambio de color al pasar el puntero.
- E-02 La verificación del código tiene sus dos botones en una fila y el mensaje de reenvío no cambia la altura.
  Tareas: T-003, T-004 | Líneas estimadas: 230 | Rama: feat/presentacion-registro-verificacion
  Cómo probarlo: con el backend levantado, abrir el enlace de verificación (`/register/continue#<PUBLIC_ID>`), ver
  los botones en una fila y pulsar «Enviar otro código»: el mensaje aparece debajo del recuento sin mover la card.
- E-02b La verificación se comprueba en un navegador real.
  Tareas: T-005 | Líneas estimadas: 180 | Rama: feat/presentacion-registro-prueba-verificacion
  Cómo probarlo: `pnpm --filter frontend test:visual`.
- E-03 El registro no muestra su card vacía mientras carga y entra con fundido.
  Tareas: T-006, T-007, T-008, T-009 | Líneas estimadas: 330 | Rama: feat/presentacion-registro-carga
  Cómo probarlo: con el backend levantado, abrir http://localhost:5173/register: la card aparece de golpe con un
  fundido, sin verse vacía; con la red lenta (herramientas del navegador) solo se ve la barra superior.
- E-03b La verificación, el enlace no válido y la cuenta creada también.
  Tareas: T-010, T-011 | Líneas estimadas: 170 | Rama: feat/presentacion-registro-carga-verificacion
  Cómo probarlo: abrir `/register/continue#<PUBLIC_ID>` y `/register/done`: entran con fundido y el cambio del
  código a la contraseña también.
- E-04 La barra superior no parpadea al cambiar de pantalla y todo se comprueba en un navegador real.
  Tareas: T-012, T-013 | Líneas estimadas: 240 | Rama: feat/presentacion-registro-barra
  Cómo probarlo: `pnpm --filter frontend test:visual`; navegar del registro a la verificación y ver que la barra
  no se mueve.
  Nota: E-03 y E-04 rozan las 400 líneas; si una entrega ya implementada las rebasa, se divide en dos
  (E-XX y E-XXb) según `AGENTS.md`.

## RF sin tarea
Ninguno.
