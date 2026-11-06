# Identidad visual

Estado: borrador

Referencia visual de la interfaz de Confiabilidad (web y escritorio). Define colores, tipografía,
formas, movimiento y reglas de uso. Los valores salen de la maqueta revisada con el usuario; el
código los recoge como variables CSS en `frontend/`, y `desktop/` los hereda al cargar el frontend.

Versión 2. Sustituye a la versión 1 (paleta Niebla marina, bloques bento, botones en píldora).

## Principios

1. **Plano y cuadrado.** Sin sombras, sin degradados, sin transparencias. Las zonas se separan con
   líneas de 1 px y radios pequeños.
2. **El color informa, no decora.** Lo normal va en neutro. Solo las alarmas y lo interactivo
   tienen color propio.
3. **Lo que se pulsa se reconoce.** Todo elemento interactivo tiene hover, foco visible y un radio
   mayor que el de las zonas que solo informan.
4. **Un color por función.** Cada color tiene un único papel; si dos elementos comparten color,
   comparten significado.
5. **Nada depende solo del color.** Cada estado lleva también forma y texto.

## Estructura de pantalla

- **Fondo único.** Lienzo y bloques usan el mismo color; los bloques se separan con borde.
- **Menú lateral** a la izquierda, con fondo del color secundario:
  - abierto mide 232 px y contraído 60 px; pasa de uno a otro con animación;
  - cabecera de 64 px con el título «Confiabilidad» a la izquierda y el botón de abrir y cerrar a
    la derecha; contraído, solo el botón, centrado;
  - secciones de navegación con icono y etiqueta;
  - pie con los botones de tema e idioma en una fila (apilados al contraer) y el de usuario debajo,
    a todo el ancho.
- **Barra superior** de 64 px, alineada con la cabecera del menú: secciones en pestañas a la
  izquierda y buscador a la derecha. El usuario no aparece en la barra superior.
- **Contenido** con margen de 22 px, ruta («Planta Concentradora / Área 210»), título de página y
  acciones a la derecha; las secciones se separan 18 px.
- **Móvil.** El menú lateral se oculta y se abre como panel superpuesto con el botón «>».

## Temas

Dos temas de igual rango, claro y oscuro: la usan ingenieros en oficina y operadores en sala de
control. Al arrancar se usa el tema del sistema operativo; el botón de tema lo cambia y la elección
se recuerda, igual que el idioma. Sustituye a la decisión D-13 de `registro-flujo`.

## Paleta: Pizarra

El contraste indicado es el del elemento sobre su fondo habitual (WCAG 2.2: mínimo 4,5:1 para texto
y 3:1 para iconos, formas y bordes de controles).

### Tema claro

| Rol | Color | Uso | Contraste |
|---|---|---|---|
| Fondo | `#f8f9f9` | Lienzo y bloques | — |
| Tinta | `#1b1e22` | Texto; relleno negro (tarjeta de alerta, criticidad A, botón de menú) | 15,9:1 |
| Texto secundario | `#61656b` | Etiquetas, ayudas, ejes, secciones no activas | 5,6:1 |
| Gris | `#c3c5c7` | Líneas, bordes de zonas, horas no planificadas, mapa de activos | 1,6:1 |
| Cuadrícula | `#d8dadb` | Cuadrícula de las gráficas | — |
| Borde de control | `#8d9094` | Borde de campos y casillas | 3,0:1 |
| Principal | `#546c8c` | Todo lo interactivo; texto blanco encima | 5,1:1 (5,4:1 con blanco) |
| Secundario | `#d8dbdf` | Menú lateral, tarjeta destacada, horas planificadas, evento en curso; texto en tinta | 12,0:1 con tinta |

### Tema oscuro

| Rol | Color | Uso | Contraste |
|---|---|---|---|
| Fondo | `#111213` | Lienzo y bloques | — |
| Tinta | `#eeeff1` | Texto | 16,3:1 |
| Relleno negro | `#111213` | Tarjeta de alerta, criticidad A | — |
| Texto secundario | `#aaadb0` | Etiquetas, ayudas, ejes, secciones no activas | 8,3:1 |
| Gris | `#47484a` | Líneas, bordes de zonas, horas no planificadas, mapa de activos | 2,0:1 |
| Cuadrícula | `#313234` | Cuadrícula de las gráficas | — |
| Borde de control | `#5f6163` | Borde de campos y casillas | 3,0:1 |
| Principal | `#9fafc6` | Todo lo interactivo; texto en color de fondo encima | 8,4:1 |
| Secundario | `#535a65` | Menú lateral, tarjeta destacada, horas planificadas, evento en curso; texto en tinta | 6,0:1 con tinta |
| Botón de menú | `#ffffff` | Fondo del botón de abrir y cerrar; icono en secundario | 7,0:1 |

### Alarmas

