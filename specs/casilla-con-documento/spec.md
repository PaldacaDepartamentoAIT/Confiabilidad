# Spec: casilla-con-documento
Estado: aprobada
Aprobación: ligera

## Objetivo (por qué)
Los formularios que piden aceptar un documento (términos y condiciones, consentimiento de marketing)
hoy lo muestran en un desplegable dentro del propio formulario, lo que lo alarga y empuja el resto de
campos. Esta feature ofrece una casilla cuyo texto es un enlace que abre el documento en una ventana
modal, de modo que el formulario sigue siendo corto y quien acepta puede leer el documento completo, y
la usa en el formulario de registro.

## Requisitos funcionales

### RF-001 Casilla con enlace al documento
Donde se indique un documento para la casilla, el sistema deberá mostrar el texto de su etiqueta como un
enlace. Cuando la persona pulse el enlace, el sistema deberá abrir el modal con el documento sin marcar
ni desmarcar la casilla; cuando pulse el cuadro de la casilla, el sistema deberá marcarla o desmarcarla sin abrir el modal. Cuando pulse cualquier otra parte de la fila (el hueco entre el cuadro y el texto o lo que sobra a la derecha), el sistema no deberá hacer nada.

### RF-002 Estructura del modal
Mientras el modal esté abierto, el sistema deberá mostrar una caja sobre una cortina que cubre la pantalla, con tres partes en este orden: un botón «x» arriba, el contenido del documento con desplazamiento y, abajo, una casilla con el mismo texto que el enlace. La cortina deberá ser negra al 50 % de opacidad y la caja deberá usar el relleno negro del sistema de diseño (`#1b1e22` en tema claro y `#000000` en oscuro) con texto blanco.

### RF-003 Contenido del documento
El sistema deberá mostrar el documento dentro del modal con su formato (Markdown: títulos, párrafos,
listas, énfasis y enlaces), sin exigir llegar al final del texto para poder marcar la casilla. Cuando la persona pulse un enlace del documento, el sistema deberá abrirlo en una pestaña nueva, sin cerrar el modal ni salir de la página.

### RF-004 Casilla del modal sincronizada
Mientras el modal esté abierto, el sistema deberá mantener sincronizado el estado de la casilla del
modal con el de la casilla del formulario: cuando la persona marque o desmarque una, la otra deberá
reflejar el mismo estado. A diferencia de la del formulario, el texto de la casilla del modal es una
etiqueta corriente: cuando la persona pulse su texto, el sistema deberá marcar o desmarcar la casilla. Además, la casilla del modal deberá mostrar el texto de la etiqueta y, si la casilla es obligatoria, su asterisco, sin repetir la ayuda ni el error.

### RF-005 El modal sigue abierto al marcar
Cuando la persona marque o desmarque la casilla del modal, el sistema deberá mantener el modal abierto.

### RF-006 Cierre del modal
Cuando la persona pulse la «x», pulse la tecla Escape o pulse la cortina, el sistema deberá cerrar el
modal y devolver el foco al enlace que lo abrió, conservando el estado de la casilla.

### RF-007 Fondo bloqueado
Mientras el modal esté abierto, el sistema deberá impedir que la página de detrás se desplace y deberá
mantener el foco del teclado dentro del modal, de modo que Tab recorra solo la «x», el contenido con desplazamiento (y los enlaces que contenga) y la casilla.

### RF-008 Nombre accesible
Mientras el modal esté abierto, el sistema deberá exponerlo a las tecnologías de apoyo como un diálogo
modal cuyo nombre sea el texto de la etiqueta, sin mostrar un título visible.

### RF-009 Tamaño del modal
El sistema deberá mostrar la caja del modal centrada, con un ancho máximo de 640 px y un alto máximo del
80 % de la pantalla; en pantallas de menos de 700 px de ancho deberá ocupar casi todo el ancho con 16 px de margen. Si el alto visible no alcanza para el 80 %, entonces la caja deberá dejar 16 px de margen arriba y abajo y mantener visibles la «x» y la casilla. Cuando
el documento no quepa, el sistema deberá desplazar solo el contenido, manteniendo siempre visibles la
«x» y la casilla.

### RF-010 Casilla sin documento
Si el documento indicado no tiene contenido, entonces el sistema deberá mostrar la casilla como una
casilla normal, con su etiqueta como texto y sin enlace ni modal.

### RF-011 Casilla obligatoria, opcional y con error
El sistema deberá conservar para esta casilla los comportamientos de una casilla de verificación del
sistema de diseño: marca de obligatoria, ayuda opcional, error con su icono y la reserva de espacio que
evita que el formulario cambie de alto al aparecer el error. El error se mostrará junto a la casilla del formulario, no en el modal. Si la casilla está en error y la persona la marca desde el modal, el error deberá mantenerse mientras el modal siga abierto; al cerrarlo, el sistema deberá revalidar y retirar el error si la casilla está marcada.

