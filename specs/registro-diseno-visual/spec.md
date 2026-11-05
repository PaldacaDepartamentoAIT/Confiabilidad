# Spec: registro-diseno-visual
Estado: aprobada
Aprobación: ligera

## Objetivo (por qué)
El registro funciona de extremo a extremo (`registro-flujo`), pero sus pantallas se ven como
documentos sueltos: no dicen en qué paso está la persona ni cuántos quedan, cada paso parece una
página nueva, los términos se despliegan dentro del formulario y los errores lo hacen cambiar de
alto al aparecer. Esta feature le da al registro el aspecto de un único asistente por pasos,
tomando como referencia la imagen aportada por el usuario (indicador de pasos arriba, campos con su
nombre encima y ayuda breve), adaptada a `docs/identidad-visual.md`. Además, añade a toda la
aplicación una barra superior con el idioma y el tema. No cambia ninguna regla del registro: los
datos, las validaciones, los mensajes y las respuestas del servidor siguen siendo los de
`registro-flujo` y `componentes-base-accesibles`.

En este documento, «paso» es cada una de las tres pantallas del asistente: formulario,
verificación y contraseña. «Cuenta creada» es la pantalla final, que no es un paso. «RF-0xx de
`registro-flujo`» y «RF-0xx de `componentes-base-accesibles`» remiten a esas specs.

## Requisitos funcionales

### Barra superior

### RF-001 Barra superior
El sistema deberá mostrar en todas las pantallas de la aplicación una barra superior con un botón
de idioma y un botón de tema.

### RF-002 Botón de idioma
El sistema deberá mostrar en el botón de idioma la abreviatura del idioma activo («ES», «EN» o
«PT»). Cuando la persona active el botón, el sistema deberá desplegar las tres opciones de idioma
con su nombre en ese mismo idioma e indicar cuál está activa (RF-003 de
`componentes-base-accesibles`). Cuando elija una, el sistema deberá cerrar las opciones y aplicar
el idioma según RF-004 y RF-005 de `componentes-base-accesibles`, con el foco de vuelta en el botón.

### RF-003 Botón de tema
El sistema deberá mostrar en el botón de tema un sol mientras esté activo el tema claro y una luna
mientras esté activo el oscuro. Cuando la persona active el botón, el sistema deberá desplegar las
opciones «Claro» y «Oscuro» e indicar cuál está activa. Cuando elija una, el sistema deberá cerrar
las opciones, aplicar ese tema a toda la aplicación sin recargar la página ni perder lo escrito, y
dejar el foco en el botón.

### RF-004 Tema inicial y recordado
Cuando la persona abra la aplicación sin haber elegido nunca un tema en ese navegador, el sistema
deberá usar el tema del sistema operativo. Cuando haya elegido uno, el sistema deberá usarlo en las
siguientes visitas desde el mismo navegador, por encima del del sistema operativo. Si el tema
guardado no es válido, entonces el sistema deberá ignorarlo, borrarlo y usar el del sistema
operativo. La primera pantalla que se pinte deberá mostrarse ya con el tema que corresponda, sin que
se vea el otro ni un instante.

### RF-005 Menús desplegables de la barra
Mientras las opciones de idioma o de tema estén desplegadas, el sistema deberá permitir recorrerlas
y elegirlas solo con el teclado, y cerrarlas sin cambiar nada al pulsar Escape, al hacer clic fuera
o al llevar el foco fuera de ellas. Al cerrarse con Escape, el foco deberá volver a su botón. Nunca
deberá haber más de un menú desplegado a la vez.

### Indicador de pasos y transición

### RF-006 Indicador de pasos
El sistema deberá mostrar encima del contenido de cada paso un indicador con tres pasos numerados
(formulario, verificación y contraseña), unidos por líneas, en el que el paso actual y los
completados se distingan de los pendientes por forma y por texto, no solo por color. El indicador
deberá comunicar al lector de pantalla el nombre del paso actual y su posición («paso 2 de 3»).

### RF-007 Avance del indicador
Cuando el flujo pase de un paso a otro, el sistema deberá actualizar el indicador al paso nuevo,
marcándolo con una animación, sin desplazar el indicador: hacia delante al avanzar y hacia atrás al
retroceder. Se retrocede cuando la pantalla de contraseña vuelve a la de verificación según RF-011 de
`registro-flujo`, y cuando la persona pulsa «Atrás» del navegador desde la verificación o la
contraseña, que la lleva al formulario vacío como hasta ahora (paso 1).

### RF-008 Indicador en la cuenta creada
Cuando se muestre la pantalla de cuenta creada, el sistema deberá mostrar el indicador con los tres
pasos completados.

