# Spec: sistema-de-diseno
Estado: aprobada
Aprobación: ligera

## Objetivo (por qué)
Todas las pantallas de la aplicación deben verse y comportarse igual sin que cada una reinvente su
estructura. La identidad visual ya está definida (`docs/identidad-visual.md`) y fijada en dos pantallas
de referencia aprobadas (`docs/referencia/crear-empresa.html` y `docs/referencia/activos.html`). Esta
feature convierte esa identidad en piezas reutilizables de la aplicación (menú lateral, barra
superior, bloques, campos, botones, avisos, indicadores, tabla, gráfica y rejilla de estado), aplica
la identidad a lo que ya existe (registro y página de muestra) y añade la comprobación automática de
que cada pieza coincide con la referencia. Las pantallas de negocio (empresas, plantas, activos…) son
de otras features: esta no las crea.

## Requisitos funcionales

### RF-001 Tema inicial
Cuando el usuario abra la aplicación sin una elección de tema válida guardada en ese navegador, el
sistema deberá mostrar el tema claro u oscuro que use su sistema operativo.

### RF-002 Botón de tema
Cuando el usuario pulse el botón de tema, el sistema deberá alternar entre el tema claro y el oscuro
con una transición de 0,4 s, indicar con su etiqueta e icono el tema activo y recordar la elección
en ese navegador para las siguientes visitas, por encima del tema del sistema operativo.

### RF-003 Tema guardado no válido
Si el tema guardado en el navegador no es «claro» ni «oscuro», entonces el sistema deberá ignorarlo,
borrarlo y aplicar RF-001.

### RF-004 Movimiento reducido
Mientras el sistema operativo del usuario pida reducir el movimiento, el sistema deberá mostrar todos
los cambios (transiciones, fundidos, desplazamientos de la línea de pestañas y paneles) sin animación.

### RF-005 Diseño público
El sistema deberá ofrecer un diseño para pantallas sin sesión con una barra superior de 64 px que
muestre el nombre del sistema a la izquierda y, a la derecha, el botón de idioma (que muestra el código del idioma activo y abre el selector de idioma de RF-003 a RF-005 de `componentes-base-accesibles`) y el botón de tema,
sin menú lateral, y con el contenido debajo.

### RF-006 Diseño con sesión
El sistema deberá ofrecer un diseño para pantallas con sesión compuesto por un menú lateral a la
altura completa de la pantalla, una barra superior y el área de contenido, con las medidas, colores y
márgenes de la guía.

### RF-007 Menú lateral
El sistema deberá ofrecer un menú lateral con cabecera (nombre del sistema y botón de abrir y cerrar),
elementos de navegación con icono y etiqueta, el elemento de la página actual marcado, y un pie con
el botón de tema, el de idioma (igual que en RF-005) y el del usuario. El botón del usuario muestra su avatar y nombre; si la pantalla le pasa una acción, es pulsable y la ejecuta, y si no, no es pulsable. Los elementos de navegación se reciben como datos y
cada elemento puede mostrar un contador.

### RF-008 Contraer y expandir el menú
Cuando el usuario pulse el botón de abrir y cerrar del menú, el sistema deberá alternar el menú entre
232 px y 60 px; contraído solo se ven los iconos, que no cambian de posición, y el botón muestra «>»
(y «<» con el menú abierto) y anuncia su estado al lector de pantalla.

### RF-009 Menú en pantallas pequeñas
Mientras la pantalla sea más estrecha que 768 px, el sistema deberá ocultar el menú lateral y
ofrecer en la barra superior un botón que lo abra como panel superpuesto, sin velo detrás; el panel
deberá cerrarse al pulsar fuera de él, al pulsar Escape o al elegir un elemento, y no deberá existir
el estado contraído. Cuando el panel se cierre, el foco deberá volver al botón que lo abrió.

### RF-010 Barra superior con pestañas
El sistema deberá ofrecer una barra superior con pestañas a la izquierda y un buscador a la derecha;
la pestaña activa lleva una línea de 2 px que se desplaza hasta la nueva pestaña (0,25 s) cuando
cambia la selección, y las pestañas se manejan con el teclado (flechas, Inicio y Fin). El buscador es solo visual: no filtra ni emite búsquedas; el comportamiento lo define la feature de cada pantalla que lo use.

