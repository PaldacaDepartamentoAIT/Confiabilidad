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
- Sin degradado de fondo, sin transparencias y sin animación de fondo.

## Temas

Dos temas de igual rango, claro y oscuro: la aplicación la usan tanto ingenieros en oficina como
operadores en sala de control. Al arrancar se usa el tema del sistema operativo; si el usuario
elige uno, se recuerda, igual que el idioma.

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

## Interacción y forma

| Elemento | Forma |
|---|---|
| Botones, pestañas, buscador, menú de usuario, días del calendario | Píldora (radio 999 px) |
| Botones de icono, iconos de la barra lateral, avatar | Círculo |
| Casillas de verificación | Cuadradas, radio 4 px (convención reconocible) |
| Tarjetas y paneles | Radio 12 px |
| Etiquetas, criticidad, franjas del calendario, barra de tiempo | Radio 4 px |

- **Foco visible:** contorno de 3 px en color de acción, separado 2 px del elemento.
- La criticidad A va rellena en relleno fuerte; B con borde de tinta; C con borde de texto
  secundario.

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
- Si el sistema pide reducir el movimiento, no se anima nada que no sea imprescindible.
