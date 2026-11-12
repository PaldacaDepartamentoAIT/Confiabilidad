# Identidad visual

Estado: aprobado

Reglas de estilo de la interfaz de Confiabilidad (web y escritorio): colores, tipografía, formas,
interacción y movimiento. El código las recoge como variables CSS y componentes reutilizables en
`frontend/`, y `desktop/` las hereda al cargar el frontend. Toda pantalla nueva se construye con
esos componentes.

Versión 2. Sustituye a la versión 1 (paleta Niebla marina, bloques bento, botones en píldora).

## Principios

1. **Plano y cuadrado.** Sin sombras, sin degradados, sin transparencias. Las zonas se separan con
   líneas de 1 px y radios pequeños.
2. **El color informa, no decora.** Lo normal va en neutro. Solo los estados de alarma y lo
   interactivo tienen color propio.
3. **Lo que se pulsa se reconoce.** Todo elemento interactivo tiene hover, foco visible y un radio
   mayor que el de las zonas que solo informan.
4. **Un color por función.** Cada color tiene un único papel; si dos elementos comparten color,
   comparten significado. Única excepción: el error de formulario usa el rojo de P1, porque también
   bloquea.
5. **Nada depende solo del color.** Cada estado lleva también forma y texto.

## Estructura de la aplicación

Hay dos estructuras, según se haya iniciado sesión o no.

- **Pantallas públicas** (inicio de sesión, registro, recuperación de contraseña y cualquier otra a
  la que se accede sin sesión): sin menú lateral. Solo una barra superior de 64 px con el nombre
  del sistema a la izquierda (mismo estilo que en el menú lateral) y el botón de idioma y el de tema
  a la derecha; el contenido va debajo, en una columna centrada de 480 px como máximo (el ancho
  completo en pantallas más estrechas), con 22 px de relleno lateral y 32 px de margen superior. La
  columna contiene un único bloque cuya cabecera es el título de la pantalla (`h1`, 15 px, 600) y,
  debajo, el texto, los campos y las acciones. Los campos van apilados con 16 px de separación y las
  acciones alineadas a la derecha con 10 px entre ellas. Las pantallas de error o de confirmación
  llevan el mismo bloque, con su título y su texto, sin formulario.
- **Pantallas con sesión iniciada:** menú lateral y barra superior, descritos a continuación.

Elementos comunes y de las pantallas con sesión:

- **Fondo único.** Lienzo y bloques usan el mismo color; los bloques se separan con borde. Única
  excepción: un bloque destacado puede llevar el fondo secundario.
- **Menú lateral** (solo con sesión) a la izquierda, con la altura de la pantalla y fondo del color
  secundario, separado del contenido por un borde de 1 px:
  - abierto mide 232 px y contraído 60 px; pasa de uno a otro con animación;
  - cabecera de 64 px con el nombre del sistema a la izquierda y el botón de abrir y cerrar a la
    derecha; contraído, solo el botón, centrado;
  - navegación con icono y etiqueta; contraída, solo el icono, con la etiqueta como `title`;
  - pie con el botón de tema y, debajo, el de idioma, siempre uno encima del otro; debajo, el de
    usuario (avatar con iniciales, nombre y flechas), a todo el ancho.
- **Barra superior** de 64 px: secciones de la pantalla en pestañas a la izquierda y buscador a la
  derecha. Su línea inferior continúa por la cabecera del menú lateral, de modo que se ve como una
  sola línea.
- **Contenido** con margen de 22 px y separación de 18 px entre bloques; el título de la página va
  al principio del contenido.
- **Móvil** (menos de 768 px). El menú lateral se oculta y se abre como panel superpuesto desde un
  botón a la izquierda de la barra superior; se cierra con un clic fuera o con Escape, sin velo. En
  móvil no existe el estado contraído.

## Temas

Dos temas de igual rango, claro y oscuro. Al arrancar se usa el tema del sistema operativo; el
botón de tema lo cambia y la elección se recuerda, igual que el idioma. El botón muestra el tema
actual. Sustituye a la decisión D-13 de `registro-flujo`.

## Paleta: Pizarra

El contraste indicado es el del elemento sobre su fondo habitual (WCAG 2.2: mínimo 4,5:1 para texto
y 3:1 para iconos, formas y bordes de controles).

### Tema claro

