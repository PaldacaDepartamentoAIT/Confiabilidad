# Identidad visual

Estado: aprobado

Referencia visual de la interfaz de Confiabilidad (web y escritorio). Define colores, tipografía,
formas y reglas de uso. Los valores salen de la maqueta revisada con el usuario; el código los
recogerá como variables CSS en `frontend/`, y `desktop/` los hereda al cargar el frontend.

## Principios

1. **El color informa, no decora.** Lo normal va en neutro. Solo las alarmas y las acciones
   tienen color propio.
2. **Lo que se pulsa se distingue por forma y por color.** Todo elemento interactivo es redondo
   (píldora o círculo) y usa el color de acción. Lo que solo informa es rectangular y nunca usa el
   color de acción.
3. **Un color por función.** Cada color tiene un único papel; si dos elementos comparten color,
   comparten significado.
4. **Nada depende solo del color.** Cada estado lleva también forma y texto.

## Estructura

- **Lienzo plano** y **bloques opacos** sin sombra, separados por el lienzo (composición en
  bloques o *bento*).
- **Barra lateral flotante** con iconos; el elemento activo usa el color de acción.
- **Barra superior** en todas las pantallas, sobre el lienzo y sin fondo propio, con los botones
  de icono de idioma y de tema alineados a la derecha.
- Sin degradado de fondo, sin transparencias y sin animación de fondo.

## Temas

Dos temas de igual rango, claro y oscuro: la aplicación la usan tanto ingenieros en oficina como
operadores en sala de control. Al arrancar se usa el tema del sistema operativo; si el usuario
elige uno, se recuerda, igual que el idioma.

- Se elige desde el botón de tema de la barra superior (sol con el tema claro en uso, luna con el
  oscuro), con dos opciones: claro y oscuro.
- El tema elegido se aplica antes de pintar la primera pantalla: nunca se ve el otro ni un
  instante.

## Paleta: Niebla marina

13 colores por tema: 7 neutros, 1 de acción con 2 tonos derivados y 3 de alarma. El contraste
indicado es el del texto sobre su fondo habitual (WCAG 2.2; mínimo 4,5:1 para texto y 3:1 para
iconos y formas).

### Tema claro

| Rol | Color | Uso | Contraste |
|---|---|---|---|
| Lienzo | `#dbe5eb` | Fondo de la aplicación | — |
| Bloque | `#ffffff` | Fondo de tarjetas y paneles | — |
| Apoyo | `#edf3f7` | Cabecera de tablas, fila seleccionada, etiquetas | — |
| Línea | `#d1dde5` | Separadores | — |
| Línea fuerte | `#768c9b` | Bordes de campos y casillas, rayado | 3,5:1 sobre bloque |
| Texto secundario | `#384d5c` | Etiquetas, ayudas, ejes | 8,8:1 sobre bloque |
| Tinta | `#0f222e` | Texto y relleno fuerte | 16,3:1 sobre bloque |
| Acción | `#1b5983` | Todo lo interactivo; texto blanco encima | 7,5:1 con blanco |
| Acento, tono 1 | `#6aafdc` | Inicio del degradado de acento; texto en tinta | 6,8:1 con tinta |
| Acento, tono 2 | `#c9e2f2` | Final del degradado de acento | 12,1:1 con tinta |
| Alarma P1 | `#8a2f3a` | Prioridad 1 | 8,2:1 sobre bloque |
| Alarma P2 | `#80442b` | Prioridad 2 | 7,6:1 sobre bloque |
| Advertencia | `#655423` | Prioridad 3 | 7,4:1 sobre bloque |

### Tema oscuro

| Rol | Color | Uso | Contraste |
|---|---|---|---|
| Lienzo | `#0c161d` | Fondo de la aplicación | — |
| Bloque | `#162631` | Fondo de tarjetas y paneles | — |
| Apoyo | `#1f313d` | Cabecera de tablas, fila seleccionada, etiquetas | — |
| Línea | `#293e4c` | Separadores | — |
| Línea fuerte | `#627d90` | Bordes de campos y casillas, rayado | 3,6:1 sobre bloque |
| Texto secundario | `#b3c5d0` | Etiquetas, ayudas, ejes | 8,7:1 sobre bloque |
| Tinta | `#eaf1f6` | Texto | 13,6:1 sobre bloque |
| Relleno fuerte | `#344855` | Relleno fuerte (ver reglas); texto en tinta | 8,4:1 con tinta |
| Acción | `#9cc9e8` | Todo lo interactivo; texto en color de lienzo | 10,4:1 con lienzo |
| Acento, tono 1 | `#4f95c4` | Inicio del degradado de acento; texto en color de lienzo | 5,6:1 con lienzo |
| Acento, tono 2 | `#9cc9e8` | Final del degradado de acento | 10,4:1 con lienzo |
| Alarma P1 | `#d97f87` | Prioridad 1 | 5,4:1 sobre bloque |
| Alarma P2 | `#d29a76` | Prioridad 2 | 6,4:1 sobre bloque |
| Advertencia | `#c4b07a` | Prioridad 3 | 7,3:1 sobre bloque |