### RF-011 Pestañas que no caben
Si las pestañas no caben en la barra, entonces el sistema deberá sustituirlas por un selector con el
nombre de la pestaña activa que despliegue las demás, con la animación de la guía.

### RF-012 Buscador en pantallas pequeñas
Mientras la pantalla sea más estrecha que 560 px, el sistema deberá reducir el buscador a un botón
que despliegue el campo sobre las pestañas y lo cierre con Escape.

### RF-013 Cambio de sección
Cuando el usuario cambie de pestaña, el sistema deberá mostrar el nuevo contenido con un fundido de
0,2 s y ocultar el anterior, de modo que solo una sección sea visible.

### RF-014 Bloque
El sistema deberá ofrecer un bloque con cabecera opcional (título, contador y acciones) en tres
variantes: normal, destacado y en alerta (fondo negro, texto blanco).

### RF-015 Campos de formulario
El sistema deberá mostrar los campos de texto, de contraseña y de código con el aspecto de la guía:
etiqueta, ayuda, marca de obligatorio, borde de 1 px al pasar el cursor, de 2 px con el foco (sin
mover el resto del contenido) y borde y mensaje de error con el icono de forma cuando el campo sea
inválido, conservando los comportamientos de RF-011 a RF-016 de `componentes-base-accesibles`.

### RF-016 Selector propio
El sistema deberá ofrecer un selector que sustituya al nativo, con un disparador igual a un campo y
un menú de opciones con la animación de la guía, que se abra y cierre con el ratón y el teclado
(Enter, Espacio, flechas, Inicio, Fin, Escape y escritura para saltar a una opción), marque la opción
seleccionada, muestre el error de campo y comunique al lector de pantalla su valor, su estado
abierto o cerrado y la opción resaltada. Esto rige en dispositivos cuyo puntero principal no es táctil; en los táctiles se aplica RF-031.

### RF-017 Casilla de verificación
El sistema deberá ofrecer una casilla de verificación con etiqueta y texto de ayuda opcional, con el
aspecto de la guía y marcada con un icono de verificación centrado.

### RF-018 Botones
El sistema deberá mostrar los botones principal y secundario con las medidas, colores y estados al
pasar el cursor, con foco y procesando de la guía, conservando RF-009 y RF-010 de
`componentes-base-accesibles`.

### RF-019 Avisos
El sistema deberá ofrecer un aviso con borde izquierdo de 4 px y un aviso de alarma con el icono de
forma de su prioridad, título, texto y una acción opcional.

### RF-020 Formas de alarma
El sistema deberá representar cada prioridad con una forma y un color: P1 cuadrado, P2 triángulo,
advertencia rombo y neutro cuadrado vacío; el texto de estado siempre va en la tinta y nunca
dependerá solo del color.

### RF-021 Indicador
El sistema deberá ofrecer un indicador con etiqueta, cifra y ayuda en tres variantes (normal,
destacado y en alerta con la cifra en el color de la prioridad) y una rejilla que los distribuya.

### RF-022 Tabla
El sistema deberá ofrecer una tabla con cabecera, filas de 44 px, columnas de texto, de código en
fuente monoespaciada y de estado con icono de forma, con desplazamiento horizontal si no cabe, y,
si no tiene filas, entonces deberá mostrar un mensaje de vacío en lugar de las filas.

### RF-023 Chip
El sistema deberá ofrecer un chip de 12 px para etiquetas como la criticidad.

### RF-024 Gráfica de barras
El sistema deberá ofrecer una gráfica de barras de dos series (la primera en el color principal, la
segunda en gris) con cuadrícula, ejes, leyenda y un texto alternativo que describa los datos, que se
escale al ancho de su bloque. El eje vertical deberá ir de 0 al siguiente múltiplo de 30 que cubra el mayor valor (mínimo 30), con marcas cada 30, y el ancho de cada grupo se ajustará al número de grupos recibidos. Si algún valor es negativo o no es un número, entonces deberá tratarlo como datos no válidos y mostrar el mensaje de vacío; si no recibe datos, entonces deberá mostrar un mensaje de vacío.

### RF-025 Rejilla de estado
El sistema deberá ofrecer una rejilla de cuadros de estado con su leyenda, donde cada cuadro lleve el
glifo de su forma, un título y una etiqueta accesible con su estado.

