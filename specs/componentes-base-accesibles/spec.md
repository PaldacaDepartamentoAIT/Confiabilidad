# Spec: componentes-base-accesibles
Estado: aprobada
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
Cuando el usuario abra la aplicación sin una elección de idioma válida guardada en ese navegador, el
sistema deberá mostrar la interfaz en el primer idioma preferido del navegador que sea `es`, `pt-BR` o `en`,
tratando cualquier variante de portugués como `pt-BR`, de español como `es` y de inglés como `en`; si
ninguno coincide, deberá mostrarla en inglés.

### RF-003 Selector de idioma
El sistema deberá ofrecer un selector de idioma que muestre cada idioma con su nombre en ese mismo
idioma («Español», «Português (Brasil)», «English»), indique cuál está activo y se pueda usar solo
con el teclado.

### RF-004 Cambio de idioma
Cuando el usuario elija un idioma en el selector, el sistema deberá mostrar todos los textos visibles,
los nombres accesibles y el título del documento en ese idioma sin recargar la página, conservando los valores escritos en
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
El sistema deberá incluir una comprobación automatizada, que se ejecute antes de poner en marcha la
aplicación, que falle cuando los tres idiomas no tengan exactamente las mismas claves de texto,
cuando algún texto esté vacío o cuando el código use una clave que no exista.

### RF-009 Botón
El sistema deberá ofrecer un botón con un nombre accesible igual a su texto visible, que se active
con el ratón, con Enter y con Espacio.

### RF-010 Botón procesando
Mientras un botón esté en estado «procesando», el sistema deberá mostrar como texto visible, y por
tanto como nombre accesible, «Procesando…» en el idioma activo, ignorar nuevas activaciones,
mantenerlo en el orden de tabulación y conservar el foco si lo tenía. Cuando el botón entre en ese
estado, el sistema deberá anunciar «procesando» al lector de pantalla sin mover el foco; al salir de
él, el botón deberá recuperar su texto sin ningún anuncio adicional.

### RF-011 Campos de texto
El sistema deberá ofrecer campos de texto genérico, correo electrónico y contraseña, cada uno con
una etiqueta visible asociada que sea su nombre accesible y con el autocompletado del navegador que
corresponda a su tipo. Cuando un campo sea obligatorio, su etiqueta deberá llevar la marca visible
«*», el formulario deberá explicar ese símbolo con un texto visible y el lector de pantalla deberá
anunciar el campo como obligatorio.

### RF-012 Mostrar u ocultar la contraseña
Cuando el usuario active el control de mostrar u ocultar del campo de contraseña, el sistema deberá
alternar entre mostrar el texto escrito y ocultarlo, conservar el valor, comunicar al lector de
pantalla si la contraseña está visible y dejar el foco en el control. El control deberá poder
usarse solo con el teclado. Su nombre accesible deberá contener su texto visible seguido de la
etiqueta de su campo (por ejemplo, «Mostrar contraseña (Nueva contraseña)»), para distinguirlo
cuando haya varios en la página.

### RF-013 Campo del código
El sistema deberá ofrecer un único campo para el código de verificación con una etiqueta visible
asociada, que acepte como máximo 6 dígitos, convierta a `0`-`9` los dígitos de ancho completo
(`０`-`９`) y los arábigos (`٠`-`٩`), descarte cualquier otro carácter escrito, abra el
teclado numérico en móvil y admita el autocompletado de códigos de un solo uso del sistema
operativo.

### RF-014 Pegar el código
Cuando el usuario pegue texto en el campo del código, el sistema deberá sustituir todo el contenido
del campo, sea cual sea la posición del cursor o la selección, por los dígitos del texto pegado
(convertidos según RF-013), en orden, quedándose con los 6 primeros. Si el texto pegado no contiene
ningún dígito, el campo no deberá cambiar.

### RF-015 Sin envío automático del código
Cuando el campo del código tenga 6 dígitos, el sistema no deberá enviar el formulario ni mover el
foco; el envío lo hace el usuario con el botón o con Enter.

### RF-016 Error de campo
Si un campo tiene un error, entonces el sistema deberá mostrar el mensaje junto al campo, marcar el
campo como no válido, asociar el mensaje al campo para que el lector de pantalla lo lea al llegar a
él y retirar ambos cuando una nueva validación del campo (RF-025) no encuentre error.

### RF-017 Mensaje general
Si se produce un error que no pertenece a un campo concreto (por ejemplo, demasiados intentos o un
fallo del servidor), o hay que comunicar un éxito o una información general, entonces el sistema
deberá mostrar un mensaje general del formulario que indique al lector de pantalla si es un error,
un éxito o una información, llevar el foco a ese mensaje y permitir que el lector lo lea. Si a la
vez hay errores de campo, entonces el foco deberá ir al primer campo con error y el mensaje general
deberá anunciarse al lector sin mover el foco. El mensaje general deberá retirarse en el siguiente
envío del formulario.