## Reglas de color

- **Relleno fuerte.** Un único color para lo que informa con fuerza: criticidad A, tarjeta
  destacada (mapa de activos), barra de operación y mantenimiento en curso. En claro es la tinta;
  en oscuro, el relleno fuerte `#344855`.
- **Acción.** Solo para elementos interactivos: botón principal, pestaña y día activos, icono
  activo de la barra lateral, casillas marcadas, texto y borde de botones secundarios. Ningún dato
  usa este color.
- **Acento.** Siempre como degradado del tono 1 al tono 2 (160°), nunca como color liso. Se usa en
  la tarjeta de disponibilidad y en el mantenimiento planificado (barras, leyenda y calendario). El
  degradado es lo que lo distingue de un botón.
- **Parada no planificada.** Rayado diagonal de líneas de 1 px cada 4 px, en línea fuerte sobre
  apoyo, sin borde.
- **Tarjeta destacada.** Fondo de relleno fuerte. Sobre ella se usan, en claro, el texto
  `#eaf1f6`, el secundario `#b3c5d0`, los puntos normales `#506a7c` y las alarmas del tema oscuro;
  en oscuro, la tinta, el texto secundario, los puntos `#5c6d78` y las alarmas del propio tema.
  Las formas de alarma sobre ella superan 3:1 en ambos temas.

## Alarmas

- Tres prioridades, cada una con color **y** forma: P1 cuadrado, P2 triángulo, advertencia rombo.
- **Color solo en la forma.** El texto del estado va en tinta; el color queda en el icono. Así las
  alarmas no dominan la pantalla y el texto mantiene su contraste.
- Los colores son atenuados (carmín, terracota y ocre oscuros) y no se usan para nada más.
- Normal y mantenimiento van en texto secundario con icono (círculo y llave), sin color propio.
- El color de marca nunca es rojo, naranja ni amarillo.
- **Excepción en formularios:** el asterisco de los campos obligatorios y los errores de campo (su
  texto y el borde del campo con error) usan el color de alarma P1. Es el único uso de P1 fuera de
  las alarmas, y nunca va solo: el asterisco se acompaña de la leyenda de obligatorios y el error,
  de su texto.

## Interacción y forma

| Elemento | Forma |
|---|---|
| Botones, pestañas, buscador, menú de usuario, días del calendario | Píldora (radio 999 px) |
| Botones de icono, iconos de la barra lateral, avatar | Círculo |
| Casillas de verificación | Cuadradas, radio 4 px (convención reconocible) |
| Tarjetas y paneles | Radio 12 px |
| Etiquetas, criticidad, franjas del calendario, barra de tiempo | Radio 4 px |
| Campos de texto, selector y su lista de opciones, globo de ayuda | Radio 4 px |
| Ventana de documento | Radio 12 px, como las tarjetas |
| Pasos del indicador de pasos | Círculo (convención reconocible; ver «Componentes») |

- **Foco visible:** contorno de 3 px en color de acción, separado 2 px del elemento.
- La criticidad A va rellena en relleno fuerte; B con borde de tinta; C con borde de texto
  secundario.

## Componentes

### Botón con menú (idioma y tema)
- Botón de icono circular, con borde y contenido en color de acción. El de idioma muestra la
  abreviatura del idioma activo («ES», «EN», «PT»); el de tema, el sol o la luna.
- El menú es un bloque con radio 12 px y borde de línea, sin sombra, bajo su botón. Cada opción es
  una fila con el texto en tinta; la activa lleva un check en color de acción delante y peso 600.
  La opción resaltada con el teclado o el puntero tiene fondo de apoyo.
- Bajo las opciones, separada por una línea, una pista de teclado en texto secundario de 11,5 px con
  las teclas en JetBrains Mono: «↑ ↓ moverte · Intro elegir · Esc cerrar».

### Indicador de pasos
- Tres círculos numerados unidos por una línea de 2 px, con el nombre de cada paso debajo.
- Los pasos solo informan, así que **no usan el color de acción**: el actual y los completados van
  en relleno fuerte (en claro, tinta con el número en blanco; en oscuro, `#344855` con el número en
  tinta), los completados con un check en lugar del número; el actual y los completados llevan
  además un borde de 2 px en tinta. Los pendientes tienen borde punteado de línea fuerte, sin
  relleno y con el número en texto secundario. El nombre del paso actual va en peso 600.