| Rol | Color | Uso | Contraste |
|---|---|---|---|
| Fondo | `#f8f9f9` | Lienzo y bloques | — |
| Tinta | `#1b1e22` | Texto y relleno negro | 15,9:1 |
| Texto secundario | `#61656b` | Etiquetas, ayudas, ejes, placeholder, pestañas no activas | 5,6:1 |
| Gris | `#c3c5c7` | Líneas, bordes de zonas, rellenos neutros, contadores | 1,6:1 |
| Cuadrícula | `#d8dadb` | Cuadrícula de las gráficas | — |
| Borde de control | `#8d9094` | Borde de campos, casillas y menús desplegables | 3,0:1 |
| Principal | `#546c8c` | Acento de lo interactivo; texto blanco encima | 5,1:1 (5,4:1 con blanco) |
| Secundario | `#d8dbdf` | Menú lateral y bloque destacado; texto en tinta | 12,0:1 con tinta |

### Tema oscuro

| Rol | Color | Uso | Contraste |
|---|---|---|---|
| Fondo | `#111213` | Lienzo y bloques | — |
| Relleno negro | `#000000` | Bloque en alerta (el tema claro usa la tinta) | — |
| Tinta | `#eeeff1` | Texto | 16,3:1 |
| Texto secundario | `#aaadb0` | Etiquetas, ayudas, ejes, placeholder, pestañas no activas | 8,3:1 |
| Gris | `#47484a` | Líneas, bordes de zonas, rellenos neutros, contadores | 2,0:1 |
| Cuadrícula | `#313234` | Cuadrícula de las gráficas | — |
| Borde de control | `#5f6163` | Borde de campos, casillas y menús desplegables | 3,0:1 |
| Principal | `#9fafc6` | Acento de lo interactivo; texto en color de fondo encima | 8,4:1 |
| Secundario | `#535a65` | Menú lateral y bloque destacado; texto en tinta | 6,0:1 con tinta |
| Botón de menú | `#ffffff` | Fondo del botón de abrir y cerrar; icono en secundario | 7,0:1 |

- En el tema claro, el botón de abrir y cerrar usa la tinta como fondo y el secundario en el icono.
- Sobre el color secundario solo se escribe en tinta: el texto secundario no llega a 4,5:1 encima.
- «Principal» es el acento de lo interactivo (botón principal, botón secundario, casilla marcada,
  hover y foco de campos, línea del elemento activo, contorno de foco). Lo demás que se pulsa
  (pestañas, navegación, botones del menú lateral) va en tinta o en texto secundario.

### Estados de alarma

Un solo color por prioridad en toda la aplicación.

| Prioridad | Forma | Claro | Oscuro | Contraste sobre el fondo |
|---|---|---|---|---|
| P1 | Cuadrado | `#a47070` | `#a47070` | 3,9:1 · 4,6:1 |
| P2 | Triángulo | `#915535` | `#d9977a` | 5,6:1 · 7,7:1 |
| Advertencia | Rombo | `#7a7020` | `#c9bd8c` | 4,8:1 · 9,9:1 |
| Neutro (por ejemplo, mantenimiento) | Cuadrado vacío | Texto secundario | Texto secundario | — |

- **Color solo en la forma.** El texto del estado va en tinta y el color queda en el icono, porque
  el rojo de P1 no llega a 4,5:1 en el tema claro.
- **Aviso.** Bloque con borde de 1 px y borde izquierdo de 4 px en el color de la prioridad.
- **Bloque en alerta.** Fondo en relleno negro; la cifra principal en el color de la prioridad y
  el texto pequeño en blanco.
- **Error de formulario.** Borde del campo e icono `circle-alert` en el rojo de P1; el texto del
  mensaje, en tinta.
- **Información y confirmación.** No tienen color propio: aviso con borde izquierdo de 4 px en texto
  secundario e icono `info`.

## Forma

| Elemento | Radio |
|---|---|
| Zonas: bloques, avisos, menús desplegables | 4 px |
| Interactivos: botones, campos, buscador, pestañas, opciones de menú, elementos del menú lateral | 6 px |
| Casillas, contadores, etiquetas (chips), avatar | 4 px |
| Línea del elemento activo | 0 (línea recta) |

| Elemento | Tamaño |
|---|---|
| Botones, campos y pestañas | 36 px de alto |
| Opciones de menú desplegable | 34 px de alto |
| Elementos del menú lateral (navegación, tema, idioma, usuario) | 36 px de alto, abierto o contraído |
| Botón de abrir y cerrar | 40 × 37 px |
| Casilla | 18 × 18 px |
| Avatar | 24 × 24 px |

