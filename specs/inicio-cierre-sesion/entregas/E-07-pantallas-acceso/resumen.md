# Entrega E-07 · Pantalla de inicio de sesión

Rama: `feat/inicio-cierre-sesion-pantallas-acceso` · PR: pendiente · Líneas de código y tests: 301 (límite: 400).

## Qué se hizo
- Se creó `frontend/src/auth/LoginPage.tsx` con `PublicLayout`, `PublicPage`, `TextField` (`type="email"`, `autoComplete="email"`), `PasswordField` (`kind="current"`), botón de envío con estado de carga, cuenta atrás ante `429` (`useCountdown`) y enlace a `/register` (`T-018`, `RF-013`, `RF-014`, `RF-017`, `RF-019`).
  - Valida al salir del campo y al enviar que correo y contraseña no estén vacíos y que el correo tenga forma de dirección (`useFormValidation`), enfocando el primer campo con error sin llamar al servidor.
  - Ante `invalid_credentials`, muestra el error general, conserva el correo escrito y vacía el campo de contraseña (`RF-014`).
  - Ante `too_many_login_attempts`, error de red o fallo del servidor, muestra el mensaje general conservando los valores.
  - Al autenticar con éxito, notifica `onAuthenticated` y navega a `/` (si `terms_status === "accepted"`) o a `/terms`.
- Se añadieron los tests `frontend/src/auth/LoginPage.test.tsx` (`CF-7`).
- Se separó `T-019` (`TermsPage`) a `E-07b` (`feat/inicio-cierre-sesion-pantalla-terminos`) para mantener cada PR por debajo de 400 líneas.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-018 | Pantalla de inicio de sesión (sin ruta) | `043803c` |

## Cómo ejecutarlo y probarlo
Actualiza las ramas remotas y cambia a la rama de la entrega:

```bash
git fetch origin
```

```bash
git checkout feat/inicio-cierre-sesion-pantallas-acceso
```
Deberías ver tu copia de trabajo en `feat/inicio-cierre-sesion-pantallas-acceso`.

Ejecuta los tests de la pantalla de inicio de sesión:

```bash
pnpm --filter frontend test src/auth/LoginPage.test.tsx
```
Deberías ver los 4 tests de `LoginPage.test.tsx` en verde.

Ejecuta el linter y el chequeo de tipos del frontend:

```bash
pnpm --filter frontend lint
```
Deberías ver la salida limpia sin errores.

```bash
pnpm --filter frontend typecheck
```
Deberías ver `tsc --noEmit` terminar sin errores.