- La línea entre dos pasos completados va en relleno fuerte; el resto, en línea.
- **Excepción de forma:** son círculos aunque informen, por ser la convención reconocible de un
  indicador de pasos, igual que las casillas son cuadradas. No se confunden con botones porque no
  usan el color de acción.

### Campos
- El nombre va encima del campo, en texto secundario; los obligatorios llevan detrás un asterisco
  en alarma P1 (ver «Alarmas»).
- Campo de 40 px de alto, fondo de bloque, borde de 1 px en línea fuerte y radio 4 px. Con error,
  el borde pasa a 2 px en alarma P1.
- Entre un campo y el siguiente hay 12 px, además del hueco del error.
- Bajo cada campo hay siempre un hueco de una línea para el error, aunque no haya error, para que
  el formulario no cambie de alto. El error va en alarma P1, en 12 px. Si no cabe en una línea, se
  muestra completo y el hueco crece mientras esté visible.
- Un control dentro del campo (el ojo de la contraseña) es un botón de icono circular en color de
  acción, en el extremo derecho, y el texto del campo nunca queda debajo de él.

### Botón de ayuda «?» y su globo
- Botón de icono circular de 18 px junto al nombre del campo, con el «?» y el borde en color de
  acción.
- El globo es un bloque de relleno fuerte con el texto en `#eaf1f6` (en claro) o en tinta (en
  oscuro), radio 4 px, ancho máximo 280 px, sin sombra, sobre el botón.

### Selector
- Mismo aspecto que un campo de texto, con una flecha hacia abajo en texto secundario a la derecha,
  la misma con o sin el puntero encima.
- Al desplegarse, la flecha gira 180° y debajo aparece la lista: un bloque con radio 4 px, borde de
  línea fuerte y altura máxima de 8 opciones, con desplazamiento. La opción resaltada tiene fondo
  de apoyo; la elegida, un check en color de acción.

### Ventana de documento
- Tarjeta centrada (radio 12 px, fondo de bloque, ancho máximo 720 px), con el título arriba, el
  texto con desplazamiento propio y un botón de icono circular para cerrar.
- Detrás, el lienzo opaco: el formulario no se ve mientras la ventana está abierta (sin
  transparencias).
- El enlace que la abre va en el texto de la casilla, subrayado y en color de acción.

### Zona de mensajes
- Cada paso de un formulario reserva encima de su botón principal un hueco de una línea para los
  mensajes generales y los avisos (espera, bloqueo, caducidad), haya o no mensaje, que crece si el
  mensaje no cabe.

### Asistente por pasos
- Indicador fijo arriba; debajo, el título del paso y su tarjeta.
- Un solo botón principal por paso, abajo a la derecha, con una flecha hacia la derecha tras el
  texto. Los botones secundarios (por ejemplo, reenviar el código) llevan borde y texto en color de
  acción y sin relleno.
- Al cambiar de paso, el título y la tarjeta se desplazan en horizontal (280 ms, `ease-out`): al
  avanzar, el paso nuevo entra por la derecha y el anterior sale por la izquierda; al retroceder,
  al revés. La barra superior y el indicador no se mueven; el indicador solo anima el cambio de
  color.

## Tipografía

| Uso | Fuente | Peso |
|---|---|---|
| Texto, títulos y cifras grandes | Manrope | 400 (texto y cifras), 500–600 (títulos de bloque, botones) |
| TAG, códigos de OT, fechas, valores en tablas | JetBrains Mono | 400–500 |

- Se incluyen en el proyecto como paquetes npm: `@fontsource-variable/manrope` y
  `@fontsource-variable/jetbrains-mono` (licencia OFL). Funcionan sin conexión en la app de
  escritorio.
- Las cifras que se alinean en columna usan `font-variant-numeric: tabular-nums`.
- JetBrains Mono distingue `0`/`O` y `1`/`l`, necesario en códigos como `210-BB-003`.
- Escala de la maqueta (se ajustará al implementar): título de área 28–40 px; cifra grande
  30–46 px; título de bloque 14,5 px; texto 13,5 px; secundario 12 px.

## Espaciado

- Separación entre bloques: 10 px.
- Relleno interior de tarjetas: 14 px vertical, 16 px horizontal.
- Relleno lateral de la página: 22 px.

## Accesibilidad

- Contrastes de esta paleta: ver tablas; todo texto supera 4,5:1, y toda forma de estado y todo borde de control, 3:1.
- Ningún estado se comunica solo con color (forma + texto).
- Si el sistema pide reducir el movimiento, no se anima nada que no sea imprescindible: los pasos
  cambian sin desplazarse y la flecha del selector y el indicador cambian sin transición.
