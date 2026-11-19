# Entrega E-04 · Registro con la casilla con documento

Rama: `feat/casilla-con-documento-registro` (sale de `feat/casilla-con-documento`) · PR: [#110](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/110) ·
Líneas de código y tests: 274 (límite: 400).

## Qué se hizo
- El formulario de registro usa ya la casilla con documento para las dos aceptaciones, una encima de la otra,
  en lugar de los desplegables: los términos (obligatoria) y, si existe documento de marketing, el consentimiento
  de marketing (opcional). Pulsar el texto abre el documento en un modal; pulsar el cuadro marca la casilla.
- Los nombres de campo, la validación de los términos y los datos que se envían (versión e idioma de cada
  documento aceptado, y el marketing solo si está marcado) no cambian: las pruebas de envío que ya había pasan
  sin tocarlas.
- Al cerrar el modal se revalida la casilla de los términos: aparece el error «Debes aceptar los términos y
  condiciones.» si no está marcada, y se retira si se marcó desde el modal. El foco vuelve al enlace.
- El formulario completo cabe ahora sin desplazamiento a 1000 px de ancho (verificado en un navegador real).
- Se retiraron los textos de los desplegables (`register.termsTitle` y `register.marketingTitle`) de los tres
  idiomas.
- Hay pruebas nuevas de idioma (cambiar de idioma con el modal abierto actualiza los textos sin cerrarlo y
  conserva el estado y el foco), de teclado (Tab, Enter, Espacio y Escape) y de accesibilidad con `axe`, con el
  modal cerrado y abierto, en el componente y en el registro.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-012 | Casilla con documento: idioma y accesibilidad | `9e30a7d` |
| T-013 | Registro con la casilla con documento | `691a22b` |
| T-014 | Retirar los textos de los desplegables | `76b2afb` |
| T-015 | Accesibilidad del registro con el modal abierto | `65b4ace` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 61 archivos de test en verde (786 tests).

Levanta la aplicación, con el backend levantado:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/register: verás los campos y, debajo, dos casillas con su texto subrayado. Pulsa «Acepto
los términos y condiciones»: se abre el documento. Ciérralo sin marcar: aparece el error de los términos. Vuelve a
abrirlo, marca la casilla del pie y ciérralo: el error desaparece y la casilla de fuera queda marcada. Pulsa «Continuar»
y el registro sigue como siempre.

## Marco teórico
- **Una casilla, dos vistas:** la casilla de fuera y la del modal muestran el mismo estado; no hay dos casillas
  independientes, así que no pueden contradecirse.
- **Retirar textos que ya no se usan:** cada clave de traducción que sobra en un idioma o en otro rompe la
  paridad de idiomas; por eso se retiran de los tres a la vez.
