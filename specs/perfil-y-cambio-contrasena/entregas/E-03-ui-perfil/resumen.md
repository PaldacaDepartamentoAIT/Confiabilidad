# Entrega E-03 · Pantalla `/profile` de consulta y navegación lateral privada

Rama: `feat/perfil-y-cambio-contrasena-ui-perfil` · Líneas de código y tests: 493 (límite con excepción justificada en `tasks.md`: 500).

## Qué se hizo
- En `docs/identidad-visual.md` y `frontend/src/styles/base.css` se documentó e implementó el patrón visual de *placeholders* de carga (*skeleton*) en gris claro (`color-mix(in srgb, var(--grid) 55%, var(--bg))` con reflejo al `22%`) y transición suave (*fade out* de `0,16 s` del skeleton seguido de *fade in* de `0,2 s` del contenido real, respetando `prefers-reduced-motion`).
- En `frontend/src/api/client.ts`, `frontend/src/api/client.test.ts` y `frontend/src/api/profile.ts` (`T-010`, `RF-001`) se añadió `getProfile` sobre `GET /auth/profile` y la deduplicación de peticiones `GET` concurrentes idénticas en vuelo para evitar llamadas duplicadas en desarrollo (`StrictMode`).
- En `frontend/src/forms/countries.ts`, `frontend/src/registration/RegisterPage.tsx` y `frontend/src/i18n/locales/{en,es,pt-BR}.ts` (`T-011`, `RF-012` y `RF-013`) se extrajo el catálogo localizado compartido de países y se incorporaron las traducciones de perfil y navegación en los tres idiomas.
- En `frontend/src/auth/ProfilePage.tsx`, `frontend/src/auth/ProfilePage.css` y `frontend/src/auth/ProfilePage.test.tsx` (`T-012`, `RF-001`, `RF-011`…`RF-013`) se creó la pantalla `/profile` manteniendo siempre visible el bloque con *placeholders* *skeleton* de 36 px (`aria-busy="true"`) y transición de entrada al recibir los datos, mostrando los campos en solo lectura (incluyendo `"ZZ"` como «Sin país asignado»), redirecciones por sesión o términos pendientes y comprobación de accesibilidad con `axe-core`.
- En `frontend/src/icons/index.ts`, `frontend/src/icons/icons.test.tsx`, `frontend/src/layouts/Sidebar.tsx`, `frontend/src/auth/privateNav.tsx`, `frontend/src/auth/HomePage.tsx`, `frontend/src/App.tsx` y `frontend/src/App.test.tsx` (`T-013`, `RF-001`, `RF-012`) se añadió el icono `IconUser`, navegación SPA en `SidebarItem`, barra lateral privada compartida entre `/` y `/profile` y la ruta `/profile` en el enrutador.
- División de entrega: la extensión homóloga del *skeleton* al panel principal (`HomePage`, `T-013b`) pasa a `E-03b` y la edición parcial del perfil (`T-010b`, `T-012b`) pasa a `E-03c` para mantener cada PR dentro del límite de líneas.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-010 | Cliente HTTP de consulta de perfil (`getProfile`) y deduplicación de `GET` | `3f365f1` / `0801f25` / `775a465` |
| T-011 | Helper compartido de países y traducciones de perfil en tres idiomas | `5c1703a` |
| T-012 | Vista de consulta y *skeletons* con *fade* en `ProfilePage` | `d38f772` / `8683bf5` / `775a465` |
| T-013 | Conexión de `/profile` en `App` y menú lateral privado compartido | `6e7e78e` / `dee2a35` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con las dependencias de frontend instaladas, actualiza las ramas remotas y cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/perfil-y-cambio-contrasena-ui-perfil
```
Ejecuta los tests de frontend (Vitest + React Testing Library + `axe-core`):
```bash
pnpm --filter frontend test
```
Deberías ver toda la suite de frontend en verde (`App.test.tsx`, `ProfilePage.test.tsx`, `locales.test.ts` y `keys.test.ts` incluidos).

Ejecuta la comprobación de tipos, ESLint y Prettier:
```bash
pnpm --filter frontend typecheck
```
Deberías ver cero errores de TypeScript.
```bash
pnpm --filter frontend lint
```
Deberías ver cero advertencias ni errores de ESLint.
```bash
pnpm --filter frontend exec prettier --check .
```
Deberías ver todos los archivos formateados correctamente.

Para probarlo manualmente en navegador (o cliente Tauri) con el stack levantado:
1. Inicia sesión en `/login` con una cuenta activa y términos aceptados.
2. En `/`, pulsa «Perfil» en el menú lateral izquierdo.
3. Comprueba que la URL cambia a `/profile` sin recargar la página y muestra correo, nombre, fecha de nacimiento y país en solo lectura (o «Sin país asignado» si el usuario conserva `"ZZ"`).
4. Si pruebas con sesión expirada o términos pendientes, `/profile` redirige automáticamente a `/login` o `/terms`.
