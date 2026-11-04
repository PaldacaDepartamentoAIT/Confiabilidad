# Entrega E-20 · Pantalla de verificación: código, bloqueo y reenvío

Rama: `feat/registro-flujo-verificacion-codigo` · PR: pendiente ·
Líneas de código y tests: 431 (límite: 400; excepción aprobada por el usuario el 2026-11-04).

T-048 se podía separar en su propia entrega; el usuario prefirió no partirla.

## Qué se hizo
- **Código y bloqueo** (`frontend/src/registration/VerifyPage.tsx`), todavía sin ruta:
  - campo del código de 6 dígitos con su botón «Verificar». Un código incompleto no se envía;
  - un código incorrecto o caducado muestra su mensaje bajo el campo;
  - con los intentos agotados (`locked`), en la respuesta o ya al cargar la pantalla, se avisa y se
    desactiva el envío: solo queda pedir otro código;
  - con límite superado (`429`), cuenta atrás y botón desactivado hasta llegar a cero;
  - si el identificador deja de existir, «Enlace no válido»; otros rechazos y fallos dan un
    mensaje general;
  - si el servidor acepta el código, todavía no pasa nada visible: el paso de contraseña llega en
    E-21.
- **Reenvío del código**:
  - el botón «Enviar otro código» muestra la espera que indica el servidor y se activa al llegar a
    cero. Debajo dice cuántos códigos se pueden pedir aún;
  - al reenviar, avisa con un texto neutro, vuelve a pedir el estado (tiempo, reenvíos) y quita el
    bloqueo del código anterior;
  - sin reenvíos restantes, el botón se desactiva y se ofrece volver al formulario;
  - un rechazo (`resend_unavailable`) o un fallo dan su mensaje, y un `429` hace que el botón
    cuente la espera.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-047 | Pantalla de verificación: código y bloqueo | `c9aae98` |
| T-048 | Pantalla de verificación: reenvío | `1c59b57` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests de la pantalla de verificación:
```bash
pnpm --filter frontend exec vitest run src/registration/VerifyPage
```
Deberías ver 29 tests en verde: los 10 del estado y el enlace no válido, 10 del código y el bloqueo
y 9 del reenvío. Ejecuta la suite completa del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 339 tests en verde. La pantalla todavía no tiene ruta: se podrá abrir en
http://localhost:5173/register/continue a partir de E-15.

## Marco teórico
- **Por qué el formulario del código se vuelve a montar con cada estado.** El bloqueo pertenece al
  código vigente: al reenviar, el servidor emite uno nuevo sin intentos gastados. Montar de nuevo el
  formulario con el estado recién recibido es la forma más simple de partir de cero con la verdad
  del servidor. Montarlo antes de que llegue ese estado conservaba el bloqueo anterior: ese fue el
  fallo que encontraron los tests.
- **Por qué un test «ve» un temporizador que no corre.** En los tests, el reloj es simulado y
  avanza cuando el test lo pide. Si lo adelanta antes de que React haya creado el intervalo, el
  tiempo pasa sin que nada cuente. `advanceTimersByTimeAsync` deja que React termine su trabajo
  pendiente entre cada paso del reloj.
