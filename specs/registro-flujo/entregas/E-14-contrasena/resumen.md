# Entrega E-14 · Paso de contraseña

Rama: `feat/registro-flujo-contrasena` · PR: pendiente ·
Líneas de código y tests: 262 (límite: 400).

## Qué se hizo
- **Paso de contraseña** (`frontend/src/registration/PasswordStep.tsx`), un componente que la
  pantalla de verificación mostrará cuando el servidor acepte el código (E-21):
  - campo de contraseña nueva (`autocomplete="new-password"`, con el botón de mostrarla) y botón
    «Crear cuenta»;
  - antes de llamar al servidor, comprueba en el navegador que tiene al menos 12 caracteres y que no
    es solo números, con los mismos dígitos que el servidor (E-11);
  - envía el identificador, el código aceptado y la contraseña. Con `201`, avisa de que la cuenta se
    creó;
  - si el servidor rechaza la contraseña, pinta bajo el campo todas las reglas incumplidas a la vez
    (parecida al nombre o al correo, común, filtrada…) y conserva el código para probar otra;
  - si el servidor rechaza el código (incorrecto, bloqueado, caducado o identificador
    desconocido), no reintenta: avisa a quien guarda el código, que vuelve a la verificación (E-21);
  - con límite superado, cuenta atrás y botón desactivado; con fallo de red o del servidor, mensaje
    general sin perder la contraseña escrita; sin doble envío.

## Tareas
El detalle de la tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-049 | Paso de contraseña | `ebce83d` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests del paso de contraseña:
```bash
pnpm --filter frontend exec vitest run src/registration/PasswordStep
```
Deberías ver 11 tests en verde: las dos reglas del navegador, el envío con éxito, las reglas del
servidor, tres rechazos del código, la cuenta atrás, dos fallos y el doble envío. Ejecuta la suite
completa del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 350 tests en verde. El paso todavía no aparece en ninguna pantalla: se verá al
verificar el código a partir de E-21, y en el navegador a partir de E-15.

## Marco teórico
- **Por qué el navegador comprueba solo dos reglas.** Longitud y «solo números» se pueden comprobar
  sin datos de nadie. Las demás (parecida al nombre o al correo, común, filtrada) necesitan los datos
  del registro pendiente o listas del servidor, así que solo las comprueba él. Comprobar en el
  navegador lo que se puede ahorra un viaje y un posible intento.
- **Por qué el paso no decide qué hacer con un código rechazado.** El código lo guarda la pantalla
  de verificación, solo en memoria (RF-011). Si el servidor lo rechaza al crear la cuenta, quien lo
  guarda debe olvidarlo y volver a pedirlo; el paso solo informa del rechazo.
