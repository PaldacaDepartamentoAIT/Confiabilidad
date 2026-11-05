# Entrega E-21 · Verificación con paso de contraseña y cuenta creada

Rama: `feat/registro-flujo-cuenta-creada` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#53](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/53) ·
Líneas de código y tests: 159 (límite: 400).

## Qué se hizo
- **Verificación con paso de contraseña** (`frontend/src/registration/VerifyPage.tsx`):
  - cuando el servidor acepta el código, la pantalla muestra el paso de contraseña (E-14) en lugar
    del campo del código y del reenvío. El código aceptado se guarda solo en la memoria de la
    página: no va a la URL ni al almacenamiento del navegador;
  - si el servidor rechaza el código al crear la cuenta (incorrecto, bloqueado, caducado), la
    pantalla lo olvida, vuelve a la verificación con su mensaje y pide de nuevo el estado. Si el
    identificador ya no existe, muestra «Enlace no válido»;
  - recargar la página vuelve a la verificación, porque el código no se guardó;
  - con la cuenta creada, va a `/register/done`.
- **Pantalla de cuenta creada** (`frontend/src/registration/DonePage.tsx`): dice que la cuenta se
  creó, sin iniciar sesión (el inicio de sesión no es de esta feature).

## Tareas
El detalle de la tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-050 | Verificación con paso de contraseña y cuenta creada | `9359f14` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests de la pantalla de verificación:
```bash
pnpm --filter frontend exec vitest run src/registration/VerifyPage
```
Deberías ver 35 tests en verde, entre ellos los 6 nuevos: paso de contraseña con el código solo en
memoria, cuenta creada, código rechazado al final, identificador que desaparece, recarga y pantalla
de cuenta creada. Ejecuta la suite completa del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 356 tests en verde. Las pantallas todavía no tienen ruta: el registro completo se
podrá recorrer en http://localhost:5173/register a partir de E-15.

## Marco teórico
- **Por qué el código vive solo en memoria.** Si el código aceptado se guardara en la URL o en el
  almacenamiento del navegador, quedaría en el historial o en disco, y otra persona con acceso al
  equipo podría usarlo para elegir la contraseña. En memoria desaparece al recargar o cerrar la
  pestaña. El coste es que, tras recargar, hay que volver a escribir el código, que sigue siendo
  válido mientras no caduque ni se agoten los intentos.
- **Por qué el servidor vuelve a comprobar el código al crear la cuenta.** Que la pantalla haya
  aceptado el código no prueba nada al servidor: una petición puede llegar sin pasar por la
  pantalla. Por eso cada intento de crear la cuenta lleva el código y el servidor lo comprueba otra
  vez (RF-012); si lo rechaza, la pantalla vuelve a la verificación.