Un solo color por prioridad en toda la aplicación (mapa, tabla, aviso, tarjeta de alerta, campos
con error).

| Prioridad | Forma | Claro | Oscuro | Contraste sobre el fondo |
|---|---|---|---|---|
| P1 | Cuadrado | `#a47070` | `#a47070` | 3,9:1 · 4,6:1 |
| P2 | Triángulo | `#915535` | `#d9977a` | 5,6:1 · 7,7:1 |
| Advertencia | Rombo | `#7a7020` | `#c9bd8c` | 4,8:1 · 9,9:1 |
| Mantenimiento | Cuadrado vacío | Texto secundario | Texto secundario | — |

- **Color solo en la forma.** El texto del estado va en tinta y el color queda en el icono, porque
  el rojo de P1 no llega a 4,5:1 en el tema claro.
- **Aviso de alarma.** Bloque con borde izquierdo de 4 px en el color de la prioridad.
- **Tarjeta de alerta** (por ejemplo, OT vencidas): fondo en relleno negro; la cifra va en el color
  de la alarma y las etiquetas pequeñas en blanco.
- **Campo con error.** Borde y mensaje en el rojo de P1; el mensaje lleva además un icono.

## Forma

| Elemento | Radio |
|---|---|
| Zonas: secciones, tarjetas, aviso de alarma, menús desplegables | 4 px |
| Interactivos: botones, campos, buscador, hover de pestañas y días, opciones de menú, elementos del menú lateral, botón de menú | 6 px |
| Casillas, etiquetas de contador y criticidad | 4 px |
| Subrayado de la pestaña y del día activos | 0 (línea recta) |

- Bordes de 1 px en todas las zonas.
- Elementos del menú lateral: 36 px de alto, abierto o contraído. Botón de abrir y cerrar: 40 × 37 px.
- Los iconos del menú lateral no se desplazan al abrir o cerrar; solo aparecen o desaparecen las
  etiquetas.

## Interacción

- **Hover.** Elementos sin relleno: fondo con el 9 % de la tinta. Botón principal y casilla
  marcada: el principal oscurecido (78 % principal, 22 % negro), en ambos temas.
- **Transición del hover.** Entra en 0,08 s y sale en 0,35 s.
- **Campos de texto** (incluido el buscador): sin cambio de fondo; hover con borde de 1 px y foco
  con borde de 2 px, ambos en el principal (en el rojo de P1 si el campo tiene error). El foco
  siempre es más grueso que el hover.
- **Foco de teclado** del resto de elementos: contorno de 2 px en el principal.
- **Pestañas.** Sin caja; la activa va en tinta con una línea recta de 2 px en el principal por
  debajo. Si no caben, se desvanecen y aparece un selector pegado a la izquierda del buscador: el
  texto de la sección activa con una flecha, sin subrayado. Se recalcula al cambiar de sección, al
  abrir o cerrar el menú y al redimensionar la ventana.
- **Calendario.** El día activo no tiene relleno; lleva la misma línea que la pestaña activa.
- **Menús de selección** (selector de secciones y selectores de formulario): mismo fondo, borde y
  tipografía que los campos; la opción activa en negrita con un chevron «>» a la izquierda.
  Accesibles con teclado (flechas, Inicio, Fin, Escape, búsqueda por letra).
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

- **Gráfica de barras.** Horas planificadas en secundario y no planificadas en gris, sólidas y sin
  borde; cuadrícula de fondo de 16 px en color de cuadrícula.
- **Mapa de activos.** 12 cuadros por fila, separados 4 px; los normales en gris y los de alarma
  en su color; mantenimiento como cuadrado vacío.
- **Tablas.** Cabecera en texto secundario, filas separadas por línea de 1 px, TAG y fechas en
  monoespaciada.

## Tipografía

| Uso | Fuente | Tamaño y peso |
|---|---|---|
| Título del sistema (menú lateral) | Manrope | 18 px, 700, línea inferior de 2,5 px a 6 px |
| Título de página | Manrope | 24 px, 600 |
| Título de sección | Manrope | 15 px, 600 |
| Cifra de indicador | Manrope | 28 px, 600 |
| Texto | Manrope | 14 px, 400–500 |
| Etiquetas y ayudas | Manrope | 12–12,5 px |
| TAG, OT, fechas, contadores | JetBrains Mono | 12–13 px, 400–500 |

Paquetes npm `@fontsource-variable/manrope` y `@fontsource-variable/jetbrains-mono` (licencia OFL).
Las cifras en columna usan `font-variant-numeric: tabular-nums`.

## Iconos y gráficos

- Iconos de la librería `lucide-react`, de trazo, a 16 px.
- Gráficas en SVG propio, sin librería.

## Accesibilidad

- Todo texto supera 4,5:1; formas de estado, iconos y bordes de controles, 3:1.
- Ningún estado se comunica solo con color.
- Los selectores propios se comportan como un `listbox` accesible.
