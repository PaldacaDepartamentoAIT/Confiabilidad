# Resumen: presentacion-registro

Estado: validada con riesgo residual aceptado (13-nov-2026). Depende de `sistema-de-diseno` y de
`casilla-con-documento`: su PR a `main` no puede fusionarse antes que los de esas dos features.

## Qué se hizo
- **Botones de la verificación en una fila.** «Enviar otro código» (secundario) a la izquierda y «Verificar»
  (principal) a la derecha, pegados al borde derecho y con 10 px entre ellos. Por debajo de 480 px pasan a dos
  filas a todo el ancho, con «Verificar» arriba.
- **Aspecto de botón bloqueado.** Cualquier botón bloqueado (desactivado o procesando) se ve al 60 % de opacidad,
  con el cursor de acción no permitida y sin cambiar de color al pasar el puntero. El catálogo muestra los dos
  botones bloqueados.
- **Hueco para el mensaje de reenvío.** Debajo del recuento de códigos hay siempre un hueco de dos líneas, de modo
  que el mensaje de reenvío aparece y desaparece sin mover la card.
- **Sin cards vacías al cargar.** El registro y la verificación no pintan la card ni su título hasta que llega la
  respuesta del servidor; entonces la card entra con un fundido de 0,2 s. Si la carga falla o pasan 10 s sin
  respuesta, aparece la card con el error de conexión, y una respuesta posterior se ignora. El enlace no válido y
  la cuenta creada entran con el fundido de su card, y el cambio del código a la contraseña también.
- **Movimiento reducido.** Con «reducir movimiento» no hay ningún fundido.
- **Barra superior fija.** `App` pinta una sola barra para todo el registro: al cambiar de pantalla es el mismo
  nodo y no se repinta ni se anima. El catálogo conserva la suya.
- **Corrección durante el trabajo.** Al compartir la barra, el orden de carga del CSS hizo que el secundario
  bloqueado cambiara de fondo al pasar el puntero; se corrigió con una regla más específica (T-014).
- **Pruebas.** 838 tests unitarios (cobertura de líneas 99,92 %) y 74 pruebas en Chromium (34 del registro), en
  claro y oscuro. La guía (`docs/identidad-visual.md`) recoge las acciones de un formulario, el hueco de
  mensajes y el fundido.

El flujo, los textos, las validaciones y los datos enviados del registro no cambian.

## Entregas
E-01 botón desactivado, E-02 verificación, E-02b prueba de la verificación, E-03 registro con carga, E-03b
verificación con carga, E-04 barra compartida, E-04b prueba de carga, fundido y barra. Cada una tiene su resumen
en `specs/presentacion-registro/entregas/`.

## Cómo probarlo
Desde la raíz del repositorio, instala las dependencias:

```bash
pnpm install
```

Ejecuta los tests del frontend:

```bash
pnpm --filter frontend test
```

Deberías ver 838 tests en verde.

Ejecuta las pruebas en un navegador real (la primera vez, descarga Chromium):

```bash
pnpm --filter frontend exec playwright install chromium
```

```bash
pnpm --filter frontend test:visual
```

Deberías ver 74 pruebas en verde.

Levanta la aplicación:

```bash
pnpm --filter frontend dev
```

- Abre http://localhost:5173/ y, en la sección de botones, comprueba los dos botones bloqueados: atenuados y sin
  cambio de color al pasar el puntero.
- Con el backend levantado, abre `/register/continue#<PUBLIC_ID>` (el identificador sale del enlace del correo de
  verificación): los dos botones van en una fila; pulsa «Enviar otro código» y el mensaje aparece sin mover la
  card. Reduce la ventana por debajo de 480 px: los botones pasan a dos filas, con «Verificar» arriba.
- Para ver la carga, abre `/register` con la conexión normal y, en las herramientas de desarrollo, «Bloqueo de
  solicitudes de red» (menú ⋮, «Más herramientas»): bloquea `*registration/options*` y recarga. Verás la barra
  superior sin card y, enseguida, la card con el error de conexión. No uses «Offline» antes de recargar: corta la
  carga de la propia página.

## Riesgo residual aceptado
La validación (13-nov-2026) dio los 9 requisitos cumplidos y el usuario aceptó cerrar con estos riesgos, todos de
impacto bajo:
1. **Fundido sin medir en Chromium** en la cuenta creada, el enlace no válido y el cambio código→contraseña, ni el
   movimiento reducido en ese último; solo tienen prueba estructural en jsdom. El CSS es compartido con la card
   del registro y la verificación, que sí se miden.
2. **Hueco del mensaje de reenvío** probado en Chromium solo con el mensaje informativo, no con el de error, el
   de espera ni con más de dos líneas. Si un margen excediera el hueco, la card saltaría.
3. **Botón bloqueado** medido en Chromium solo para el secundario por `disabled`; `aria-disabled` y el principal
   se comprueban leyendo el CSS.
4. **Idioma y tema entre pantallas**: la barra es el mismo nodo (probado), pero no hay una aserción propia de que
   se conserven al navegar.
5. **Ajeno a la feature:** `prettier --check .` falla por `frontend/eslint.config.js` y por archivos de `specs/` de
   otras features; conviene tratarlo en una rama `chore/` aparte.

## Marco teórico
- **Fundido (fade).** Una animación CSS que cambia la opacidad de 0 a 1 en 0,2 s. Se aplica a la card cuando se
  pinta, para que no aparezca de golpe, y a un contenido que cambia de paso, remontándolo con otra clave.
- **Por qué no se pinta la card mientras carga.** Una card vacía que luego se rellena hace saltar el diseño y
  parece un fallo. Es mejor esperar y mostrarla entera; si tarda demasiado, se muestra con un error.
- **Respuesta tardía.** Si el plazo ya dio la carga por fallida y luego llega la respuesta, se ignora; si no, la
  pantalla cambiaría sola de error a contenido sin que la persona lo espere.
- **Movimiento reducido.** Una preferencia del sistema operativo de quien se marea con las animaciones. Una sola
  regla global (`prefers-reduced-motion`) anula todas las animaciones y transiciones de la aplicación.
- **Orden y especificidad del CSS.** Si dos reglas con la misma especificidad chocan, gana la que se carga
  después, y ese orden depende de qué archivo se importa antes. Por eso una regla que debe ganar siempre (el
  secundario bloqueado sin hover) lleva más especificidad en vez de confiar en el orden.
- **Una barra que no se repinta.** En React, un componente conserva su nodo mientras esté en la misma posición del
  árbol. Al subir la barra a `App`, cambiar de pantalla solo cambia su contenido y la barra sigue siendo el mismo
  elemento.
