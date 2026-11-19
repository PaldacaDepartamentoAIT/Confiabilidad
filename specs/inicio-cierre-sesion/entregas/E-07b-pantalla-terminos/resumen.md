# Entrega E-07b · Pantalla de términos pendientes

Rama: `feat/inicio-cierre-sesion-pantalla-terminos` · PR: pendiente · Líneas de código y tests: 302 (límite: 400).

## Qué se hizo
- Se creó `frontend/src/auth/TermsPage.tsx` usando `PublicLayout`, `PublicPage`, `DocumentCheckbox` (modal con documento en Markdown), botón principal de aceptación y botón secundario de cierre de sesión (`T-019`, `RF-006`, `RF-011`, `RF-012`, `RF-015`, `RF-017`, `RF-019`):
  - Con `terms_status === "not_accepted"` y documento disponible, exige marcar la casilla antes de enviar, invoca `acceptTerms(client, { version, locale })`, notifica `onAccepted` y navega a `/`.
  - Si cambia el idioma de la interfaz (o si no se entregó `session` inicial), consulta `getSession(client)` para mostrar el documento en el idioma activo.
  - Con `terms_status === "no_current_version"` (o sin documento), oculta el formulario de aceptación, muestra `FormMessage` con `auth.termsUnavailableNotice` y mantiene el botón para cerrar la sesión actual (`S-06`).
  - El botón de cerrar sesión ejecuta `logout(client, tokenStorage)`, limpia el estado local y navega a `/login` incluso si el servidor responde `401` o falla la red (`S-07`).
- Se añadieron los tests `frontend/src/auth/TermsPage.test.tsx` (`CF-5`, `CF-7`).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-019 | Pantalla de términos pendientes (sin ruta) | `9b1d2c2` |

## Cómo ejecutarlo y probarlo
Actualiza las ramas remotas y cambia a la rama de la entrega:

```bash
git fetch origin
```

```bash
git checkout feat/inicio-cierre-sesion-pantalla-terminos
```
Deberías ver tu copia de trabajo en `feat/inicio-cierre-sesion-pantalla-terminos`.

Ejecuta los tests de la pantalla de términos pendientes:

```bash
pnpm --filter frontend test src/auth/TermsPage.test.tsx
```
Deberías ver los 3 tests de `TermsPage.test.tsx` en verde.

Ejecuta el linter y el chequeo de tipos del frontend:

```bash
pnpm --filter frontend lint
```
Deberías ver la salida limpia sin errores.

```bash
pnpm --filter frontend typecheck
```
Deberías ver `tsc --noEmit` terminar sin errores.
