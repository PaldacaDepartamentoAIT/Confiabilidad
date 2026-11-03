# Entrega E-09 · Cliente de la API

Rama: `feat/registro-flujo-cliente-api` · PR: pendiente ·
Líneas de código y tests: 293 (límite: 400).

La entrega se planificó con T-034 y T-035, pero juntas medían 488 líneas. Se dividió: T-035
(llamadas del registro) pasa a E-16.

## Qué se hizo
- **Cliente de la API** (`frontend/src/api/client.ts`): un único punto por el que el frontend habla
  con el backend.
  - En el navegador usa las rutas `/api/browser/v1/…` con la cookie de sesión del mismo origen y
    envía el token CSRF de la cookie `csrftoken` en la cabecera `X-CSRFToken`.
  - En el escritorio (Tauri, detectado por su objeto global `__TAURI_INTERNALS__`) usa
    `VITE_API_BASE_URL` + `/api/app/v1/…`, sin cookies ni CSRF.
  - Cada petición lleva el idioma activo en `Accept-Language` y en `language` (en el cuerpo de los
    POST y en la consulta de los GET).
  - Convierte cada respuesta en un resultado con tipo: éxito, errores por campo (solo sus códigos),
    rechazo con código, no encontrado (`404`), límite superado (`429`, con los segundos de espera
    del cuerpo o, si faltan, de la cabecera `Retry-After`), fallo sin código y fallo de red.
- Las pantallas aún no lo usan; lo harán desde E-12.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-034 | Cliente de la API | `e5babca` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests del cliente:
```bash
pnpm --filter frontend exec vitest run src/api/client
```
Deberías ver 16 tests en verde, uno por cada comportamiento: rutas y CSRF del navegador, rutas
de Tauri, idioma en los GET, errores por campo, rechazo, `404`, `429` con y sin espera en el
cuerpo, `403` y `500`, fallo de red, cuerpo vacío, ausencia de cookie y lectura del entorno.
Ejecuta la suite completa del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 209 tests en verde.

## Marco teórico
- **Dos rutas para la misma API.** El navegador y el escritorio llaman a vistas distintas
  (`browser` y `app`) porque se autentican de forma distinta. El navegador envía cookies solo, así que
  necesita el token CSRF para demostrar que la petición sale de la propia web. Tauri no usa cookies
  del navegador, por lo que no corre ese riesgo y no lleva token. Elegir la ruta en un solo sitio
  evita que una pantalla mezcle las dos.
- **Resultados con tipo en vez de excepciones.** Cada respuesta se convierte en un valor con un
  `kind` que TypeScript obliga a tratar. Así una pantalla no puede olvidarse del `429` o del `404`
  sin que el compilador lo note.
