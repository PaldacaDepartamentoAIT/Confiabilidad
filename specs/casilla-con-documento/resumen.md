# Resumen: casilla-con-documento

Estado: validada con riesgo residual aceptado (13-nov-2026). Depende de `sistema-de-diseno`: su PR a `main` no
puede fusionarse antes que el de aquella feature.

## Qué se hizo
- **Casilla con enlace al documento** (`DocumentCheckbox`, reutilizable). El texto de la casilla es un enlace que
  abre el documento en un modal; pulsar el cuadro marca la casilla sin abrir nada; pulsar otra parte de la fila no
  hace nada. Sin documento, es una casilla normal. Admite obligatoria, ayuda y error, con la reserva de espacio de
  los demás campos.
- **Modal de documento** (`DocumentModal`). Un `<dialog>` nativo con una cortina negra al 50 % y una caja negra
  de 640 px como máximo: la «×» arriba, el documento en Markdown con desplazamiento y, abajo, una casilla con el
  mismo texto. Se cierra con la «×», Escape o un clic en la cortina y devuelve el foco al enlace. La página de
  detrás no se desplaza y el foco no sale del modal. Los enlaces del documento se abren en una pestaña nueva y
  son azul grisáceo, sin subrayado.
- **Las dos casillas comparten estado.** Marcar en el modal marca la de fuera y viceversa; el modal sigue abierto.
  La casilla del modal está fuera del formulario y no tiene nombre, así que no entra en los datos. Un error de la
  casilla de fuera se mantiene mientras el modal está abierto y se revalida al cerrarlo.
- **Registro.** Los términos (obligatoria) y el marketing (opcional, si hay documento) usan la casilla, una
  encima de la otra, en lugar de los desplegables; el flujo, las validaciones y los datos enviados no cambian. El
  formulario completo cabe sin desplazamiento a 1000 px de ancho. Se retiraron los textos de los desplegables.
- **Catálogo y guía.** El catálogo muestra el modal de ejemplo y la casilla en sus cuatro casos; la guía
  (`docs/identidad-visual.md`) tiene la sección «Modal de documento».
- **Pruebas.** 786 tests unitarios (cobertura de líneas 99,9 %) y 40 pruebas en Chromium (26 del modal), en claro
  y oscuro. Una de ellas detectó un defecto real (el foco no volvía al cerrar), ya corregido.

## Cómo probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 61 archivos de test en verde (786 tests).

Ejecuta las pruebas en un navegador real (la primera vez, descarga Chromium):
```bash
pnpm --filter frontend exec playwright install chromium
```

```bash
pnpm --filter frontend test:visual
```
Deberías ver 40 pruebas en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
- Abre http://localhost:5173/ y baja hasta «Casillas con documento»: pulsa el enlace de «Acepto la política de
  datos» (tiene un error visible), marca la casilla dentro del modal y ciérralo: el error desaparece y el foco
  vuelve al enlace. Pulsa también el cuadro de otra casilla y el hueco de la fila: no abre nada.
- Con el backend levantado, abre http://localhost:5173/register: pulsa «Acepto los términos y condiciones», ciérralo
  sin marcar y verás el error; vuelve a abrirlo, marca la casilla del pie y ciérralo: el error desaparece.

## Riesgo residual aceptado
La validación (13-nov-2026) dio 14 de 16 requisitos cumplidos y el usuario aceptó cerrar con estos riesgos:
1. **RF-001**: la prueba de que pulsar el hueco de la fila no hace nada corre solo en jsdom, donde pasaría igual
   si la fila fuera una etiqueta `<label>`. En un navegador real funciona (comprobado a mano). Impacto medio,
   probabilidad baja.
2. **RF-016**: ninguna prueba en Chromium comprueba que, al cambiar el tamaño con el modal de la casilla abierto,
   se conservan el foco y el estado de la casilla (a mano, sí). Impacto bajo, probabilidad muy baja.
3. **Registro**: el contraste y el tema oscuro del registro solo se comprueban en jsdom y por sondeo manual, no con
   una prueba en Chromium. Impacto bajo, probabilidad baja.
4. **Movimiento reducido (S-03)**: defecto de código conocido. Con «reducir movimiento» la cortina del modal sigue
   con un fundido de 0,2 s (la caja no). Impacto bajo, probabilidad baja. Corrección posible: desactivar la
   animación de `::backdrop` bajo `prefers-reduced-motion` en `DocumentModal.css`.
5. **Observaciones menores**: Tab no se comprueba hacia todos los elementos del modal en Chromium; la prueba de
   desplazamiento mide la «×» y no el pie; la reserva de espacio del error no se mide en la casilla con documento;
   los «Cómo probarlo» de `tasks.md` llevan comandos en línea.

## Marco teórico
- **`<dialog>` nativo y modal.** Cuando se abre con `showModal()`, el navegador deja inerte el resto de la
  página, atrapa el foco dentro del diálogo y atiende Escape. Es más fiable que programar esas tres cosas a mano.
- **Componente controlado.** El modal no decide cuándo cerrarse: avisa («quiero cerrarme») y quien lo usa cambia
  `open`. La casilla es la dueña del estado marcado y las dos casillas lo leen y lo escriben; así no pueden
  contradecirse.
- **Por qué la fila no es una etiqueta `<label>`.** Una etiqueta marca su casilla al pulsar cualquier parte de
  ella. Como aquí el texto es un enlace que abre otra cosa, la fila no debe actuar como etiqueta; la casilla se
  nombra con el texto del enlace mediante `aria-labelledby`.
- **Enlaces sin subrayado y contraste.** Si un enlace no se subraya, solo el color lo distingue del texto, y ese
  color debe contrastar al menos 3:1 con el texto que lo rodea y 4,5:1 con el fondo. Por eso los enlaces del modal
  no son blancos.
- **Devolver el foco.** Al cerrar un diálogo, quien usa teclado o lector de pantalla debe volver donde estaba. Un
  `<dialog>` que se desmonta en vez de cerrarse no lo hace solo: hay que recordar el elemento que lo abrió.
- **Probar en un navegador real.** jsdom simula el DOM, pero no calcula el diseño ni el foco real. Que el foco no
  salga del modal o que la página de detrás no se desplace solo se comprueba en un navegador de verdad.
- **Validar al cerrar.** Un formulario suele validar un campo al salir de él. Como el modal se cierra sin que el
  foco «salga» de la casilla de verdad, el componente avisa al formulario a mano al cerrar.
