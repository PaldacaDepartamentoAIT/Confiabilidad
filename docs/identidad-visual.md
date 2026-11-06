# Identidad visual

Estado: borrador

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
   comparten significado.
5. **Nada depende solo del color.** Cada estado lleva también forma y texto.

## Estructura de la aplicación

- **Fondo único.** Lienzo y bloques usan el mismo color; los bloques se separan con borde.
- **Menú lateral** a la izquierda, con fondo del color secundario:
  - abierto mide 232 px y contraído 60 px; pasa de uno a otro con animación;
  - cabecera de 64 px con el nombre del sistema a la izquierda y el botón de abrir y cerrar a la
    derecha; contraído, solo el botón, centrado;
  - navegación con icono y etiqueta;
  - pie con los botones de tema e idioma en una fila (apilados al contraer) y el de usuario debajo,
    a todo el ancho.
- **Barra superior** de 64 px, alineada con la cabecera del menú: secciones de la pantalla en
  pestañas a la izquierda y buscador a la derecha.
- **Contenido** con margen de 22 px y separación de 18 px entre bloques.
- **Móvil.** El menú lateral se oculta y se abre como panel superpuesto.

## Temas

Dos temas de igual rango, claro y oscuro. Al arrancar se usa el tema del sistema operativo; el
botón de tema lo cambia y la elección se recuerda, igual que el idioma. Sustituye a la decisión
D-13 de `registro-flujo`.

## Paleta: Pizarra

El contraste indicado es el del elemento sobre su fondo habitual (WCAG 2.2: mínimo 4,5:1 para texto
y 3:1 para iconos, formas y bordes de controles).

### Tema claro

| Rol | Color | Uso | Contraste |
|---|---|---|---|
| Fondo | `#f8f9f9` | Lienzo y bloques | — |
| Tinta | `#1b1e22` | Texto y relleno negro | 15,9:1 |
| Texto secundario | `#61656b` | Etiquetas, ayudas, ejes, pestañas no activas | 5,6:1 |
| Gris | `#c3c5c7` | Líneas, bordes de zonas, rellenos neutros | 1,6:1 |
| Cuadrícula | `#d8dadb` | Cuadrícula de las gráficas | — |
| Borde de control | `#8d9094` | Borde de campos y casillas | 3,0:1 |
| Principal | `#546c8c` | Todo lo interactivo; texto blanco encima | 5,1:1 (5,4:1 con blanco) |
| Secundario | `#d8dbdf` | Menú lateral y bloques destacados; texto en tinta | 12,0:1 con tinta |

### Tema oscuro

| Rol | Color | Uso | Contraste |
|---|---|---|---|
| Fondo | `#111213` | Lienzo, bloques y relleno negro | — |
| Tinta | `#eeeff1` | Texto | 16,3:1 |
| Texto secundario | `#aaadb0` | Etiquetas, ayudas, ejes, pestañas no activas | 8,3:1 |
| Gris | `#47484a` | Líneas, bordes de zonas, rellenos neutros | 2,0:1 |
| Cuadrícula | `#313234` | Cuadrícula de las gráficas | — |
| Borde de control | `#5f6163` | Borde de campos y casillas | 3,0:1 |
| Principal | `#9fafc6` | Todo lo interactivo; texto en color de fondo encima | 8,4:1 |
| Secundario | `#535a65` | Menú lateral y bloques destacados; texto en tinta | 6,0:1 con tinta |
| Botón de menú | `#ffffff` | Fondo del botón de abrir y cerrar; icono en secundario | 7,0:1 |

En el tema claro, el botón de abrir y cerrar usa la tinta de fondo y el secundario en el icono.

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
- **Aviso.** Bloque con borde izquierdo de 4 px en el color de la prioridad.
- **Bloque en alerta.** Fondo en relleno negro; la cifra principal en el color de la prioridad y
  el texto pequeño en blanco.
- **Error de formulario.** Borde del campo y mensaje en el rojo de P1; el mensaje lleva además un
  icono.

## Forma