### RF-018 Errores en el idioma activo
Cuando el usuario cambie de idioma mientras se muestra un mensaje de error de campo o un mensaje
general, el sistema deberá mostrar ese mensaje en el nuevo idioma sin perder el estado.

### RF-019 Uso solo con teclado
El sistema deberá permitir recorrer y usar todos los componentes solo con el teclado, en un orden de
tabulación igual al orden visual, con un indicador de foco visible y sin trampas de foco.

### RF-020 Página de muestra
El sistema deberá mostrar una página de muestra con el selector de idioma y un formulario de
ejemplo que contenga un campo de texto, uno de correo, uno de contraseña actual, uno de contraseña
nueva, el campo del código y un botón de envío, para probar los componentes a mano con teclado y lector de pantalla.

### RF-021 Validación de la página de muestra
Cuando el usuario envíe el formulario de ejemplo con algún campo vacío (los cinco son obligatorios),
un correo que no tenga exactamente una `@` con algún carácter antes y después o que contenga
espacios, una contraseña nueva que no cumpla RF-026 o un código de menos de 6 dígitos, el sistema deberá mostrar el error de cada campo
afectado y llevar el foco al primer campo con error. Las mismas reglas se aplican al salir de cada
campo (RF-025).

### RF-022 Simulación de envío en la página de muestra
Cuando el usuario envíe el formulario de ejemplo sin errores de campo, el sistema deberá poner el
botón en estado «procesando» durante 3 segundos y después mostrar un mensaje general que diga que
el formulario es de demostración y no envía datos. La página deberá ofrecer además un control para
mostrar un error general de ejemplo.

### RF-023 Idioma guardado no válido
Si el idioma guardado en el navegador no es `es`, `pt-BR` ni `en`, entonces el sistema deberá
ignorarlo, borrarlo y aplicar RF-002.

### RF-024 Tipo de contraseña
El sistema deberá exigir que cada uso del campo de contraseña indique si es la contraseña actual o
una nueva, y deberá pedir al navegador el autocompletado de contraseña actual o de contraseña nueva
según esa indicación.

### RF-025 Momento de la validación
Cuando el usuario salga de un campo, aunque aún no haya enviado el formulario, o cuando envíe el
formulario, el sistema deberá validar ese campo (todos, al enviar) y mostrar o retirar su error
según el resultado. El campo de contraseña y su control de mostrar u ocultar cuentan como un solo
campo: pasar el foco del uno al otro no es salir del campo, y salir de los dos sí lo es. Las
comprobaciones que dependen de datos del servidor (por ejemplo, si un correo ya está registrado)
solo deberán hacerse al enviar, y su error deberá mantenerse hasta el siguiente envío.

### RF-026 Reglas de la contraseña nueva
Cuando el usuario salga de un campo de contraseña nueva o envíe su formulario, el sistema deberá
mostrar un error si la contraseña tiene menos de 12 caracteres, contados como el servidor (por punto
de código), o si está formada solo por dígitos de cualquier sistema de escritura. El resto de la
política de contraseñas (parecido al correo o al nombre, contraseñas comunes y filtradas; RF-022 de
`procesos-pendientes`) la comprueba solo el servidor, al enviar. Un campo de contraseña actual no
aplica estas reglas.

### RF-027 Ayuda de la contraseña nueva
El sistema deberá mostrar bajo cada campo de contraseña nueva un texto de ayuda visible con sus
reglas, asociado al campo para que el lector de pantalla lo lea al llegar a él, también cuando el
campo tenga un error.

## Supuestos
- S-01 Los textos provisionales describen el contexto real en el que se usarán (cuenta de usuario
  de una herramienta de gestión de activos industriales: correo, contraseña, código de
  verificación, enviar, reenviar código, errores de intentos y de servidor), redactados en los tres
  idiomas. Sustituirlos por los definitivos consiste en editar los archivos de traducción, sin
  tocar los componentes.
- S-02 Cuando el navegador no prefiere ninguno de los tres idiomas, la interfaz usa el inglés
  (C-13), que es también el texto de reserva de RF-007. El backend mantiene el español por defecto
  (RF-012 de `correo-asincrono-plantillas`). Las pantallas que llamen a la API deberán enviar
  siempre el idioma activo de forma explícita (fuera del alcance de esta feature), porque el
  backend lee el idioma del navegador y no el elegido en el selector.
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
- S-09 La página de muestra tiene un campo de contraseña actual, sin reglas, y otro de contraseña
  nueva, con las de RF-026.
- S-10 Validar al salir desde el principio hace que recorrer con Tab un formulario vacío muestre el
  error de cada campo obligatorio que se deja atrás; el usuario acepta ese coste.
- S-11 Las reglas de RF-026 copian a mano las del servidor (`MinimumLengthValidator` con 12 y
  `NumericPasswordValidator` en `AUTH_PASSWORD_VALIDATORS`), porque backend y frontend no comparten
  código (P-08). Si el servidor las cambia, hay que cambiarlas también aquí; mientras no se haga, el
  servidor sigue siendo quien decide al enviar.

