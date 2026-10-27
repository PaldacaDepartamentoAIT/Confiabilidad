# Resumen — componentes-base-accesibles
Estado: entregas completas, pendiente de validación · Última actualización: 2026-10-27

## Qué se hizo
Los componentes comunes de las futuras pantallas del frontend, accesibles desde el principio y
traducidos a español, portugués de Brasil e inglés, sin estilo todavía. Se prueban en una página de
muestra que sustituye a la página de inicio (S-06). Las pantallas reales y su conexión con la API
quedan fuera (ver «Fuera de alcance» en [`spec.md`](spec.md)).

- **Traducción** (`frontend/src/i18n/`): `i18next` con los textos de los tres idiomas en archivos
  de TypeScript. Una clave que no existe no compila, un test falla si a un idioma le falta una
  clave o tiene un texto vacío, y un texto que faltara se vería en inglés, nunca como clave.
- **Idioma inicial y selector**: la primera visita usa el idioma preferido del navegador si es uno
  de los tres y, si no, el inglés. El selector es un grupo de tres botones, cada uno con su nombre
  en su propio idioma; el elegido se recuerda en el navegador y cambia también el `lang` de la
  página y el título de la pestaña. Un valor guardado que no sea válido se borra.
- **Campos de texto y correo**: etiqueta visible, asterisco para los obligatorios con una leyenda
  que lo explica, ayuda y error asociados al campo para que el lector los lea al llegar a él.
- **Contraseña**: cada uso indica si es la actual o una nueva, y así el navegador ofrece la
  guardada o propone una nueva. El control «Mostrar contraseña» nombra su campo, dice si está
  activado y no saca la contraseña a los correctores ortográficos. La contraseña nueva muestra sus
  reglas (al menos 12 caracteres, no solo números), las mismas que comprueba el servidor.
- **Código de verificación**: un solo campo de 6 dígitos que convierte los dígitos de otros
  sistemas de escritura (por ejemplo, `١٢٣`) en `0-9`, se queda con los dígitos de un texto pegado y
  no envía nada solo.
- **Botón**: es de tipo `button` salvo que se diga otra cosa y tiene un estado «procesando» que
  cambia su texto, ignora nuevos clics sin perder el foco y lo anuncia al lector.
- **Mensajes generales**: error, éxito o información, con un prefijo visible («Error:»,
  «Éxito:», «Información:») que dice su tipo al lector.
- **Validación del formulario** (`frontend/src/forms/useFormValidation.ts`): valida cada campo al
  salir de él y todos al enviar, y lleva el foco al primer campo con error. Acepta la respuesta del
  servidor con `showResult`: errores por campo, que duran hasta el siguiente envío y ceden ante un
  error local nuevo, y un mensaje general que recibe el foco o, si también hay errores de campo, se
  anuncia sin mover el foco.
- **Página de muestra**: un formulario con nombre, correo, contraseña actual, contraseña nueva y
  código. Un envío válido pone «Verificar» en «Procesando…» 3 segundos y muestra un mensaje de
  demostración; el botón «Mostrar error general de ejemplo» muestra el error de demasiados intentos.

Cada entrega tiene su propio resumen en [`entregas/`](entregas/), con sus tareas y su PR.

### Límites conocidos
- No hay estilo: el foco visible es el del navegador (S-05).
- Las reglas de la contraseña nueva copian a mano las del servidor (S-11): si el servidor las
  cambia, hay que cambiarlas también aquí.
- El servidor sigue usando el español por defecto; las pantallas que llamen a la API tendrán que
  enviarle el idioma elegido (S-02).
- La prueba con un lector de pantalla real es manual y está pendiente (ver más abajo y
  [`HUMAN_TODO.md`](HUMAN_TODO.md)).
- El arranque con Docker no se pudo comprobar en el entorno remoto, que no tiene salida a internet
  (también en [`HUMAN_TODO.md`](HUMAN_TODO.md)).

## Cómo probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 185 tests en verde.

Para ver además la cobertura:
```bash
pnpm --filter frontend test:coverage
```
Deberías ver la fila «All files» por encima del 99 % de líneas.

Arranca la página de muestra:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173.

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173.

### Idiomas (CF-4)
1. Abre la página en una ventana privada. Deberías verla en el idioma de tu navegador si es español,
   portugués o inglés y, si no, en inglés.
2. Pulsa «Português (Brasil)» y después «English». Deberías ver todos los textos en ese idioma, y el
   título de la pestaña también.
3. Deja el correo con `a@` y sal del campo, pulsa «Mostrar error general de ejemplo» y cambia de
   idioma. Deberías ver el error del correo y el mensaje general traducidos, sin perderse.
4. Recarga la página. Deberías verla en el último idioma elegido.

### Checklist de teclado (CF-3)
Sin tocar el ratón. Completado por el usuario el 2026-10-27:
- [x] Tab recorre, en este orden: los tres botones de idioma, «Nombre completo», «Correo
  electrónico», «Contraseña», su «Mostrar contraseña», «Nueva contraseña», su «Mostrar
  contraseña», «Código de verificación», «Verificar» y «Mostrar error general de ejemplo».
  Mayús+Tab lo recorre al revés y en ningún punto el foco se queda atrapado.
- [x] Enter o Espacio sobre un botón de idioma cambia el idioma, y el foco sigue en ese botón.
- [x] Al salir de un campo obligatorio vacío aparece «Completa este campo.»; al corregirlo y salir,
  el error desaparece.