### RF-009 Transición lateral
Cuando el flujo pase de un paso a otro, o del último paso a la cuenta creada, el sistema deberá
desplazar el contenido en horizontal, sin recargar la página ni mostrar un estado intermedio vacío.
Al avanzar, el contenido nuevo (título del paso y tarjeta) deberá entrar por la derecha y el
anterior salir por la izquierda; al retroceder, al revés. La barra superior y el indicador de pasos no
deberán desplazarse. El desplazamiento deberá verse igual en todos los navegadores admitidos y en la
aplicación de escritorio, aunque no admitan transiciones de vista.

### RF-010 Movimiento reducido
Mientras el sistema operativo pida reducir el movimiento, el sistema deberá cambiar de paso sin
desplazamiento ni animación del indicador ni del icono del selector (RF-017).

### RF-011 Foco tras cambiar de paso
Cuando termine el cambio de paso, el sistema deberá llevar el foco al título del paso nuevo, y no
deberá quedar ningún elemento enfocable del paso anterior. Si el paso nuevo se abre con errores que
hay que mostrar (RF-003 y RF-011 de `registro-flujo`), entonces el foco deberá seguir las reglas de
esos requisitos.

### RF-012 Solo avanzar
El sistema deberá mostrar en cada paso un único botón principal, alineado a la derecha y con una
flecha hacia la derecha junto a su texto, y ningún botón para volver al paso anterior.

### Campos

### RF-013 Nombre del campo y obligatoriedad
El sistema deberá mostrar el nombre de cada campo encima de él, y en los obligatorios un asterisco
junto al nombre que el lector de pantalla no lea como texto suelto, manteniendo la leyenda de campos
obligatorios.

### RF-014 Botón de ayuda «?»
El sistema deberá mostrar, junto al nombre de los campos nombre completo, fecha de nacimiento,
correo, país, código y contraseña de las pantallas del registro, un botón circular con el signo «?». Cuando la persona pase el puntero por encima, lo enfoque con el teclado
o lo toque, el sistema deberá mostrar un globo con la descripción del campo, y cuando el puntero o
el foco se vayan, al volver a tocarlo o al pulsar Escape, deberá ocultarlo. La descripción deberá
estar asociada al campo para que el lector de pantalla la lea al llegar a él, y traducida en los
tres idiomas. Las casillas de términos y de marketing y los campos de la página de muestra no
deberán llevarlo.

### RF-015 Reglas de la contraseña visibles
El sistema deberá seguir mostrando bajo el campo de contraseña nueva su texto de ayuda con las
reglas, siempre visible (RF-027 de `componentes-base-accesibles`), además del botón «?».

### RF-016 Espacio reservado para el error
El sistema deberá reservar bajo cada campo, y bajo la casilla de términos, el alto de una línea de
mensaje de error, tenga o no error, de modo que aparecer o desaparecer un error de una línea no
cambie el alto del formulario. Si un error necesita más de una línea, entonces el sistema deberá
mostrarlo completo, sin cortarlo, y el formulario podrá crecer solo mientras ese error esté visible.

### RF-017 Selector con flecha
El sistema deberá mostrar cada campo de selección con un aspecto y una lista de opciones propios,
sin la apariencia nativa del navegador en ningún estado, con una flecha hacia abajo en su extremo
derecho. Cuando se desplieguen las opciones, el sistema deberá girar la flecha hacia arriba con una
animación, y deshacer el giro al cerrarlas. El selector deberá poder usarse solo con el teclado:
abrirlo, recorrer las opciones con las flechas, saltar a una opción tecleando el principio de su
nombre, elegirla con Intro y cerrarlo sin cambios con Escape. También deberá anunciar al lector de
pantalla su nombre, si es obligatorio, su valor, si está desplegado y la opción resaltada. Al elegir
una opción o cerrarlo, el foco deberá volver al selector.

### RF-018 Mostrar u ocultar la contraseña con un ojo
El sistema deberá mostrar el control de mostrar u ocultar la contraseña dentro del campo, en su
extremo derecho, como un botón de icono: un ojo mientras la contraseña esté oculta (acción
«mostrar») y un ojo tachado mientras esté visible (acción «ocultar»). El texto escrito no deberá
quedar debajo del icono. Su nombre accesible seguirá siendo el de RF-012 de
`componentes-base-accesibles`.

### RF-023 Zona de mensajes del paso
El sistema deberá reservar en cada paso, encima del botón principal, una zona de mensajes con el alto
de una línea, haya o no mensaje, para el mensaje general (RF-003 de `registro-flujo`), el aviso de
espera por límite superado, el de bloqueo tras cinco intentos y el de código caducado. Si un mensaje
necesita más de una línea, entonces el sistema deberá mostrarlo completo y la zona podrá crecer solo
mientras esté visible.

### Términos y marketing

### RF-019 Casilla de términos
El sistema deberá mostrar la aceptación de los términos como una sola casilla con el texto «Acepto
los términos y condiciones *», en el idioma de la interfaz, en el que «términos y condiciones» sea
un enlace subrayado, y no deberá mostrar el texto de los términos desplegado dentro del formulario.