## Fuera de alcance
- El estilo visual (colores, tipografía, espaciados, aspecto de casillas del código).
- Las pantallas reales y su conexión con la API (incluido el envío del idioma al backend).
- Guardar el idioma en la cuenta del usuario.
- Más idiomas, escritura de derecha a izquierda y formato de fechas o números según el idioma.
- El envío automático al completar el código y el código en 6 casillas separadas.
- El resumen de errores con enlaces a cada campo.
- Otros componentes (casillas de verificación, listas desplegables de datos, diálogos, tablas).

## Criterios de finalización
- CF-1 RF-001…RF-027 cubiertos por tests automatizados en verde, con cobertura de líneas ≥ 80 %
  en el código nuevo (P-05), y `typecheck`, `lint` y `format` limpios.
- CF-2 La comprobación de RF-008 forma parte de la suite y pasa con los textos entregados.
- CF-3 La página de muestra se recorre y se usa entera solo con el teclado.
- CF-4 La página de muestra se ve en español, portugués de Brasil e inglés cambiando el selector,
  incluidos los mensajes de error.
- CF-5 El checklist de lector de pantalla de `resumen.md` se ha completado con NVDA o VoiceOver
  sobre la página de muestra y la acción de `HUMAN_TODO.md` está marcada.

## Historial de cambios
- 2026-10-26 — Creación (feature nueva) — RF: RF-001…RF-022 — Estado: pendiente de clarificar
- 2026-10-26 — Clarificación (C-01…C-13) — RF: RF-002, RF-004, RF-008, RF-010, RF-011, RF-013,
  RF-014, RF-016, RF-017, RF-018, RF-021 y RF-022 ajustados; RF-023, RF-024 y RF-025 añadidos; S-02
  ajustado; S-09 y S-10 añadidos — Estado: clarificado
- 2026-10-26 — S-02 ajustado: el backend mantiene el español por defecto; se descarta el
  `sdd-cambio` del backend por su poco beneficio — Estado: clarificado
- 2026-10-26 — Aprobación por el usuario — Estado: aprobada
- 2026-10-27 — Cambio: la contraseña y su control de mostrar u ocultar cuentan como un solo campo al
  validar al salir — RF: RF-025 — Estado: pendiente de clarificar
- 2026-10-27 — Clarificación (C-14): salir de los dos sí valida la contraseña — RF: RF-025 —
  Estado: clarificado
- 2026-10-27 — Impacto analizado: plan (M-07, D-16) y tarea nueva T-033 en E-06; aprobado por el
  usuario — RF: RF-025 — Estado: impacto analizado
- 2026-10-27 — Cambio: reglas y ayuda de la contraseña nueva — RF: RF-020, RF-021, RF-026 y RF-027
  — Estado: pendiente de clarificar
- 2026-10-27 — Clarificación (C-15, C-16): longitud por punto de código y dígitos de cualquier
  sistema, como el servidor — Estado: clarificado
- 2026-10-27 — Impacto analizado: plan (M-02, M-07, M-11, M-12, D-18) y entrega nueva E-10
  (T-035…T-039); aprobado por el usuario — Estado: impacto analizado
- 2026-10-27 — Cambio: el control de mostrar u ocultar nombra su campo, porque la página tiene dos
  — RF: RF-012 — Estado: pendiente de clarificar
- 2026-10-27 — Clarificación: el nombre accesible contiene el texto visible (WCAG 2.5.3) — RF:
  RF-012 — Estado: clarificado
- 2026-10-27 — Impacto analizado: plan (D-10) y tarea nueva T-040 en E-10; pedido por el usuario
  (opción A) — RF: RF-012 — Estado: impacto analizado
- 2026-10-28 — Validación: cerrada con riesgo residual aceptado. Riesgos aceptados: (1) RF-006:
  con NVDA + Chrome, al recorrer con Tab, los nombres de los campos y de los controles de mostrar
  contraseña se leen con la voz por defecto del lector y no con la del idioma activo, también al
  recargar; `<html lang>` es correcto y el test solo comprueba el atributo; causa sin confirmar
  (probable limitación de NVDA en modo foco); (2) RF-026: una contraseña solo de superíndices pasa
  en el navegador y la rechaza el servidor (S-11); (3) P-02: el arranque del contenedor `frontend`
  queda pendiente de verificar en local (`HUMAN_TODO.md`). RF-001…RF-027 verificados con evidencia
  (suite 185/185, cobertura 99,76 %); CF-3 y CF-5 recorridos por el usuario — RF: RF-006, RF-026
- 2026-10-28 — Riesgo residual (3) resuelto: el usuario comprobó en local que el contenedor
  `frontend` arranca — RF: — — Estado: cerrado
- 2026-10-28 — Corrección de redacción: RF-021 decía «los seis son obligatorios» y el formulario
  tiene cinco campos; sin cambio de comportamiento (los cinco ya eran obligatorios y así lo prueban
  los tests). Impacto: ninguno en plan, tareas ni tests; pedido por el usuario — RF: RF-021 —
  Estado: impacto analizado
