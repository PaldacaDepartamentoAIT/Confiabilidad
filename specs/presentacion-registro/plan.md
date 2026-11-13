# Plan: presentacion-registro
Estado: borrador

## Módulos

### M-01 Aspecto de botón desactivado (`components/Button.css`, `showcase/sections/ButtonsSection.tsx`)
Responsabilidad: un botón bloqueado, con el atributo `disabled` o con `aria-disabled="true"`, se ve atenuado al
60 % y con el cursor de no permitido, y no cambia de color al pasar el puntero; el catálogo muestra un botón
desactivado de cada variante.
RF: RF-002, RF-008

### M-02 Carga y fundido de las pantallas públicas (`layouts/PublicPage.tsx`, `PublicPage.css`, `registration/useDeadline.ts`)
Responsabilidad: `PublicPage` recibe si su pantalla está lista; hasta entonces no pinta la card, y al pintarla la
anima con un fundido de entrada de 0,2 s. Un contenedor `Fade` anima del mismo modo un contenido que cambia
dentro de la card (del código a la contraseña). `useDeadline` avisa si pasan 10 s sin respuesta, para mostrar el
error de conexión que ya existe.
RF: RF-004, RF-005, RF-006

### M-03 Barra superior compartida (`App.tsx`, páginas del registro)
Responsabilidad: la barra superior se pinta una sola vez, en `App`, alrededor de las pantallas del registro, y
las páginas dejan de pintarla; así no se repinta ni parpadea al cambiar de pantalla y conserva idioma y tema.
RF: RF-009

### M-04 Verificación del código (`registration/VerifyPage.tsx`, `registration/verify.css`)
Responsabilidad: «Enviar otro código» y «Verificar» van en una misma fila (`.form-actions`), alineados a la
derecha y con el secundario a la izquierda, y por debajo de 480 px en dos filas a todo el ancho con «Verificar»
arriba; los mensajes del reenvío (informativo, de espera y de error) pasan a un hueco reservado de dos líneas
debajo del recuento de códigos. Además, esta pantalla y la de registro piden `ready` y el plazo de 10 s a M-02.
RF: RF-001, RF-003, RF-004, RF-005

### M-05 Registro y cuenta creada (`registration/RegisterPage.tsx`, `registration/DonePage.tsx`)
Responsabilidad: usan `ready`, el plazo de 10 s (el registro) y el fundido de M-02, sin cambiar flujo, textos,
validaciones ni datos.
RF: RF-004, RF-005, RF-007

### M-06 Prueba en navegador real (`frontend/visual/registration.visual.test.ts`)
Responsabilidad: en Chromium y con la API simulada, comprueba lo que jsdom no puede: botones en una línea y su
orden, disposición a 420 px, botón desactivado, altura de la card sin cambios al aparecer el mensaje de
reenvío, ninguna card vacía mientras carga, fundido, barra superior que no se vuelve a montar, movimiento reducido
y accesibilidad.
RF: RF-001, RF-002, RF-003, RF-004, RF-005, RF-006, RF-009

### M-07 Guía (`docs/identidad-visual.md`)
Responsabilidad: filas nuevas para el botón desactivado, las acciones de la verificación, el hueco del mensaje y
el fundido de las pantallas públicas.
RF: RF-001, RF-002, RF-003, RF-004, RF-005

## Modelo de datos
No hay: es solo frontend.

## Decisiones

### D-01 La barra superior se pinta en `App`, no en cada página
Elegida: `App` envuelve las tres pantallas del registro con un único `PublicLayout`; las páginas dejan de usarlo.
Descartada: dejar `PublicLayout` dentro de cada página y evitar el parpadeo con CSS.
Motivo: cada cambio de ruta desmonta la página y su barra y monta otra; un elemento que se repinta no puede
garantizar que no parpadee (RF-009). Uno solo que persiste, sí. El coste: las pruebas de página que miraban la
barra dentro de la página se mueven a `App`. La página de muestra (catálogo) sigue con su propia barra.

### D-02 La card no se pinta hasta que la pantalla está lista
Elegida: `PublicPage` con la propiedad `ready`; si es falsa, devuelve `null` y solo se ve la barra.
Descartada: pintar la card con `opacity: 0` o `visibility: hidden` mientras carga.
Motivo: una card invisible sigue ocupando sitio (la página salta al aparecer), y sigue en el árbol de
accesibilidad si se olvida ocultarla. Sin DOM no hay ninguna de las dos cosas.

### D-03 El fundido es una animación CSS de entrada al montar
Elegida: `@keyframes public-in` de 0,2 s sobre la card (y sobre el contenedor `Fade`), que se ejecuta al
montarse.
Descartada: una transición controlada por estado (montar con la clase apagada y encenderla en otro render).
Motivo: un solo render y sin parpadeo. El movimiento reducido (RF-006) lo cubre la regla global de `base.css`
(`animation: none !important`), sin código propio; se comprueba en Chromium porque ya falló con el botón de tema
cuando una regla local con `!important` ganaba a la global.

### D-04 El cambio interno de la verificación se anima con una `key`
Elegida: el contenido bajo el título va en un contenedor `Fade` con `key` según el paso (código o contraseña):
al cambiar la `key` React lo monta de nuevo y se anima solo.
Descartada: una librería de transiciones.
Motivo: no se añaden dependencias sin preguntar (`AGENTS.md`) y no hace falta una.