### RF-020 Casilla de marketing
Donde haya un documento de marketing vigente, el sistema deberá mostrar la casilla de marketing
(opcional y sin marcar, RF-001 de `registro-flujo`) con el mismo formato que la de términos: un
texto en el que el nombre del documento sea un enlace subrayado que abre su ventana (RF-021), sin
asterisco.

### RF-021 Ventana del documento
Cuando la persona active el enlace de un documento, el sistema deberá abrir una ventana superpuesta
con su título y el texto completo de la versión vigente, con desplazamiento vertical dentro de la
ventana si no cabe, sin marcar ni desmarcar la casilla. Mientras la ventana esté abierta, el foco
deberá quedar dentro de ella y el resto de la pantalla no deberá poder usarse. Cuando la persona la
cierre con su botón de cerrar, con Escape o haciendo clic fuera de ella, el sistema deberá cerrarla,
conservar lo escrito en el formulario y devolver el foco al enlace.

### Estilo

### RF-022 Identidad visual
El sistema deberá aplicar a la barra superior, el indicador de pasos, los campos, los botones, las
casillas, los globos de ayuda y la ventana de documento los colores, formas, tipografía, foco
visible y contrastes de `docs/identidad-visual.md`, en el tema claro y en el oscuro.

## Supuestos
- S-01 La imagen de referencia aporta la estructura (indicador numerado unido por líneas, tarjeta
  blanca con título, campos con el nombre encima, asterisco y botón principal con flecha), no sus
  colores: el naranja está prohibido por la guía visual («el color de marca nunca es rojo, naranja
  ni amarillo»), así que lo activo usa el color de acción.
- S-02 «Desplazamiento lateral hacia la derecha» se interpreta como avance de izquierda a derecha:
  el paso nuevo entra por la derecha (RF-009), como el indicador avanza hacia la derecha.
- S-03 Las descripciones de los «?» las redacta el plan, una por campo (nombre completo, fecha de
  nacimiento, correo, país, código y contraseña), y no prometen nada que el servidor no garantice ni
  revelan si un correo tiene cuenta.
- S-04 El menú de idioma conserva el comportamiento del selector actual (RF-003…RF-005 de
  `componentes-base-accesibles`); solo cambia su forma, de grupo de botones a botón con menú.
- S-05 La pantalla de muestra de `componentes-base-accesibles` recibe la barra superior y el estilo
  nuevo de los campos porque los comparte; no recibe indicador de pasos ni «?».
- S-06 En la casilla de términos, el asterisco forma parte del texto visible pero se anuncia como
  «obligatorio», igual que en los demás campos.
- S-07 El usuario no eligió si el indicador se desliza con el contenido; se deja fijo arriba y anima
  el cambio de paso (RF-007, RF-009), porque así pidió que «pase de uno a otro».

## Fuera de alcance
- Cualquier cambio en los datos, las validaciones, los mensajes de error, los temporizadores o las
  respuestas del servidor del registro (`registro-flujo`).
- Quitar el consentimiento de marketing del registro (se mantiene, RF-020).
- Un botón «Anterior» o editar los datos del formulario ya enviados.
- La opción «Sistema» en el menú de tema.
- La barra lateral de navegación de la guía visual y cualquier pantalla que no sea del registro o
  la de muestra.
- Los enlaces de navegación de la imagen de referencia (Jobs, Properties, My Listings, etc.).

## Criterios de finalización
- CF-1 RF-001…RF-023 cubiertos por tests automatizados en verde, con cobertura de líneas ≥ 80 % en
  el código nuevo (P-05), y `typecheck`, `lint` y `format` limpios.
- CF-2 Las pruebas de accesibilidad automáticas existentes de las pantallas del registro siguen en
  verde con el diseño nuevo, en ambos temas.
- CF-3 El registro completo (formulario, verificación, contraseña y cuenta creada) se recorre solo
  con el teclado, incluidos los menús de la barra, los «?» y la ventana de documento.
- CF-4 El usuario ha revisado el registro en tema claro y oscuro, en los tres idiomas, con y sin
  movimiento reducido, y lo da por bueno frente a la imagen de referencia.
- CF-5 `docs/identidad-visual.md` recoge la barra superior, el indicador de pasos, el globo de
  ayuda, la ventana de documento y la transición entre pasos, con la aprobación del usuario.

## Historial de cambios
- 2026-11-05 — Clarificación (C-01…C-08): «Atrás» del navegador vuelve al formulario como hasta
  ahora; selector con lista propia accesible; animación propia independiente del soporte del
  navegador; título y tarjeta se deslizan, barra e indicador fijos; foco al título del paso; zona de
  mensajes reservada; «?» solo en campos de texto y selección; sin destello del otro tema al cargar
  — RF: RF-004, RF-007, RF-009, RF-011, RF-014, RF-017, RF-023 — Estado: clarificado
- 2026-11-05 — Spec aprobada por el usuario