### RF-012 Uso en el registro
El sistema deberá mostrar en el formulario de registro la aceptación de los términos (obligatoria) y,
donde exista documento de marketing, el consentimiento de marketing (opcional) con esta casilla, una
encima de la otra, en lugar de los desplegables actuales, conservando el flujo, los textos, las
validaciones y los datos que el formulario envía hoy (versión e idioma de cada documento aceptado).

### RF-013 Catálogo
El sistema deberá mostrar en la página de catálogo la casilla con documento: obligatoria, opcional, con
error y sin documento, y abrir el modal en cada caso que tenga documento.

### RF-014 Idiomas
El sistema deberá ofrecer en español, portugués de Brasil e inglés los textos propios del componente
(por ejemplo, el nombre del botón de cerrar), con la misma paridad de claves que el resto de la
aplicación.

### RF-015 Accesibilidad
El sistema deberá poder usarse por completo con el teclado (abrir con Enter sobre el enlace, recorrer el
modal con Tab, marcar con Espacio, cerrar con Escape) y deberá cumplir contraste AA y no tener
violaciones de accesibilidad, en tema claro y oscuro, con el modal cerrado y abierto.

### RF-016 Cambios con el modal abierto
Mientras el modal esté abierto, cuando cambie el idioma o el tamaño de la pantalla (por ejemplo, al girar
un móvil), el sistema deberá actualizar los textos y recalcular la caja manteniendo el modal abierto, el
foco y el estado de la casilla.

## Supuestos
- S-01 El documento llega a la casilla ya cargado y en Markdown; quién lo pide al servidor y en qué
  idioma es cosa de la pantalla, no de la casilla.
- S-02 Las medidas y colores de la caja salen de la guía visual: la caja usa el relleno negro y el texto
  blanco del bloque en alerta, y la cortina es un negro semitransparente. En tema oscuro la caja se
  distingue de la cortina con un borde del color de las líneas. El plan las concreta y se añaden a la
  guía.
- S-03 La caja aparece con un fundido corto y sin animación cuando el sistema pide reducir el movimiento.
- S-04 Marcar la casilla del formulario sin abrir el modal es válido: no se exige haber abierto el
  documento.
- S-05 Esta feature depende de `sistema-de-diseno` (casilla, bloque, botones y reserva del error), que
  aún no está en `main`; su PR final a `main` no puede fusionarse antes que el de aquella.
- S-06 Se cambian los tests del registro que miran los desplegables actuales; el resto de sus tests
  sigue igual.

## Fuera de alcance
- Exigir llegar al final del documento antes de poder aceptar.
- Registrar si la persona abrió o leyó el documento.
- Rediseñar el resto del formulario de registro (panel de progreso, disposición en columnas y de los
  campos): será otra feature.
- Un panel lateral en vez de una caja centrada.
- Cambiar el contenido, las versiones o la obtención de los documentos legales (backend).
- Más de un modal abierto a la vez.

## Criterios de finalización
- Cada RF se cumple y está cubierto por un test.
- El registro supera sus tests previos, salvo los que describían los desplegables, que se sustituyen por
  los de la casilla con documento.
- No hay violaciones de accesibilidad automáticas en el catálogo y en el registro, en ambos temas, con
  el modal cerrado y abierto.
- En un navegador real: el modal abre y cierra por sus tres vías, el contenido se desplaza sin mover la
  «x» ni la casilla, el foco queda dentro del modal y vuelve al enlace, y la página de detrás no se
  desplaza.
- Las pruebas visuales de `sistema-de-diseno` siguen pasando.

## Historial de cambios
- 2026-11-12 — Spec inicial — RF: RF-001 a RF-015 — Estado: pendiente de clarificar
- 2026-11-12 — Clarificación: C-01 a C-07 — RF: RF-001, RF-002, RF-003, RF-004, RF-007, RF-009, RF-011, RF-016 — Estado: clarificado
- 2026-11-13 — Validación: cerrada con riesgo residual aceptado por el usuario (14 de 16 RF cumplidos; RF-001 y RF-016 sin prueba completa en un navegador real). Riesgos aceptados: (1) RF-001: la prueba de que pulsar el hueco de la fila no hace nada corre solo en jsdom y no detectaría que la fila se envolviera en una etiqueta `<label>` (impacto medio, probabilidad baja); (2) RF-016: ninguna prueba en Chromium comprueba que se conservan el foco y el estado de la casilla al cambiar el tamaño con el modal de la casilla abierto (bajo, muy baja); (3) el contraste y el tema oscuro del registro solo se comprueban en jsdom y por sondeo manual, sin prueba en Chromium (bajo, baja); (4) defecto de código conocido de S-03: con «reducir movimiento» la cortina del modal (`::backdrop`) sigue animándose con un fundido de 0,2 s, aunque la caja no (bajo, baja); (5) observaciones menores: Tab no se comprueba hacia todos los elementos del modal en Chromium, la prueba de desplazamiento mide la «x» y no el pie, la reserva de espacio del error no se mide en la casilla con documento y los «Cómo probarlo» de `tasks.md` llevan comandos en línea — Estado: validada con riesgo residual
