# Entrega E-06b · Confirmación de deshabilitación en dos pasos desde `/profile`

Rama: `feat/deshabilitar-cuenta-ui-perfil` · PR: pendiente · Líneas de código y tests: 394 (límite: 400).

## Qué se hizo
- En [ProfilePage.tsx](../../../../frontend/src/auth/ProfilePage.tsx) y [ProfilePage.css](../../../../frontend/src/auth/ProfilePage.css) se habilitó la opción «Deshabilitar» del menú de acciones de `/profile` y se incorporó el flujo en dos pasos (`DisableAccountBlock`) dentro de la tarjeta principal (`RF-001`, `RF-014`, `D-08`):
  - En el paso 1 se informan las consecuencias de la baja y, si `ProfileData` indica bloqueo por empresa (`owns_company`) o por ser el último superusuario activo (`last_superuser`), se muestra un aviso `<Notice>` manteniendo inhabilitada la acción de continuar (`RF-003`, `RF-016`).
  - En el paso 2 se solicita confirmación explícita con la contraseña actual (`PasswordField` con mostrar/ocultar, validación local obligatoria, vaciado selectivo ante `current_password_incorrect` y errores generales en *toast* roja vía `useFormValidation`), manteniendo persistente la cuenta atrás de bloqueo (`disable_retry_after` al cargar `/profile` y respuestas `429`) (`RF-004`, `RF-005`, `RF-014`).
  - Al confirmarse la baja (`POST auth/account/disable` `200`), se limpian el token y los datos locales de sesión, se marca el aviso de confirmación post-baja (`markAccountDisabledNotice()`) y se redirige a `/login` (`RF-014`, `RF-015`).
  - Ante `401` o `403 terms_required` redirige a `/login` o `/terms` igual que el resto de acciones de perfil (`RF-013`).
- En [ProfilePage.test.tsx](../../../../frontend/src/auth/ProfilePage.test.tsx) se añadió la cobertura de menú habilitado, bloqueos preventivos por empresa y último superusuario, flujo completo en dos pasos, errores de campo/red, cuenta atrás persistente, redirección a `/terms` y `/login`, `es` / `pt-BR` / `en` y accesibilidad con `axe-core`.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [tasks.md](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-013 | Interfaz de deshabilitación en dos pasos desde el menú de `/profile` con bloqueos preventivos y cuenta atrás persistente | `574cd7b` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con las dependencias de frontend instaladas:
```bash
git fetch origin
```

```bash
git checkout feat/deshabilitar-cuenta-ui-perfil
```

Ejecuta los tests de perfil y accesibilidad:
```bash
pnpm --filter frontend test src/auth/ProfilePage.test.tsx src/auth/a11y.test.tsx
```
Deberías ver todas las pruebas de `ProfilePage` y `a11y` en verde.

Ejecuta toda la suite de frontend, comprobación de tipos, lint y formato:
```bash
pnpm --filter frontend test
```
Deberías ver toda la suite de frontend en verde.

```bash
pnpm --filter frontend typecheck
```
Deberías ver salida limpia sin errores de TypeScript.

```bash
pnpm lint
```
Deberías ver cero avisos de ESLint.

```bash
pnpm --filter frontend exec prettier --check .
```
Deberías ver `All matched files use Prettier code style!`.

Para probarlo en la interfaz web o escritorio, inicia sesión, abre `/profile`, pulsa el menú de tres puntos (`Acciones del perfil`) -> `Deshabilitar`, avanza al paso 2 e introduce tu contraseña actual (o prueba con un usuario propietario de una empresa preliminar para comprobar el aviso preventivo con el botón deshabilitado).

## Marco teórico
### Confirmación en dos pasos e inicialización de bloqueo desde el perfil (`RF-005`, `RF-014`)
Para evitar deshabilitaciones accidentales sin crear una ruta adicional ni perder el estado de bloqueo tras recargar la página, el primer paso resume el impacto (cierre inmediato de sesiones y ventana de 12 meses vía soporte) y bloquea preventivamente si el usuario tiene empresa o es el único superusuario activo, mientras `GET auth/profile` entrega `disable_retry_after` para que el temporizador (`useCountdown`) continúe activo aunque se recargue `/profile` o se cancele y vuelva a abrir la confirmación.
