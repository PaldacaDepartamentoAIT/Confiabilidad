# Entrega E-06b · Textos multilingües y traducción de errores de autenticación en el cliente

Rama: `feat/inicio-cierre-sesion-textos-auth` · PR: pendiente · Líneas de código y tests: 110 (límite: 400).

## Qué se hizo
- Se añadieron en `frontend/src/i18n/locales/en.ts`, `frontend/src/i18n/locales/es.ts`, `frontend/src/i18n/locales/pt-BR.ts` y `frontend/src/i18n/locales/locales.test.ts` los textos multilingües del grupo `auth` (pantallas de inicio de sesión, términos pendientes, panel principal y gestión de sesiones activas), el enlace `register.signInLink` y los cuatro textos de validación `invalidCredentials`, `tooManyLoginAttempts`, `alreadyAuthenticated` y `cannotRevokeCurrentSession` (`T-016`, `RF-013`, `RF-014`, `RF-015`, `RF-016`, `RF-019`).
- Se ampliaron `frontend/src/registration/serverErrors.ts` y `frontend/src/registration/serverErrors.test.ts` para traducir `invalid_credentials`, `too_many_login_attempts`, `already_authenticated` y `cannot_revoke_current_session` a sus claves de traducción (`T-017`, `RF-012`, `RF-014`, `RF-019`).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-016 | Textos de inicio de sesión, términos pendientes y sesiones activas en tres idiomas | `05d3537` |
| T-017 | Traducción de errores de inicio de sesión y términos en el cliente | `89bab44` |

## Cómo ejecutarlo y probarlo
Actualiza las ramas remotas y cambia a la rama de la entrega:

```bash
git fetch origin
```

```bash
git checkout feat/inicio-cierre-sesion-textos-auth
```
Deberías ver tu copia de trabajo en `feat/inicio-cierre-sesion-textos-auth`.

Ejecuta los tests de traducciones y mapeo de errores del servidor:

```bash
pnpm --filter frontend test src/i18n/locales/locales.test.ts src/registration/serverErrors.test.ts
```
Deberías ver ambos archivos de tests en verde.

Ejecuta el linter y el chequeo de tipos del frontend:

```bash
pnpm --filter frontend lint
```
Deberías ver la salida limpia sin errores.

```bash
pnpm --filter frontend typecheck
```
Deberías ver `tsc --noEmit` terminar sin errores.
