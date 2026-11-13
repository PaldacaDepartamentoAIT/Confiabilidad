# Spec: presentacion-registro
Estado: aprobada
Aprobación: ligera

## Objetivo (por qué)
Las pantallas públicas del registro muestran su card vacía mientras cargan sus datos, cambian de alto cuando
aparece un mensaje y, en la pantalla de verificación del código, separan los dos botones en líneas distintas y
no muestran como desactivado un botón bloqueado. Esta feature pule la presentación de esas pantallas: botones
en una línea, aspecto de desactivado, hueco reservado para el mensaje de reenvío y un fundido al mostrar cada
pantalla.

## Requisitos funcionales

### RF-001 Acciones de la verificación en una línea
El sistema deberá mostrar en la pantalla de verificación del código los botones «Enviar otro código» y
«Verificar» en la misma línea, alineados a la derecha, con «Enviar otro código» (secundario) a la izquierda y
«Verificar» (principal) a la derecha, separados 10 px. Cuando los dos botones no quepan en una línea (pantallas de menos de 480 px de ancho), el sistema deberá disponerlos en dos líneas, cada uno a todo el ancho de la card, con «Verificar» arriba y «Enviar otro código» debajo.

### RF-002 Aspecto de botón desactivado
Mientras un botón esté bloqueado, ya sea porque está desactivado o porque está procesando, el sistema deberá
mostrarlo atenuado al 60 % de opacidad y con el cursor de acción no permitida, sin cambiar su color al pasar el
puntero por encima. Esto vale para todos los botones del sistema.

### RF-003 Hueco reservado para el mensaje de reenvío
El sistema deberá mostrar en la pantalla de verificación, debajo del recuento de códigos que se pueden pedir
todavía (o del aviso de que no quedan), un hueco reservado del alto de dos líneas de texto donde aparezcan los mensajes del reenvío: el informativo, el de espera y el de error. El aviso de código bloqueado, el error del formulario y el aviso de que no quedan códigos (con su enlace al formulario) permanecen donde están. Cuando uno de esos mensajes aparezca o desaparezca, el
sistema no deberá cambiar el alto de la card. Si un mensaje ocupa más de dos líneas, entonces la card deberá
crecer lo justo para mostrarlo entero.

### RF-004 Card oculta mientras carga
Mientras una pantalla pública del registro (registro, verificación, cuenta creada y enlace no válido) esté
cargando los datos que necesita, el sistema no deberá mostrar su card y solo deberá verse la barra superior.
Cuando los datos estén listos, el sistema deberá mostrar la card completa con un fundido de entrada de 0,2 s.
Si la carga falla, o si no hay respuesta pasados 10 s, entonces el sistema deberá mostrar la card con el mensaje de error de conexión, con el mismo fundido.

### RF-005 Fundido entre pantallas
Cuando la persona pase de una pantalla pública del registro a otra, o cuando cambie el contenido de la card dentro de una misma pantalla (de la introducción del código a la elección de la contraseña), el sistema deberá mostrar el contenido nuevo con el mismo fundido de entrada de 0,2 s, sin mostrarlo vacío. Las pantallas que no cargan datos (cuenta creada y enlace no válido) entran con fundido en cuanto se pintan.

### RF-006 Movimiento reducido
Si el sistema operativo pide reducir el movimiento, entonces el sistema deberá mostrar las cards sin fundido,
de forma inmediata cuando estén listas.

### RF-007 Sin cambios de flujo
El sistema deberá conservar el flujo, los textos, las validaciones y los datos de las pantallas del registro
tal como están, y superar los tests que ya tienen, salvo los que dependan del orden o de la posición de lo que
esta feature cambia.

### RF-008 Catálogo
El sistema deberá mostrar en el catálogo un botón desactivado, de cada variante, con su aspecto de desactivado.

### RF-009 Barra superior estable
Mientras la persona cambia de pantalla pública del registro, el sistema deberá mantener la barra superior
(nombre del sistema y botones de idioma y de tema) fija, sin repintarla ni animarla, y conservar el idioma y el
tema elegidos.

## Supuestos
- S-01 «Cargar» significa esperar la respuesta del servidor que necesita la pantalla; mientras se espera no
  hay esqueleto ni indicador de carga, solo la barra superior.
- S-02 El alto de dos líneas se mide con el interlineado del texto de la card; el plan lo concreta en píxeles.
- S-03 (eliminado: la disposición en pantallas estrechas es ahora parte de RF-001).
- S-04 El aspecto de desactivado es el que tenían los botones antes de la limpieza de `base.css`: opacidad
  del 60 % y cursor de no permitido.
- S-05 El fundido de salida de la pantalla anterior no se anima: la anterior desaparece al cambiar de ruta y la
  nueva entra con fundido.
- S-06 Esta feature depende de `sistema-de-diseno` y de `casilla-con-documento`, que aún no están en `main`; su
  PR a `main` no puede fusionarse antes que los de aquellas.
- S-07 El límite de espera de 10 s se mide desde que la pantalla pide los datos, y la pantalla de error de conexión
  es la que ya existe.

## Fuera de alcance
- Esqueletos o indicadores de carga mientras se espera.
- Un fundido de salida (la pantalla que se va) o un fundido cruzado.
- Cambiar los textos, las validaciones o el flujo del registro.
- Un indicador de carga pasado el límite de espera.
- Pantallas con sesión y el resto de la aplicación, salvo el aspecto de los botones desactivados.

## Criterios de finalización
- Cada RF se cumple y está cubierto por un test.
- Las pantallas del registro superan sus tests previos, salvo los que dependan del orden o la posición de lo
  cambiado, que se actualizan.
- En un navegador real: los dos botones de la verificación van en una línea y el principal a la derecha; un
  botón bloqueado se ve atenuado; la card de la verificación no cambia de alto al aparecer o desaparecer el
  mensaje de reenvío; ninguna pantalla pública del registro muestra su card vacía mientras carga y entran con
  fundido; con movimiento reducido no hay fundido.
- No hay violaciones de accesibilidad automáticas en las pantallas afectadas, en ambos temas.
- Las pruebas visuales de `sistema-de-diseno` y de `casilla-con-documento` siguen pasando.

## Historial de cambios
- 2026-11-13 — Spec inicial — RF: RF-001 a RF-008 — Estado: pendiente de clarificar
- 2026-11-13 — Clarificación: C-01 a C-05 — RF: RF-001, RF-003, RF-004, RF-005, RF-009 — Estado: clarificado
