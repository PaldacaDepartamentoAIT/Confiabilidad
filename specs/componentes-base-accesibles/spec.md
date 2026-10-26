# Spec: componentes-base-accesibles
Estado: borrador
Aprobación: ligera

## Objetivo (por qué)
Todas las pantallas de la aplicación (registro, acceso por código, cambio de contraseña y las que
vengan) se construyen con las mismas piezas: selector de idioma, botones, campos de texto, campo del
código de 6 dígitos y mensajes de error. Esta feature entrega esas piezas antes que las pantallas,
accesibles con teclado y lector de pantalla y traducidas a español, portugués de Brasil e inglés
desde el principio, porque añadir accesibilidad y traducción al final obliga a rehacer cada pantalla.
Los textos son provisionales (coherentes con su contexto) hasta que lleguen los definitivos, y el
aspecto visual se define más adelante.

## Requisitos funcionales

### RF-001 Idiomas disponibles
El sistema deberá ofrecer la interfaz en español (`es`), portugués de Brasil (`pt-BR`) e inglés
(`en`), con todos los textos de la interfaz definidos en los tres idiomas.

### RF-002 Idioma inicial
Cuando el usuario abra la aplicación sin haber elegido antes un idioma en ese navegador, el sistema
deberá mostrar la interfaz en el primer idioma preferido del navegador que sea `es`, `pt-BR` o `en`,
tratando cualquier variante de portugués como `pt-BR`, de español como `es` y de inglés como `en`; si
ninguno coincide, deberá mostrarla en español.

### RF-003 Selector de idioma
El sistema deberá ofrecer un selector de idioma que muestre cada idioma con su nombre en ese mismo
idioma («Español», «Português (Brasil)», «English»), indique cuál está activo y se pueda usar solo
con el teclado.

### RF-004 Cambio de idioma
Cuando el usuario elija un idioma en el selector, el sistema deberá mostrar todos los textos visibles
y los nombres accesibles en ese idioma sin recargar la página, conservando los valores escritos en
los campos y el foco en el selector.

### RF-005 Idioma recordado
Cuando el usuario haya elegido un idioma en el selector, el sistema deberá usar ese idioma en las
siguientes visitas desde el mismo navegador, por encima del idioma del navegador.

### RF-006 Idioma declarado del documento
El sistema deberá declarar en el documento el idioma activo, para que el lector de pantalla
pronuncie los textos con la voz de ese idioma, y marcar el nombre de cada idioma del selector con su
propio idioma.

### RF-007 Texto de reserva
Si a un idioma le falta el texto de una clave, entonces el sistema deberá mostrar ese texto en
inglés y nunca la clave interna.

### RF-008 Traducciones completas
El sistema deberá incluir una comprobación automatizada que falle cuando los tres idiomas no tengan
exactamente las mismas claves de texto o cuando algún texto esté vacío.

### RF-009 Botón
El sistema deberá ofrecer un botón con un nombre accesible igual a su texto visible, que se active
con el ratón, con Enter y con Espacio.

### RF-010 Botón procesando
Mientras un botón esté en estado «procesando», el sistema deberá ignorar nuevas activaciones,
mantenerlo en el orden de tabulación, conservar el foco si lo tenía y comunicar al lector de
pantalla que está procesando.

### RF-011 Campos de texto
El sistema deberá ofrecer campos de texto genérico, correo electrónico y contraseña, cada uno con
una etiqueta visible asociada que sea su nombre accesible, con una indicación de obligatoriedad que
el lector de pantalla anuncie cuando el campo sea obligatorio y con el autocompletado del navegador
que corresponda a su tipo.

### RF-012 Mostrar u ocultar la contraseña
Cuando el usuario active el control de mostrar u ocultar del campo de contraseña, el sistema deberá
alternar entre mostrar el texto escrito y ocultarlo, conservar el valor, comunicar al lector de
pantalla si la contraseña está visible y dejar el foco en el control. El control deberá poder
usarse solo con el teclado.

### RF-013 Campo del código
El sistema deberá ofrecer un único campo para el código de verificación con una etiqueta visible
asociada, que acepte como máximo 6 dígitos, descarte cualquier otro carácter escrito, abra el
teclado numérico en móvil y admita el autocompletado de códigos de un solo uso del sistema
operativo.

### RF-014 Pegar el código
Cuando el usuario pegue texto en el campo del código, el sistema deberá conservar solo sus dígitos,
en orden, y quedarse con los 6 primeros.

### RF-015 Sin envío automático del código
Cuando el campo del código tenga 6 dígitos, el sistema no deberá enviar el formulario ni mover el
foco; el envío lo hace el usuario con el botón o con Enter.

### RF-016 Error de campo
Si un campo tiene un error, entonces el sistema deberá mostrar el mensaje junto al campo, marcar el
campo como no válido, asociar el mensaje al campo para que el lector de pantalla lo lea al llegar a
él y retirar ambos cuando el error desaparezca.

