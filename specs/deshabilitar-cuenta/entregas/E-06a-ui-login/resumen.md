# Entrega E-06a · Cliente API, traducciones y avisos de cuenta deshabilitada en `/login`

Rama: `feat/deshabilitar-cuenta-ui-login` · PR: pendiente · Líneas de código y tests: 149 (límite: 400).

## Qué se hizo
- En [profile.ts](../../../../frontend/src/api/profile.ts) se añadió `disableAccount(client, { current_password })`, se amplió `ProfileData` con los campos opcionales de elegibilidad (`can_disable`, `disable_block_reason`, `disable_retry_after`) y se añadieron `markAccountDisabledNotice` y `consumeAccountDisabledNotice` sobre `sessionStorage` (`RF-001`, `RF-014`, `RF-015`).
- En [serverErrors.ts](../../../../frontend/src/registration/serverErrors.ts), [en.ts](../../../../frontend/src/i18n/locales/en.ts), [es.ts](../../../../frontend/src/i18n/locales/es.ts) y [pt-BR.ts](../../../../frontend/src/i18n/locales/pt-BR.ts) se añadieron las traducciones y mapeos en los tres idiomas para `owns_company`, `last_superuser`, `account_disabled`, `account_disabled_expired` y los textos del flujo de deshabilitación y confirmación (`RF-008`, `RF-014`).
- En [LoginPage.tsx](../../../../frontend/src/auth/LoginPage.tsx) se mostró el aviso informativo de confirmación post-baja (`auth.accountDisabledNotice`) al llegar tras deshabilitar una cuenta (limpiándose al intentar un nuevo acceso) junto con la traducción de `account_disabled` y `account_disabled_expired` (`RF-008`, `RF-014`).
- En [serverErrors.test.ts](../../../../frontend/src/registration/serverErrors.test.ts) y [LoginPage.test.tsx](../../../../frontend/src/auth/LoginPage.test.tsx) se añadieron pruebas de mapeo de códigos, confirmación post-baja y errores de cuenta deshabilitada en los tres idiomas.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [tasks.md](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-011 | Cliente `disableAccount`, `ProfileData` ampliado y traducciones en `es`, `pt-BR` y `en` | `8ad81d5` |
| T-012 | Mensajes específicos de cuenta deshabilitada y confirmación post-baja en `LoginPage` | `c37271b` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con las dependencias de frontend instaladas:
```bash
git fetch origin
```
```bash
git checkout feat/deshabilitar-cuenta-ui-login
```
Ejecuta los tests de frontend de esta entrega:
```bash
pnpm --filter frontend test src/auth/LoginPage.test.tsx src/registration/serverErrors.test.ts src/i18n/keys.test.ts src/i18n/locales/locales.test.ts
```
Deberías ver todas las suites de login, errores e idiomas en verde.

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

Para probarlo en el navegador tras levantar backend y frontend, intenta iniciar sesión en `/login` con una cuenta deshabilitada (usando su contraseña correcta): verás el mensaje específico sobre la reactivación con soporte durante 12 meses (o el aviso de plazo vencido si superó los 12 meses).

## Marco teórico
### Aviso único post-baja con `sessionStorage` (`RF-014`)
Para mostrar en `/login` la confirmación de que la cuenta quedó deshabilitada tras redirigir desde `/profile` sin dejar parámetros permanentes en la URL ni volver a mostrar el aviso al recargar, el origen escribe una marca efímera en `sessionStorage` y `LoginPage` la consume una sola vez al montarse (`consumeAccountDisabledNotice`).