- Bordes de 1 px en todas las zonas.
- Los iconos del menú lateral no se desplazan al abrir o cerrar; solo aparecen o desaparecen las
  etiquetas.

## Interacción

- **Hover.** Elementos sin relleno: fondo opaco que mezcla un 9 % de la tinta con el fondo de su
  contenedor. Elementos rellenos con el principal (botón principal, casilla marcada): el principal
  oscurecido (78 % principal, 22 % `#000`), en ambos temas.
- **Transición del hover.** Entra en 0,08 s y sale en 0,35 s.
- **Botón principal:** relleno en el principal, texto en peso 600. **Botón secundario:** sin
  relleno, borde y texto en el principal.
- **Campos de texto** (incluido el buscador): sin cambio de fondo; hover con borde de 1 px y foco
  con borde de 2 px, ambos en el principal (en el rojo de P1 si el campo tiene error). El foco
  siempre es más grueso que el hover; el relleno interior compensa el grosor para que el texto no se
  mueva. Los obligatorios llevan «*» y una leyenda «* Campo obligatorio».
- **Botón de icono dentro de un campo.** Va a la derecha, dentro del borde del campo, con un icono
  de 16 px en texto secundario (tinta al pasar el cursor), sin borde ni relleno, de 32 × 32 px como
  mínimo y con el nombre accesible del campo. Si alterna un estado, como mostrar u ocultar la
  contraseña, lleva `aria-pressed`.
- **Foco de teclado** del resto de elementos: contorno de 2 px en el principal, separado 2 px.
- **Elemento activo** (pestaña, elemento de la navegación lateral, día de un calendario): sin
  relleno, en tinta, con una línea recta de 2 px en el principal por debajo. En la barra superior,
  la línea se desplaza de la pestaña anterior a la nueva al cambiar de sección.
- **Pestañas que no caben.** Se desvanecen todas y aparece un selector pegado a la izquierda del
  buscador: el texto de la pestaña activa con un chevron hacia abajo, sin borde ni subrayado. Se
  recalcula al cambiar de pestaña, al abrir o cerrar el menú y al redimensionar la ventana.
- **Menús de selección.** Mismo fondo, borde de control y tipografía que los campos; la opción
  seleccionada en negrita con un chevron «>» a la izquierda; la resaltada con el teclado usa el fondo
  del hover. Siguen el patrón de combobox con `listbox`: flechas, Inicio, Fin, RePág, AvPág, Enter,
  Espacio, Tab, Escape y búsqueda por letra (sin distinguir tildes).
- **Botón de abrir y cerrar el menú:** chevron «<» con el menú abierto y «>» con el menú contraído.
- **Buscador.** Ancho fijo de 220 px. Por debajo de 560 px se convierte en un botón con lupa. Al
  pulsarlo, el campo se despliega desde el botón hasta ocupar todo el ancho de la barra superior a la
  derecha del botón del menú lateral (que sigue visible), mientras las pestañas (o el selector) se
  desvanecen. Al perder el foco, aunque haya texto escrito, o con Escape, el campo se pliega y vuelve
  a verse el botón.
- **Estado del menú lateral.** No se recuerda: cada sesión empieza con el menú abierto.

## Movimiento

| Animación | Duración |
|---|---|
| Abrir y cerrar el menú lateral (sin rebote) | 0,25 s, salida suave |
| Etiquetas del menú lateral al abrir o cerrar | 0,15–0,2 s de fundido |
| Desplazamiento de la línea de la pestaña activa | 0,25 s, salida suave |
| Cambio del contenido al cambiar de sección | 0,2 s de fundido |
| Pestañas a selector y al revés | 0,15 s de salida y, a continuación, 0,2 s de entrada |
| Buscador reducido: abrir y cerrar | 0,25 s, salida suave; 0,2 s de fundido de las pestañas y del botón |
| Aparición de un menú desplegable | 0,18 s (fundido y 6 px de desplazamiento hacia abajo); se cierra sin animación |
| Panel lateral en móvil | 0,25 s de deslizamiento |
| Cambio de tema | 0,4 s en todos los colores, solo durante el cambio |

Si el sistema pide reducir el movimiento, no se anima nada, incluidos el hover y el cambio de tema.

## Datos

- **Gráficas de barras.** Primera serie en el principal y segunda en gris, sólidas y sin borde; cuadrícula de fondo
  de 16 px en color de cuadrícula.