### RF-026 Aplicación a lo existente
El sistema deberá mostrar las pantallas de registro y la página de muestra con la identidad nueva y el
diseño público (RF-005), sin cambiar su flujo, sus textos ni sus validaciones, y superando los tests
que ya tienen.

### RF-027 Catálogo
El sistema deberá mantener una página de catálogo (la página de muestra) que exhiba cada pieza de
esta feature en sus variantes y estados, en ambos temas y en ambos diseños, con elementos de ejemplo.

### RF-028 Comprobación contra la referencia
El sistema deberá comprobar de forma automática, en tema claro y oscuro, que los estilos calculados
de cada pieza coinciden, con igualdad exacta y sin tolerancia, con los de las pantallas de referencia en tamaño de fuente, peso, familia, interlineado, espaciado de letras, color, fondo, grosor y color de bordes, radio y relleno, y además en alto (y ancho en las de tamaño fijo). Deberá fallar si alguna propiedad difiere. Cada pieza deberá existir en al menos una referencia; las que no existan en la comparada se omiten.

### RF-029 Accesibilidad
El sistema deberá permitir usar todas las piezas solo con el teclado, mostrar siempre un foco
visible, cumplir el contraste AA en ambos temas y no depender solo del color para transmitir un
estado.

### RF-030 Idiomas
El sistema deberá mostrar los textos de las piezas (etiquetas de botones, contadores, estados vacíos,
nombres accesibles) en español, portugués de Brasil e inglés, según RF-001 a RF-008 de
`componentes-base-accesibles`.

### RF-031 Selector en dispositivos táctiles
Mientras el dispositivo tenga un puntero principal táctil, el sistema deberá mostrar el selector nativo del sistema con la misma etiqueta, valor, opciones y error de RF-016 y el aspecto de campo de la guía.

## Supuestos
- S-01 El botón de tema tiene solo dos estados (claro y oscuro); una vez pulsado, no hay forma de
  volver a «seguir al sistema operativo» salvo borrar los datos del navegador.
- S-02 El menú lateral no recuerda si estaba contraído; siempre arranca abierto.
- S-03 Los textos de ejemplo del catálogo (secciones, nombres, cifras) son inventados y no
  representan funciones reales.
- S-04 Los datos de las piezas (elementos del menú, pestañas, filas, series) llegan ya listos; esta
  feature no consulta ningún servicio.
- S-05 Los textos de los estados vacíos de tabla y gráfica son provisionales hasta que lleguen los
  definitivos.
- S-06 El selector propio conserva la misma información que el nativo (valor, opciones, etiqueta,
  error) y sustituye al nativo donde este se use.
- S-07 Los colores de las prioridades P1, P2 y advertencia son los de la guía en cada tema.

## Fuera de alcance
- Pantallas de negocio (empresas, plantas, activos, órdenes, alarmas) y sus rutas con sesión.
- Autenticación, sesión de usuario y permisos que decidan qué ve cada usuario en el menú.
- Datos reales para tabla, gráfica e indicadores.
- Recordar el estado contraído del menú.
- Idiomas distintos de español, portugués de Brasil e inglés.
- Cliente de escritorio: hereda la interfaz web sin cambios propios.

## Criterios de finalización
- Cada RF se cumple y está cubierto por un test.
- Las pantallas de registro y la página de muestra superan sus tests previos.
- El test de comparación (RF-028) pasa en tema claro y oscuro para todas las piezas.
- No hay violaciones de accesibilidad automáticas en el catálogo en ambos temas.
- El catálogo exhibe todas las piezas y los dos diseños.
- Los selectores nativo y propio muestran el mismo valor y error según el tipo de puntero.

## Historial de cambios
- 2026-11-09 — Spec inicial — RF: RF-001 a RF-030 — Estado: clarificado
- 2026-11-09 — Clarificación: C-01 a C-09 — RF: RF-005, RF-007, RF-009, RF-010, RF-012, RF-015, RF-016, RF-024, RF-028, RF-031 — Estado: clarificado
- 2026-11-10 — Corrección de RF-009: sin velo, según la guía y las referencias — RF: RF-009 — Estado: clarificado
