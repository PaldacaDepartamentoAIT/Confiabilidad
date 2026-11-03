# Entrega E-12 · Textos del registro y errores del servidor

Rama: `feat/registro-flujo-textos` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#47](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/47) ·
Líneas de código y tests: 363 (límite: 400).

Primera entrega tras reorganizar las de las pantallas (aprobado el 2026-11-03): E-12 a E-14 se
re-estimaron por tarea y pasan a E-12, E-18, E-19, E-13, E-20, E-14 y E-21.

## Qué se hizo
- **Textos de las pantallas del registro** en `es`, `pt-BR` y `en`, en un grupo nuevo `register`:
  formulario (etiquetas, país, términos, marketing), verificación (texto fijo que no afirma que el
  correo exista ni que llegara un código, temporizador, reenvío, bloqueo, enlace no válido),
  contraseña y cuenta creada.
- **Textos de los errores del servidor** en el grupo `validation`: una clave por cada código que
  puede devolver el backend, con los mismos textos que `backend/apps/accounts/api/messages.py`, más
  la espera por límite superado, el fallo de red y un texto genérico para un código desconocido.
- **Traducción de los códigos** (`frontend/src/registration/serverErrors.ts`): convierte cada
  código del servidor en su clave, con los valores que el texto necesita (150 caracteres, 18 años y
  5 días), y un código desconocido en el genérico. Algunos códigos tienen un texto más preciso según
  el campo (correo, fecha de nacimiento), como en el servidor.
- Test nuevo: cada texto usa los mismos parámetros (`{{max}}`…) en los tres idiomas.
- Las pantallas aún no usan estos textos; lo harán desde E-18.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-041 | Textos del formulario y errores del servidor | `9d4abd1` |
| T-042 | Traducción de los errores del servidor | `96ff6fc` |
| T-045 | Textos de verificación, contraseña y cuenta creada | `5eacac6` |

T-041 tiene una excepción de 4 archivos, aprobada por el usuario: el grupo nuevo `register` obliga
a añadirlo a la lista de grupos de `locales.test.ts`.

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests de los textos:
```bash
pnpm --filter frontend exec vitest run src/i18n
```
Deberías ver 34 tests en verde: los tres idiomas tienen las mismas claves, ningún texto vacío y los
mismos parámetros. Ejecuta los tests de la traducción de los errores:
```bash
pnpm --filter frontend exec vitest run src/registration/serverErrors
```
Deberías ver 39 tests en verde: uno por cada código del servidor, los de campo, el genérico y los
valores de los textos con números. Ejecuta la suite completa del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 291 tests en verde.

## Marco teórico
- **Por qué el frontend traduce códigos y no muestra el mensaje del servidor.** El servidor ya
  devuelve un texto traducido, pero en el idioma que tenía al responder. Si la persona cambia el
  idioma de la pantalla después, ese texto quedaría en el idioma anterior. Guardar el código y
  traducirlo al pintar mantiene el error en el idioma activo (D-11).
- **Texto genérico para lo desconocido.** Si el servidor añade un código nuevo antes que el
  frontend, la pantalla muestra «Algo no ha funcionado…» en vez de un hueco o una clave sin
  traducir. El test de los códigos del servidor es la lista que hay que actualizar cuando eso pase.
