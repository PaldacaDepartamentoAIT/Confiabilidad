# Entrega E-10 · Casilla, selector, fecha y validación ampliada

Rama: `feat/registro-flujo-campos` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#45](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/45) ·
Líneas de código y tests: 409 (límite: 400; excepción aprobada por el usuario el 2026-11-03).

T-038 se podía separar en su propia entrega; el usuario prefirió no partirla por 9 líneas de
exceso.

## Qué se hizo
- **Casilla** (`frontend/src/components/fields/Checkbox.tsx`) y **selector**
  (`frontend/src/components/fields/SelectField.tsx`), con la misma estructura accesible que el
  campo de texto: etiqueta asociada, asterisco de obligatorio oculto al lector, `aria-required`,
  `aria-invalid` con error, y ayuda y error leídos como descripción del campo. La etiqueta de la
  casilla admite contenido, para poder enlazar los términos. El selector empieza con una opción
  vacía («Elige…») que vale `""`. `axe-core` no encuentra fallos con error en los dos.
- **Campo de fecha**: `TextField` admite `type="date"`, que el formulario usará para la fecha de
  nacimiento.
- **Validación ampliada** (`frontend/src/forms/useFormValidation.ts`), sin cambiar a quien ya la usa:
  - lee los `<select>` por su valor y las casillas como `"true"` (marcada) o `""` (sin marcar), al
    salir del campo y al enviar;
  - un campo puede recibir varios errores del servidor a la vez: `errors` sigue dando el primero y
    `allErrors` da la lista completa;
  - con la opción `scrollToError`, desplaza la página hasta el primer campo con error y después le
    lleva el foco, tanto al enviar como con los errores del servidor.
- Las pantallas aún no usan estas piezas; lo harán desde E-12.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-036 | Casilla y selector accesibles | `21228c0` |
| T-037 | Campo de fecha | `987ab00` |
| T-038 | Validación con selectores, casillas y varios errores | `04642e4` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests de los campos:
```bash
pnpm --filter frontend exec vitest run src/components/fields
```
Deberías ver en verde, entre otros, los 8 tests de la casilla y el selector y el del campo de
fecha. Ejecuta los tests de la validación:
```bash
pnpm --filter frontend exec vitest run src/forms/useFormValidation
```
Deberías ver 21 tests en verde: los 14 que ya existían, sin cambios, y los nuevos de selector,
casilla, varios errores y desplazamiento. Ejecuta la suite completa del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 232 tests en verde.

## Marco teórico
- **Desplazar antes de enfocar.** Al enfocar un campo, el navegador lo trae a la vista, pero no
  siempre lo deja bien encuadrado: puede quedar pegado al borde o tapado por una barra fija.
  `scrollIntoView({ block: "center" })` lo centra primero, y el foco llega después, para que la
  persona vea el error y el lector de pantalla lea el campo con su error.
- **Por qué una casilla vale `"true"` o `""`.** El hook valida textos. Si la casilla se convierte en
  texto vacío cuando no está marcada, la regla «obligatorio» que ya usan los demás campos sirve
  también para «acepta los términos», sin una regla especial.
