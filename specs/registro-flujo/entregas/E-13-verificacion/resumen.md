# Entrega E-13 · Pantalla de verificación: estado y enlace no válido

Rama: `feat/registro-flujo-verificacion` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#50](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/50) ·
Líneas de código y tests: 291 (límite: 400).

## Qué se hizo
- **Pantalla de verificación** (`frontend/src/registration/VerifyPage.tsx`), todavía sin ruta y
  sin el campo del código (llega en E-20):
  - lee el identificador del fragmento de la URL (`/register/continue#<identificador>`), que nunca
    viaja al servidor en la dirección, y lo envía en el cuerpo de la consulta de estado;
  - si el navegador no tiene la cookie CSRF (por ejemplo, al abrir el enlace del correo en otro
    navegador), la pide antes con la consulta de opciones (D-09);
  - muestra un texto fijo que no afirma que el correo exista ni que llegara un código, y el tiempo
    que le queda al código (`El código caduca en 14:59.`), contando cada segundo. Al llegar a cero,
    o si el servidor dice que el registro caducó, indica que hay que pedir otro;
  - al recargar, vuelve a preguntar al servidor, que es quien sabe el tiempo real;
  - con un identificador desconocido (`404`), o sin identificador, muestra «Enlace no válido» con
    un enlace al formulario de registro;
  - nunca muestra el correo: la pantalla no lo recibe.

## Tareas
El detalle de la tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-046 | Pantalla de verificación: estado y enlace no válido | `76f2683` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests de la pantalla de verificación:
```bash
pnpm --filter frontend exec vitest run src/registration/VerifyPage
```
Deberías ver 10 tests en verde: estado y texto fijo, cuenta atrás hasta caducar, caducado según el
servidor, cookie CSRF, recarga, enlace no válido, sin identificador, fallo de red, fallo del
servidor y respuesta antigua descartada. Ejecuta la suite completa del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 320 tests en verde. La pantalla todavía no tiene ruta: se podrá abrir en
http://localhost:5173/register/continue a partir de E-15.

## Marco teórico
- **Por qué el identificador va en el fragmento (`#`).** El navegador nunca envía al servidor la
  parte de la URL que va después de `#`: no aparece en los registros de acceso ni en la cabecera
  `Referer`. La pantalla lo lee en el navegador y lo manda en el cuerpo de la petición.
- **Por qué el temporizador no se anuncia.** Una región «viva» hace que el lector de pantalla lea
  cada cambio. Si el temporizador lo fuera, leería un número cada segundo e impediría usar la
  pantalla. El tiempo está a la vista y se lee cuando la persona llega a él.