### RF-017 Error general
Si se produce un error que no pertenece a un campo concreto (por ejemplo, demasiados intentos o un
fallo del servidor), entonces el sistema deberá mostrar un mensaje general del formulario, llevar
el foco a ese mensaje y permitir que el lector de pantalla lo lea.

### RF-018 Errores en el idioma activo
Cuando el usuario cambie de idioma mientras se muestra un mensaje de error, el sistema deberá
mostrar ese mensaje en el nuevo idioma sin perder el estado de error.

### RF-019 Uso solo con teclado
El sistema deberá permitir recorrer y usar todos los componentes solo con el teclado, en un orden de
tabulación igual al orden visual, con un indicador de foco visible y sin trampas de foco.

### RF-020 Página de muestra
El sistema deberá mostrar una página de muestra con el selector de idioma y un formulario de
ejemplo que contenga un campo de texto, uno de correo, uno de contraseña, el campo del código y un
botón de envío, para probar los componentes a mano con teclado y lector de pantalla.

### RF-021 Validación de la página de muestra
Cuando el usuario envíe el formulario de ejemplo con un campo obligatorio vacío, un correo con un
formato no válido o un código de menos de 6 dígitos, el sistema deberá mostrar el error de cada
campo afectado y llevar el foco al primer campo con error.

### RF-022 Simulación de envío en la página de muestra
Cuando el usuario envíe el formulario de ejemplo sin errores de campo, el sistema deberá poner el
botón en estado «procesando» durante un momento y después mostrar un mensaje general que diga que
el formulario es de demostración y no envía datos. La página deberá ofrecer además un control para
mostrar un error general de ejemplo.

## Supuestos
- S-01 Los textos provisionales describen el contexto real en el que se usarán (cuenta de usuario
  de una herramienta de gestión de activos industriales: correo, contraseña, código de
  verificación, enviar, reenviar código, errores de intentos y de servidor), redactados en los tres
  idiomas. Sustituirlos por los definitivos consiste en editar los archivos de traducción, sin
  tocar los componentes.
- S-02 El idioma por defecto es el español, alineado con el backend (RF-012 de
  `correo-asincrono-plantillas`); el inglés se usa solo como texto de reserva de una clave que
  falte (RF-007), a petición del usuario.
- S-03 «Recordado» significa guardado en el navegador del usuario; no se guarda en la cuenta ni se
  envía al backend en esta feature.
- S-04 Si el navegador no permite guardar el idioma elegido (por ejemplo, en modo privado
  estricto), el selector sigue funcionando durante la visita y la siguiente visita vuelve a
  aplicar RF-002.
- S-05 El indicador de foco visible puede ser el del navegador mientras no se defina el estilo.
- S-06 La página de muestra sustituye a la página de inicio actual y se retirará o se moverá cuando
  lleguen las pantallas reales; no existe ninguna pantalla que dependa de ella.
- S-07 La aplicación de escritorio carga la misma interfaz web, así que hereda los componentes y la
  detección de idioma (con el idioma del sistema operativo como idioma preferido), sin trabajo
  propio.
- S-08 La prueba con lector de pantalla real (NVDA en Windows o VoiceOver en macOS) es manual: su
  checklist va en `resumen.md` y la acción, en `specs/componentes-base-accesibles/HUMAN_TODO.md`.

## Fuera de alcance
- El estilo visual (colores, tipografía, espaciados, aspecto de casillas del código).
- Las pantallas reales y su conexión con la API (incluido el envío del idioma al backend).
- Guardar el idioma en la cuenta del usuario.
- Más idiomas, escritura de derecha a izquierda y formato de fechas o números según el idioma.
- El envío automático al completar el código y el código en 6 casillas separadas.
- El resumen de errores con enlaces a cada campo.
- Otros componentes (casillas de verificación, listas desplegables de datos, diálogos, tablas).

## Criterios de finalización
- CF-1 RF-001…RF-022 cubiertos por tests automatizados en verde, con cobertura de líneas ≥ 80 %
  en el código nuevo (P-05), y `typecheck`, `lint` y `format` limpios.
- CF-2 La comprobación de RF-008 forma parte de la suite y pasa con los textos entregados.
- CF-3 La página de muestra se recorre y se usa entera solo con el teclado.
- CF-4 La página de muestra se ve en español, portugués de Brasil e inglés cambiando el selector,
  incluidos los mensajes de error.
- CF-5 El checklist de lector de pantalla de `resumen.md` se ha completado con NVDA o VoiceOver
  sobre la página de muestra y la acción de `HUMAN_TODO.md` está marcada.

## Historial de cambios
- 2026-10-26 — Creación (feature nueva) — RF: RF-001…RF-022 — Estado: pendiente de clarificar
