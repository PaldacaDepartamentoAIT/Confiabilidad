# Entrega E-03b · Edición parcial de datos personales en `/profile`

Rama: `feat/perfil-y-cambio-contrasena-ui-perfil-edicion` · Líneas de código y tests: 460 (límite con excepción justificada en `tasks.md`: 500).

## Qué se hizo
- En `frontend/src/api/client.ts`, `frontend/src/api/profile.ts`, `frontend/src/registration/serverErrors.ts`, `frontend/src/registration/serverErrors.test.ts`, `frontend/src/api/auth.test.ts` y `frontend/src/api/registration.test.ts` (`T-010b`, `RF-002`…`RF-004`, `RF-013`) se añadió `patch` al `ApiClient` compartiendo `jsonSend` con `post`, `updateProfile` (`PATCH /auth/profile`) y la traducción de `email_immutable`, `unknown_field` y `no_profile_fields`.
- En `frontend/src/auth/ProfilePage.tsx`, `frontend/src/auth/ProfilePage.css` y `frontend/src/auth/ProfilePage.test.tsx` (`T-012b`, `RF-002`…`RF-004`, `RF-011`…`RF-013`) se añadió el formulario `PersonalInfoBlock` dentro del `Block` con *skeletons* de carga (`ProfileSkeleton`):
  - mantiene `email` en solo lectura;
  - carga el catálogo localizado de países (`fetchOptions` + `countryOptions`), muestra «Sin país asignado» cuando está en `"ZZ"` y omite `country` del `PATCH` mientras siga sin seleccionarse (`C-02`), exigiéndolo una vez asignado;
  - valida en `blur` y al enviar con `useFormValidation` (foco al primer error, errores de servidor y texto recortado sincronizado en el input);
  - actualiza al instante `ProfilePage`, `UserProvider` y `App`.
- En `frontend/src/App.tsx` y `frontend/src/App.test.tsx` (`T-012b`) se conectó `onProfileUpdated` y se verificó que editar el nombre en `/profile` actualiza en vivo el botón de usuario de la barra lateral.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-010b | Cliente HTTP `patch`, `updateProfile` y mapeo de errores de edición | `41ec34f` |
| T-012b | Edición parcial, validación y sincronización lateral en `ProfilePage` | `1ed9ec9` / `2d95604` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con las dependencias de frontend instaladas, actualiza ramas y pasa a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/perfil-y-cambio-contrasena-ui-perfil-edicion
```
Ejecuta los tests, comprobación de tipos, ESLint y Prettier:
```bash
pnpm --filter frontend test
```
Deberías ver toda la suite de frontend (`ProfilePage.test.tsx`, `App.test.tsx`, `serverErrors.test.ts`, etc.) en verde.
```bash
pnpm --filter frontend typecheck
```
Deberías ver cero errores de TypeScript.
```bash
pnpm --filter frontend lint
```
Deberías ver cero errores ni advertencias de ESLint.
```bash
pnpm --filter frontend exec prettier --check .
```
Deberías ver `All matched files use Prettier code style!`.

Para probarlo manualmente en el navegador (o en Tauri) con el stack levantado:
1. Inicia sesión y abre `/profile` desde el menú lateral («Perfil»).
2. Comprueba que el correo es de solo lectura, edita el nombre con espacios alrededor o cambia la fecha/país y pulsa «Guardar cambios».
3. Verifica el mensaje de confirmación, que el nombre queda recortado en el campo y que el botón de usuario del menú lateral cambia al instante (y en Network que `PATCH /api/browser/v1/auth/profile` devuelve `200`).
4. Prueba enviar el nombre vacío o con dos espacios seguidos para comprobar la validación local y la del servidor con foco en el campo.
