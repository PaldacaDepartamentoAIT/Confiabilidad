# Entrega E-07b · Pantalla de términos pendientes y rutas `/login` y `/terms`

Rama: `feat/inicio-cierre-sesion-pantalla-terminos` · PR: pendiente · Líneas de código y tests: 355 (límite: 400).

## Qué se hizo
- Se creó `frontend/src/auth/TermsPage.tsx` usando `PublicLayout`, `PublicPage`, `DocumentCheckbox` (modal con documento en Markdown), botón principal de aceptación y botón secundario de cierre de sesión (`T-019`, `RF-006`, `RF-011`, `RF-012`, `RF-015`, `RF-017`, `RF-019`).
  - Con `terms_status === "not_accepted"` y documento disponible, exige marcar la casilla antes de enviar, invoca `acceptTerms(client, { version, locale })`, notifica `onAccepted` y navega a `/`.
  - Con `terms_status === "no_current_version"` (o sin documento), oculta el formulario de aceptación, muestra `FormMessage` con `auth.termsUnavailableNotice` y mantiene el botón para cerrar la sesión actual (`S-06`).
  - El botón de cerrar sesión ejecuta `logout(client, tokenStorage)`, limpia el estado local y navega a `/login` incluso si el servidor responde `401` o falla la red (`S-07`).
- Se conectaron `/login` (`LoginPage`) y `/terms` (`TermsPage`) en `frontend/src/App.tsx` y `frontend/src/App.test.tsx` para poder visualizar e interactuar con ambas pantallas en el navegador desde esta misma entrega.
- Se añadieron los tests `frontend/src/auth/TermsPage.test.tsx` (`CF-5`, `CF-7`).
- Se documentó en `AGENTS.md` y `.claude/skills/sdd-tareas/SKILL.md` la regla de exponer siempre en una ruta visible o en `/showcase` cualquier pantalla o componente visual en la misma entrega que lo crea.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-019 | Pantalla de términos pendientes y conexión de rutas `/login` y `/terms` | `9b1d2c2` |

## Cómo ejecutarlo y probarlo
Actualiza las ramas remotas y cambia a la rama de la entrega:

```bash
git fetch origin
```

```bash
git checkout feat/inicio-cierre-sesion-pantalla-terminos
```
Deberías ver tu copia de trabajo en `feat/inicio-cierre-sesion-pantalla-terminos`.

### Ver las pantallas en el navegador
Con los servicios levantados (`docker compose -f docker/docker-compose.yml up` o `pnpm --filter frontend dev`), abre en el navegador:
- `http://localhost:5173/login`: muestra la pantalla de inicio de sesión (`LoginPage`) con validación al salir/enviar, selector de idioma/tema, botón de mostrar contraseña y enlace a `/register`.
- Si inicias sesión con un usuario de prueba que aún no ha aceptado la versión vigente de términos (por ejemplo `demo@example.com` con `DemoPass123!`), te lleva automáticamente a `http://localhost:5173/terms` (`TermsPage`), donde puedes abrir el modal con el documento en Markdown, marcar la casilla y aceptarlo o cerrar sesión.

### Tests y análisis estático
Ejecuta los tests de la pantalla de términos y del enrutador principal:

```bash
pnpm --filter frontend test src/auth/TermsPage.test.tsx src/App.test.tsx
```
Deberías ver todos los tests de `TermsPage.test.tsx` y `App.test.tsx` en verde.

Ejecuta el linter y el chequeo de tipos del frontend:

```bash
pnpm --filter frontend lint
```
Deberías ver la salida limpia sin errores.

```bash
pnpm --filter frontend typecheck
```
Deberías ver `tsc --noEmit` terminar sin errores.