### D-05 El plazo de 10 s lo vigila `useDeadline` y fija el error de red existente
Elegida: un hook que, mientras la pantalla está cargando, llama a una función pasados 10 s; las dos páginas que
cargan la usan para pasar a su estado de error de conexión. Una respuesta que llegue después se ignora.
Descartada: dejar que cada petición tenga su propio tiempo máximo en el cliente HTTP.
Motivo: el plazo es de la pantalla (qué se ve), no de la petición. Ignorar la respuesta tardía evita que la card
cambie de un error a un formulario sin que la persona haga nada; recargar la página lo reintenta.

### D-06 El botón de reenviar pasa dentro del formulario del código
Elegida: `CodeForm` recibe el botón secundario y pinta ambos botones en `.form-actions`; el reenvío sigue siendo
estado y lógica de `VerifyPage`, y el botón es `type="button"` para no enviar el formulario.
Descartada: dejarlo fuera y alinearlo con el submit con un atributo `form=` o con un contenedor común.
Motivo: es lo único que da una sola fila sin duplicar botones ni mover el submit fuera de su formulario.

### D-07 En pantallas estrechas, columna invertida y a todo el ancho
Elegida: por debajo de 480 px, `flex-direction: column-reverse` y los botones a todo el ancho.
Descartada: reordenar el HTML o duplicar los botones para que el orden visual y el de Tab coincidan.
Motivo: con el orden `[reenviar, verificar]` en el HTML (secundario antes que principal, como en la guía), la
columna invertida pone «Verificar» arriba. Coste conocido: en esa disposición Tab recorre primero el botón de
abajo; se documenta y se asume.

### D-08 El hueco del mensaje de reenvío mide dos líneas de texto
Elegida: un contenedor debajo del recuento con `min-height: calc(2 * 1.45em)` (dos interlíneas del texto de la
card, unos 40 px a 14 px) que contiene el mensaje informativo, el de espera y el de error del reenvío.
Descartada: una altura fija en píxeles, que no sigue el tamaño de la letra.
Motivo: cuadra con S-02 y con el patrón de la reserva del error de los campos; un mensaje más largo hace crecer
la card, como dice RF-003.

### D-09 El aspecto de desactivado vive en el componente de botón
Elegida: en `Button.css`, `.btn:disabled` y `.btn[aria-disabled="true"]` con 60 % y cursor de no permitido, y el
hover solo para los botones que no están bloqueados.
Descartada: volver a poner `button:disabled` en `base.css`.
Motivo: D-12 de `sistema-de-diseno` (`base.css` no estila elementos sueltos) y un test que lo vigila.

### D-10 La rama de integración sale de `feat/casilla-con-documento`
Elegida: `feat/presentacion-registro` parte de `feat/casilla-con-documento`.
Descartada: partir de `main`, como pide `AGENTS.md`.
Motivo: el registro usa la casilla con documento y las dos features no están en `main` (S-06). Su PR a `main`
espera a los de aquellas.

## Estrategia de tests
- **Unitario (Vitest + jsdom, P-04 y P-05):** `PublicPage` (`ready`, clase de fundido), `Fade` (monta de nuevo con
  otra `key`), `useDeadline` (temporizadores simulados), `VerifyPage` (orden y clases de los botones, hueco
  reservado con sus mensajes, plazo de 10 s, mensaje de error de conexión), `RegisterPage` (card oculta mientras
  carga y plazo), `DonePage`, `App` (una sola barra, que persiste entre pantallas) y el CSS del botón con una
  lectura de `Button.css` (como `field.css` y `DocumentModal.css`).
- **Navegador real (proyecto de pruebas visuales, Chromium, claro y oscuro):** una fila con el secundario a la
  izquierda y el principal a la derecha, dos filas a 420 px, botón desactivado (opacidad y cursor, sin hover), altura
  de la card idéntica con y sin mensaje de reenvío, ninguna card (ni su título) mientras la respuesta está
  retenida, fundido (la opacidad pasa de 0 a 1 en unos 0,2 s), barra superior que es el mismo nodo antes y
  después de navegar, y sin animación con movimiento reducido. Entra en el CI que ya ejecuta `test:visual`.
- **Accesibilidad:** `axe` en jsdom y, en Chromium, con contraste, las pantallas afectadas.
- **Mutantes:** al menos uno por tarea (por ejemplo, la card que se pinta con `ready` falso o el botón de
  reenviar fuera de la fila).
- **Sin cambios:** la comparación exacta con las referencias no cambia: las piezas afectadas no cambian de
  estilo en reposo.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-04, M-06, M-07 | unitario, navegador |
| RF-002 | M-01, M-06, M-07 | unitario (CSS), navegador |
| RF-003 | M-04, M-06, M-07 | unitario, navegador |
| RF-004 | M-02, M-04, M-05, M-06, M-07 | unitario, navegador |
| RF-005 | M-02, M-04, M-05, M-06, M-07 | unitario, navegador |
| RF-006 | M-02, M-06 | navegador |
| RF-007 | M-05 | unitario (los tests previos) |
| RF-008 | M-01 | unitario |
| RF-009 | M-03, M-06 | unitario, navegador |

## RF sin cobertura
Ninguno.
