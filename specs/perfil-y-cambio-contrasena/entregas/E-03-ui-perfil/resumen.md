# Entrega E-03 · Pantalla `/profile` de consulta y navegación lateral privada

Rama: `feat/perfil-y-cambio-contrasena-ui-perfil` · Líneas de código y tests: 399 (límite: 400).

## Qué se hizo
- En `frontend/src/api/profile.ts` (`T-010`, `RF-001`) se añadió `getProfile` y el tipo `ProfileData` sobre `GET /auth/profile`.
- En `frontend/src/forms/countries.ts`, `frontend/src/registration/RegisterPage.tsx` y `frontend/src/i18n/locales/{en,es,pt-BR}.ts` (`T-011`, `RF-012` y `RF-013`) se extrajo el catálogo localizado compartido de países y se incorporaron las traducciones de perfil y navegación en los tres idiomas.
- En `frontend/src/auth/ProfilePage.tsx`, `frontend/src/auth/ProfilePage.css` y `frontend/src/auth/ProfilePage.test.tsx` (`T-012`, `RF-001`, `RF-011`…`RF-013`) se creó la pantalla `/profile` con bloque de información personal en solo lectura (incluyendo `"ZZ"` como «Sin país asignado»), manejo de redirecciones por sesión o términos pendientes y comprobación de accesibilidad con `axe-core`.
- En `frontend/src/icons/index.ts`, `frontend/src/layouts/Sidebar.tsx`, `frontend/src/auth/privateNav.tsx`, `frontend/src/auth/HomePage.tsx`, `frontend/src/App.tsx` y `frontend/src/App.test.tsx` (`T-013`, `RF-001`, `RF-012`) se añadió el icono `IconUser`, navegación SPA en `SidebarItem`, barra lateral privada compartida entre `/` y `/profile` y la ruta `/profile` en el enrutador.
- División de entrega: al superar 400 líneas con el formulario editable completo, la edición parcial (`patch`, `updateProfile`, validaciones y actualización en vivo del menú lateral) pasa a `E-03b` (`T-010b` y `T-012b`).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-010 | Cliente HTTP de consulta de perfil (`getProfile` en `api/profile.ts`) | `3f365f1` / `0801f25` |
| T-011 | Helper compartido de países y traducciones de perfil en tres idiomas | `5c1703a` |
| T-012 | Vista de consulta de información personal en `ProfilePage` | `d38f772` / `6e7e78e` |
| T-013 | Conexión de `/profile` en `App` y menú lateral privado compartido | `6e7e78e` |

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