- **Rejillas de estado.** Cuadros separados 4 px; los normales en gris y los que tienen un estado de
  alarma en su color; el estado neutro, como cuadrado vacío.
- **Tablas.** Cabecera en texto secundario, filas separadas por línea de 1 px, códigos y fechas en
  monoespaciada.
- **Contadores.** Relleno gris, texto en tinta, monoespaciada de 12 px.

## Tipografía

| Uso | Fuente | Tamaño y peso |
|---|---|---|
| Nombre del sistema | Manrope | 18 px, 700, subrayado en tinta de 2,5 px de grosor y 6 px de separación |
| Título de página | Manrope | 24 px, 600 |
| Título de bloque | Manrope | 15 px, 600 |
| Cifra destacada | Manrope | 28 px, 600 |
| Texto y pestañas | Manrope | 14 px, 400–500 (las pestañas en 500, activas o no) |
| Etiquetas de campo | Manrope | 12,5 px, 500, en texto secundario |
| Ayudas | Manrope | 12 px |
| Códigos, fechas, contadores, avatar | JetBrains Mono | 12–13 px, 400–500 (13 px dentro de los campos) |

Paquetes npm `@fontsource-variable/manrope` y `@fontsource-variable/jetbrains-mono` (licencia OFL).
Las cifras en columna usan `font-variant-numeric: tabular-nums`.

## Especificación de componentes

Valores exactos tomados de la pantalla de referencia «Crear empresa»
(`docs/referencia/crear-empresa.html`). Todas las pantallas deben reproducirlos tal cual; esta
sección manda sobre las descripciones generales de arriba.

### Menú lateral

| Parte | Valor |
|---|---|
| Contenedor | `position: sticky; top: 0; height: 100vh`; ancho 232 px (60 px contraído); borde derecho de 1 px en gris; transición de ancho 0,25 s `ease-out` |
| Cabecera | 64 px de alto, relleno horizontal de 10 px, borde inferior de 1 px en gris |
| Nombre del sistema | posicionado a 22 px del borde izquierdo y centrado en vertical; 18 px, 700, `line-height: 1,25`, `letter-spacing: -0,01em`; subrayado en tinta de 2,5 px con 6 px de separación |
| Botón de abrir y cerrar | 40 × 37 px, radio 6 px, a la derecha de la cabecera; icono de chevron de 22 px (la excepción al icono de 16 px); al pasar el cursor, fondo en 80 % del fondo del botón y 20 % del texto secundario |
| Navegación | relleno de 10 px, separación de 2 px entre elementos |
| Elemento de navegación | 36 px de alto, relleno horizontal de 12 px, separación de 10 px entre icono y etiqueta, radio 6 px, peso 500, icono de 16 px |
| Elemento activo | línea de 2 px en el principal, a 3 px del borde inferior del elemento y con 12 px de margen a cada lado |
| Contador | 20 px de alto, ancho mínimo de 20 px, relleno horizontal de 5 px, fondo gris, texto en tinta, JetBrains Mono 12 px, 500, radio 4 px |
| Pie | borde superior de 1 px en gris, relleno de 10 px, separación de 8 px entre botones |
| Botones del pie | 36 px de alto, relleno horizontal de 12 px, separación de 10 px, peso 500 |
| Botón de usuario | relleno horizontal de 8 px; avatar de 24 × 24 px (radio 4 px, fondo gris, JetBrains Mono 12 px 500), nombre y chevrons arriba y abajo |

### Barra superior

| Parte | Valor |
|---|---|
| Contenedor | `position: sticky; top: 0`, 64 px de alto, relleno horizontal de 22 px, separación de 12 px, borde inferior de 1 px en gris, fondo del lienzo |
| Pestaña | 36 px de alto, relleno horizontal de 12 px, radio 6 px, 14 px, peso 500; inactiva en texto secundario, activa en tinta |
| Separación entre pestañas | 4 px |
| Línea de la pestaña activa | 2 px en el principal, pegada al borde inferior de la pestaña con 12 px de margen a cada lado; se desplaza entre pestañas |
| Buscador | 220 × 36 px, icono de lupa a 11 px del borde izquierdo en texto secundario, relleno izquierdo de 34 px; placeholder «Buscar…» |
| Selector de pestañas | alto de 36 px, relleno de 0 10 px 0 12 px, radio 6 px, separación de 6 px entre texto y chevron, peso 500, menú alineado a la derecha con ancho mínimo de 200 px |