- [x] Pasar con Tab de «Contraseña» a su «Mostrar contraseña» y volver no muestra error; salir de
  los dos con la contraseña vacía, sí.
- [x] Espacio sobre «Mostrar contraseña» deja ver la contraseña, y otra vez la oculta.
- [x] En el código, escribir letras no hace nada; pegar `Tu código: 12 34 56` deja `123456`.
- [x] Enter desde cualquier campo con errores envía y lleva el foco al primer campo con error.
- [x] Con todo válido (por ejemplo, la nueva contraseña `turbina-compresor-7` y el código `123456`),
  Enter sobre «Verificar» lo pone en «Procesando…» con el foco en él; Enter otra vez no hace nada;
  a los 3 segundos aparece el mensaje de demostración con el foco.
- [x] Enter sobre «Mostrar error general de ejemplo» muestra el error con el foco en él.

### Checklist de lector de pantalla (CF-5)
Con NVDA en Windows (Firefox o Chrome) o VoiceOver en macOS (Safari), recorriendo con Tab:
- [ ] Al cargar, el lector dice el título de la página («Confiabilidad — Componentes» en español).
- [ ] El selector se anuncia como el grupo «Idioma», y el botón del idioma activo, como pulsado.
- [ ] Cada botón de idioma se pronuncia con la voz de su idioma («English» con voz inglesa).
- [ ] Cada campo obligatorio se anuncia con su etiqueta y como obligatorio, sin leer el asterisco.
- [ ] «Nueva contraseña» lee también su ayuda: «Al menos 12 caracteres, no solo números.».
- [ ] Los dos «Mostrar contraseña» se distinguen por su campo y dicen si están pulsados.
- [ ] Al volver a un campo con error, el lector lo anuncia como no válido y lee el error.
- [ ] Al enviar con errores, el lector anuncia el primer campo con error con su mensaje.
- [ ] Al enviar con todo válido, el lector dice «Procesando» y, a los 3 segundos, «Información:
  Formulario de demostración: no se envían datos.».
- [ ] «Mostrar error general de ejemplo» hace que el lector lea «Error: Demasiados intentos. Espera
  unos minutos y vuelve a intentarlo.».
- [ ] Al cambiar de idioma, el lector lee la página con la voz del idioma nuevo.

Cuando lo completes, marca la acción correspondiente en [`HUMAN_TODO.md`](HUMAN_TODO.md).

## Marco teórico
### Autocompletado de la contraseña actual y de la nueva
El navegador no sabe, solo con `type="password"`, si el campo pide la contraseña que ya tienes o una
nueva. El atributo `autocomplete` se lo dice: con `current-password` ofrece la guardada para ese
sitio; con `new-password` propone una nueva y segura y no rellena la vieja. Por eso cada uso del
campo debe decir cuál es: un error ahí hace que el gestor de contraseñas rellene algo equivocado.

### Cuándo se valida un campo
Validar al salir del campo avisa pronto, antes de enviar; validar al enviar revisa todo de una vez.
Esta feature hace las dos cosas desde el principio. Hay comprobaciones que solo puede hacer el
servidor (por ejemplo, si un correo ya está registrado): esas se hacen al enviar, y su error se
mantiene hasta el siguiente envío. Si mientras tanto el usuario cambia el valor y aparece un error
local, se ve el local, porque describe lo que hay escrito ahora.

### Contraseña y su botón como un solo campo
Si salir de la contraseña hacia su propio botón «Mostrar contraseña» contara como salir del campo,
quien usa teclado vería «Completa este campo.» solo por ir a mostrarla. Por eso el campo y su botón
cuentan como uno: el error aparece al dejar atrás los dos.

### El clic que se pierde
Un clic es «pulsar y soltar sobre el mismo elemento». Al pulsar un botón, el campo pierde el foco y
su error puede desaparecer; si eso sube el botón antes de soltar, el navegador no cuenta el clic.
Los botones bajo los campos evitan que el campo pierda el foco al pulsarlos, así nada se mueve.

### `aria-disabled` frente a `disabled`
Un botón con `disabled` sale del orden de Tab y, si tenía el foco, lo pierde: quien usa teclado o
lector no sabe dónde está. Con `aria-disabled` el lector lo anuncia como no disponible, pero sigue
enfocable; el propio botón ignora los clics mientras procesa.

### Regiones vivas (`aria-live`)
Son zonas de la página cuyo cambio de texto el lector anuncia aunque el foco esté en otro sitio. Una
región «educada» espera a que el lector termine de hablar y una «urgente» lo interrumpe: los avisos
informativos van por la educada y los errores, por la urgente. La región tiene que existir antes del
cambio y, para repetir el mismo aviso, hay que vaciarla antes de volver a escribirlo.

### El tipo del mensaje, dicho con palabras
El color o un icono no le dicen nada al lector de pantalla. Por eso cada mensaje general empieza con
su tipo escrito («Error:», «Éxito:», «Información:»), traducido como el resto del texto.

### Textos que no se quedan sin traducir
Con tres idiomas, es fácil añadir un texto en uno y olvidarlo en otro. Dos defensas lo impiden: el
compilador rechaza una clave que no existe, y un test compara las claves de los tres idiomas y
falla si falta alguna o está vacía. Si aun así faltara, se vería el texto en inglés.
