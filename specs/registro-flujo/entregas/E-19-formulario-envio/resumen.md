# Entrega E-19 · Pantalla del formulario: envío

Rama: `feat/registro-flujo-formulario-envio` · PR: pendiente ·
Líneas de código y tests: 289 (límite: 400).

## Qué se hizo
- **Envío del formulario de registro** (`frontend/src/registration/RegisterPage.tsx`), todavía sin
  ruta:
  - con los datos correctos, envía al servidor el nombre, la fecha, el correo, el país, los términos
    aceptados (su versión e idioma) y el idioma de la pantalla. El consentimiento de marketing solo
    viaja si la casilla está marcada;
  - con `202`, va a la verificación: `/register/continue#<identificador>`;
  - con errores de campo (`400`), pinta bajo cada campo todos sus errores traducidos, desplaza la
    página hasta el primero en el orden del formulario y le lleva el foco. Un error que no
    corresponde a ningún campo de la pantalla da un mensaje general;
  - con límite superado (`429`), muestra «Demasiados intentos. Vuelve a intentarlo en N s.»
    contando hacia atrás y desactiva el botón hasta llegar a cero;
  - con un fallo de red o del servidor, muestra un mensaje general y conserva lo escrito;
  - mientras espera la respuesta, un segundo envío no hace nada.

## Tareas
El detalle de la tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-044 | Pantalla del formulario: envío | `5d8c345` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests de la pantalla del formulario:
```bash
pnpm --filter frontend exec vitest run src/registration/RegisterPage
```
Deberías ver 19 tests en verde: los 9 de los campos y las comprobaciones y los 10 del envío (datos
enviados, marketing, errores bajo cada campo, errores mezclados, doble envío, fallo de red, fallo del
servidor, rechazo con código y cuenta atrás). Ejecuta la suite completa del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 310 tests en verde. La pantalla todavía no tiene ruta: se podrá abrir en
http://localhost:5173/register a partir de E-15.

## Marco teórico
- **Por qué se desactiva el botón con un `429` y no se reintenta solo.** El servidor dice cuántos
  segundos faltan para volver a aceptar peticiones. Reintentar antes solo gasta intentos y alarga el
  bloqueo; reintentar solo, sin que la persona lo pida, enviaría datos que quizá ya quiere cambiar.
  Por eso la pantalla cuenta hacia atrás y deja que la persona vuelva a pulsar al llegar a cero.
- **Por qué un error «sin campo» va arriba.** El servidor puede devolver un error que no pertenece a
  ningún campo (por ejemplo, un cuerpo ilegible). Si la pantalla solo pintara errores bajo los
  campos, ese error no se vería y la persona no sabría por qué no avanza.