### Contenido

| Parte | Valor |
|---|---|
| Contenedor | relleno de 22 px, separación de 18 px entre bloques |
| Título de página | 24 px, 600, `letter-spacing: -0,01em`, interlineado 1,25 |
| Descripción de página | texto secundario, 14 px, a 4 px del título |
| Formulario | dos columnas: contenido flexible y un bloque lateral de 280 px, con 18 px entre ellas; a menos de 1100 px, una sola columna |
| Rejilla de campos | columnas automáticas de 240 px como mínimo, separación de 16 px en vertical y 18 px en horizontal; un campo puede ocupar toda la fila |
| Acciones del formulario | alineadas a la derecha, separación de 10 px; el secundario («Cancelar») antes que el principal |
| Leyenda de obligatorios | «* Campo obligatorio», 12 px, texto secundario, debajo de las acciones y alineada a la derecha, igual que ellas |

### Bloque

| Parte | Valor |
|---|---|
| Contenedor | borde de 1 px en gris, radio 4 px, relleno de 18 px arriba, 20 px a los lados y 20 px abajo, fondo del lienzo |
| Título | 15 px, 600, margen inferior de 14 px |
| Bloque destacado | fondo secundario; todo el texto en tinta, incluidas las ayudas |

### Campos

| Parte | Valor |
|---|---|
| Etiqueta | 12,5 px, 500, texto secundario, a 6 px del campo; el «*» en texto secundario |
| Campo | 36 px de alto, relleno horizontal de 11 px, borde de 1 px en borde de control, radio 6 px, 14 px, fondo del lienzo |
| Campo de códigos | JetBrains Mono 13 px |
| Hover | borde de 1 px en el principal |
| Foco o menú abierto | borde de 2 px en el principal; el relleno horizontal baja a 10 px para que el texto no se mueva |
| Área de texto | 92 px de alto mínimo, relleno de 8 px arriba y 11 px a los lados (7 px y 10 px con foco), redimensionable en vertical |
| Ayuda | 12 px, texto secundario |
| Contador de caracteres | JetBrains Mono 12 px, texto secundario, a la derecha de la ayuda |
| Error | borde en P1; debajo, el icono `circle-alert` en P1 y el mensaje en tinta, 12,5 px, con 6 px de separación; `aria-invalid` activo |

### Menú de selección

| Parte | Valor |
|---|---|
| Disparador | igual que un campo; texto a la izquierda y chevron hacia abajo a la derecha; sin valor, «Selecciona una opción» en texto secundario |
| Ancho del disparador | todo el ancho disponible de su contenedor (100 %), sea un campo de formulario, un botón del menú lateral o un selector de la barra; el menú desplegado nunca es más estrecho que él |
| Menú | aparece a 4 px bajo el disparador, ancho mínimo igual al del disparador, alto máximo de 260 px con desplazamiento, relleno de 4 px, fondo del lienzo, borde de 1 px en borde de control, radio 4 px |
| Opción | 34 px de alto, relleno de 0 10 px 0 6 px, separación de 6 px, radio 6 px; la seleccionada en peso 700 y con un chevron «>» a la izquierda; el resto reserva el mismo hueco |
| Opción resaltada u opción bajo el cursor | fondo con el 9 % de la tinta mezclado con el lienzo |

### Casilla

| Parte | Valor |
|---|---|
| Caja | 18 × 18 px, borde de 1 px en borde de control, radio 4 px |
| Marcada | fondo y borde en el principal, check de 14 px de trazo 3 en el color de texto sobre el principal |
| Hover | sin marcar: fondo con el 9 % de la tinta; marcada: el principal oscurecido |
| Fila | caja y texto separados 10 px; texto de 14 px |
| Ayuda y error | debajo de la fila, a 2 px, alineados con el borde izquierdo de la caja (sin sangría); la ayuda de 12 px en texto secundario; el error con el icono `circle-alert` en P1 y el mensaje en tinta, como en un campo de texto |

### Botones

| Parte | Valor |
|---|---|
| Medidas | 36 px de alto, relleno horizontal de 16 px, radio 6 px, 14 px, peso 600, separación de 8 px entre icono y texto |
| Principal | fondo y borde en el principal, texto en el color de texto sobre el principal; hover con el principal oscurecido |
| Secundario | sin relleno, borde de 1 px y texto en el principal; hover con el 9 % de la tinta |