| Elemento | Radio |
|---|---|
| Zonas: bloques, avisos, menús desplegables | 4 px |
| Interactivos: botones, campos, buscador, hover de pestañas, opciones de menú, elementos del menú lateral | 6 px |
| Casillas, contadores, etiquetas | 4 px |
| Subrayado del elemento activo | 0 (línea recta) |

- Bordes de 1 px en todas las zonas.
- Elementos del menú lateral: 36 px de alto, abierto o contraído. Botón de abrir y cerrar: 40 × 37 px.
- Los iconos del menú lateral no se desplazan al abrir o cerrar; solo aparecen o desaparecen las
  etiquetas.

## Interacción

- **Hover.** Elementos sin relleno: fondo con el 9 % de la tinta. Elementos rellenos con el
  principal (botón principal, casilla marcada): el principal oscurecido (78 % principal, 22 %
  negro), en ambos temas.
- **Transición del hover.** Entra en 0,08 s y sale en 0,35 s.
- **Campos de texto** (incluido el buscador): sin cambio de fondo; hover con borde de 1 px y foco
  con borde de 2 px, ambos en el principal (en el rojo de P1 si el campo tiene error). El foco
  siempre es más grueso que el hover.
- **Foco de teclado** del resto de elementos: contorno de 2 px en el principal.
- **Elemento activo** (pestaña, día de un calendario): sin relleno, en tinta, con una línea recta
  de 2 px en el principal por debajo.
- **Pestañas que no caben.** Se desvanecen y aparece un selector pegado a la izquierda del
  buscador: el texto de la pestaña activa con una flecha, sin subrayado. Se recalcula al cambiar de
  pestaña, al abrir o cerrar el menú y al redimensionar la ventana.
- **Menús de selección.** Mismo fondo, borde y tipografía que los campos; la opción activa en
  negrita con un chevron «>» a la izquierda. Accesibles con teclado (flechas, Inicio, Fin, Escape,
  búsqueda por letra).
- **Buscador.** Ancho fijo de 220 px.

## Movimiento

| Animación | Duración |
|---|---|
| Abrir y cerrar el menú lateral (sin rebote) | 0,25 s, salida suave |
| Etiquetas del menú lateral al abrir o cerrar | 0,15–0,2 s de fundido |
| Pestañas a selector y al revés | 0,15 s de salida, 0,2 s de entrada |
| Aparición de un menú desplegable | 0,18 s (fundido y 6 px de desplazamiento) |
| Cambio de tema | 0,4 s en todos los colores |

Si el sistema pide reducir el movimiento, no se anima nada.

## Datos

- **Gráficas de barras.** Series en secundario y en gris, sólidas y sin borde; cuadrícula de fondo
  de 16 px en color de cuadrícula.
- **Rejillas de estado.** Cuadros separados 4 px; los normales en gris y los que tienen un estado de
  alarma en su color; el estado neutro, como cuadrado vacío.
- **Tablas.** Cabecera en texto secundario, filas separadas por línea de 1 px, códigos y fechas en
  monoespaciada.

## Tipografía

| Uso | Fuente | Tamaño y peso |
|---|---|---|
| Nombre del sistema (menú lateral) | Manrope | 18 px, 700, línea inferior de 2,5 px a 6 px |
| Título de página | Manrope | 24 px, 600 |
| Título de bloque | Manrope | 15 px, 600 |
| Cifra destacada | Manrope | 28 px, 600 |
| Texto | Manrope | 14 px, 400–500 |
| Etiquetas y ayudas | Manrope | 12–12,5 px |
| Códigos, fechas, contadores | JetBrains Mono | 12–13 px, 400–500 |

Paquetes npm `@fontsource-variable/manrope` y `@fontsource-variable/jetbrains-mono` (licencia OFL).
Las cifras en columna usan `font-variant-numeric: tabular-nums`.

## Iconos y gráficos

- Iconos de la librería `lucide-react`, de trazo, a 16 px.
- Gráficas en SVG propio, sin librería.

## Accesibilidad

- Todo texto supera 4,5:1; formas de estado, iconos y bordes de controles, 3:1.
- Ningún estado se comunica solo con color.
- Los selectores propios se comportan como un `listbox` accesible.
