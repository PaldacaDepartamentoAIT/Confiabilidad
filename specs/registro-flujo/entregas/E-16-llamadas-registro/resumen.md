# Entrega E-16 · Llamadas del registro

Rama: `feat/registro-flujo-llamadas-registro` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#44](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/44) ·
Líneas de código y tests: 195 (límite: 400).

Sale de E-09, que con esta tarea medía 488 líneas. Va después de E-09 y antes de E-12.

## Qué se hizo
- **Llamadas del registro** (`frontend/src/api/registration.ts`): una función con tipos por cada
  ruta del flujo, todas sobre el cliente de E-09.
  - `fetchOptions`: países, términos y documento de marketing del formulario (GET).
  - `submitRegistration`: envía el formulario con los términos aceptados (`accepted: true`, versión
    e idioma del documento mostrado). `marketing` solo viaja si se pasa, es decir, si la casilla
    está marcada.
  - `fetchStatus`, `verifyCode`, `resendCode` y `completeRegistration`: llevan siempre el
    `public_id` en el cuerpo, nunca en la URL, junto con el código y la contraseña cuando la ruta
    los pide.
- Los tipos (`RegistrationOptions`, `RegistrationStatus`, `Started`…) reflejan las respuestas del
  backend, para que las pantallas no adivinen nombres de campos.
- Las pantallas aún no usan estas funciones; lo harán desde E-12.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-035 | Llamadas del registro | `49203cc` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests de las llamadas del registro:
```bash
pnpm --filter frontend exec vitest run src/api/registration
```
Deberías ver 7 tests en verde: uno por ruta, más el que comprueba que `marketing` solo se envía
cuando se pasa. Ejecuta la suite completa del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 216 tests en verde.

## Marco teórico
- **El `public_id` va en el cuerpo, no en la URL.** Las rutas del flujo son fijas
  (`registration/verify`…), y el identificador viaja en el JSON. Así no aparece en los registros de
  acceso de los servidores ni en el historial de proxys, que guardan la URL pero no el cuerpo.
- **Ausente no es lo mismo que `undefined`.** En JavaScript, un objeto con `marketing: undefined`
  tiene la clave y otro sin ella no la tiene. Al convertirlo a JSON los dos dan lo mismo, pero el
  test exige que la clave no exista, para que la función cumpla la tarea por sí misma y no dependa
  de cómo se serialice después.