### Aviso

Borde de 1 px en gris y de 4 px a la izquierda, radio 4 px, relleno de 12 px arriba y abajo y 14 px a
los lados, separación de 10 px entre icono y texto, texto en tinta. El borde izquierdo y el icono
usan el color de la prioridad; en un aviso informativo, el texto secundario.

### Datos

Valores exactos tomados de la pantalla «Activos», aprobada como referencia
(`docs/referencia/activos.html`). Los componentes de las páginas de referencia llevan `data-ui`, y
`docs/referencia/comparar.cjs` comprueba que una página candidata coincida con ellas (ver
`docs/referencia/README.md`).

| Parte | Valor |
|---|---|
| Rejilla de indicadores | columnas automáticas de 190 px como mínimo, separación de 18 px |
| Indicador | bloque de 16 px de relleno; etiqueta de 12,5 px, 500, texto secundario; cifra de 28 px, 600, interlineado 1,2, `tabular-nums`, con 2 px de margen arriba y abajo; ayuda de 12 px |
| Indicador destacado | fondo secundario; etiqueta y ayuda en tinta |
| Indicador en alerta | fondo en relleno negro; etiqueta y ayuda en blanco `#ffffff`; cifra en el color de la prioridad (28 px) |
| Cabecera de bloque | elementos en fila con 10 px de separación, 14 px de margen inferior; título de 15 px, 600; contador a continuación; acciones alineadas a la derecha |
| Aviso de alarma | relleno de 12 px arriba y abajo y 16 px a los lados, separación de 12 px entre icono, texto y acción; el título en peso 600; puede llevar un botón secundario a la derecha |
| Estado | icono de forma de 16 px y texto en tinta, a 8 px; el estado normal no lleva icono pero reserva el mismo hueco de 16 px |
| Chip (criticidad y similares) | fondo gris, texto en tinta, 12 px, 500, relleno horizontal de 8 px, interlineado de 22 px, radio 4 px |
| Gráfica de barras | lienzo SVG de 640 × 240 que se escala al ancho del bloque; área de trazado de 576 × 192 situada en x = 40, y = 8, con la cuadrícula de 16 px detrás de las barras; eje vertical con marcas cada 30 y números de 12 px en JetBrains Mono, texto secundario, a 8 px del área; meses debajo, centrados y a 20 px, en Manrope 12 px, texto secundario |
| Barras | 30 px de ancho, 4 px de separación entre las dos series, 96 px por grupo; primera serie en el principal y segunda en gris, sólidas y sin borde |
| Leyenda de gráfica | separación de 16 px entre elementos; muestras de 12 × 12 px sin borde; 12 px, texto secundario |
| Rejilla de estado | cuadros de 24 × 24 px con radio 0 y separación de 4 px, que continúan en la fila siguiente; los normales en gris; los de P1, P2 y advertencia en su color con el glifo de su forma (12 px, en color del lienzo) dentro, para no depender solo del color; el neutro, con borde de 2 px en texto secundario; cada cuadro con `title` y `aria-label` |
| Leyenda de la rejilla | iconos de forma de 16 px y etiquetas de 12 px en tinta, 14 px por debajo de la rejilla |
| Tabla | ancho completo con desplazamiento horizontal desde 640 px; cabecera de 12,5 px, 500, texto secundario, relleno de 8 px arriba y abajo y 12 px a los lados, borde inferior de 1 px en gris; filas de 44 px de alto con relleno horizontal de 12 px y borde inferior de 1 px en gris; códigos y fechas en JetBrains Mono 13 px |
| Fila bajo el cursor o seleccionada | fondo con el 9 % de la tinta; la seleccionada lleva además una línea de 2 px en el principal a su izquierda, para distinguirla del hover |
| Pie de tabla | 12 px, texto secundario, a 12 px por debajo; muestra el número de filas seleccionadas |

Regla de estado: **el texto del estado va siempre en tinta**; solo el icono de forma lleva el color de
la prioridad.

## Iconos y gráficos

- Iconos de la librería `lucide-react`, de trazo 2, a 16 px (14 px dentro de las casillas).
- Gráficas en SVG propio, sin librería.

## Accesibilidad

- Todo texto supera 4,5:1; formas de estado, iconos y bordes de controles, 3:1.
- Ningún estado se comunica solo con color.
- Los selectores propios se comportan como un combobox con `listbox` accesible.
