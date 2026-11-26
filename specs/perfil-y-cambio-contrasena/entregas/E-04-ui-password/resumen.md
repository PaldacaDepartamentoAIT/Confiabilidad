# Entrega E-04 · Formulario de cambio de contraseña en `/profile`

Rama: `feat/perfil-y-cambio-contrasena-ui-password` · Líneas de código y tests: 444 (límite con excepción justificada en `tasks.md`: 500).

## Qué se hizo
- En `frontend/src/api/profile.ts`, `frontend/src/registration/serverErrors.ts`, `frontend/src/registration/serverErrors.test.ts` y `frontend/src/i18n/locales/{en,es,pt-BR}.ts` (`T-014`, `RF-006`…`RF-008`, `RF-013`) se añadió `changePassword` (`POST /auth/password/change`), la traducción de `current_password_incorrect` y las claves de interfaz y notificación en español, portugués de Brasil e inglés.
- En `frontend/src/auth/ProfilePage.tsx`, `frontend/src/auth/ProfilePage.css` y `frontend/src/auth/ProfilePage.test.tsx` (`T-015`, `RF-006`…`RF-008`, `RF-011`…`RF-013`):
  - se habilitó «Cambiar contraseña» en el menú vertical de tres puntos de la tarjeta de perfil (manteniendo «Deshabilitar» deshabilitada hasta su propia feature);
  - al seleccionarla, la tarjeta pasa al modo `password` con `PasswordChangeBlock`, mostrando `Contraseña actual` (`kind="current"`) y `Nueva contraseña` (`kind="new"`, con botón de mostrar/ocultar y pista de requisitos coherente con `registro-flujo`) en `.profile-password-grid` (dos columnas en escritorio y una en móvil), más «Cancelar» y el botón de envío;
  - se extrajeron los helpers compartidos `fieldResult`, `handleFailure` y `useErrorText` para reutilizar la traducción de errores, el foco al primer error y las redirecciones ante `401` o `terms_required`;
  - se aplicó el vaciado selectivo: ambos campos se limpian al completar con éxito (volviendo a solo lectura con notificación flotante *toast*), solo `current_password` se limpia si falla la contraseña actual, ambos se conservan ante errores de política o red/servidor y se descartan al pulsar «Cancelar» o cambiar de modo;
  - ante `429` (`rateLimited`) se muestra la cuenta atrás (`useCountdown`) y se deshabilita el botón de envío hasta llegar a cero;
  - se ampliaron las pruebas de `ProfilePage.test.tsx` cubriendo cambio desde el menú, `axe-core`, validación local, vaciado selectivo, notificación *toast*, `429`, errores de red, «Cancelar», redirección por términos e idioma inglés.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-014 | Cliente y traducciones para cambio de contraseña en `/profile` | `248bb47` |
| T-015 | Modo de cambio de contraseña en `ProfilePage` desde el menú contextual | `dab7391`, `3b2fa16` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con las dependencias de frontend instaladas, actualiza ramas y pasa a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/perfil-y-cambio-contrasena-ui-password
```
```bash
git pull origin feat/perfil-y-cambio-contrasena-ui-password
```
Ejecuta los tests, comprobación de tipos, ESLint y Prettier:
```bash
pnpm --filter frontend test
```
Deberías ver toda la suite de frontend (`ProfilePage.test.tsx`, `serverErrors.test.ts`, `keys.test.ts`, `locales.test.ts`, etc.) en verde.
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

Para probarlo manualmente de extremo a extremo con el stack levantado (y con dos sesiones abiertas, por ejemplo navegador normal + ventana privada):
1. Inicia sesión en `/profile` y verifica que en `/` (Panel principal) aparecen ambas sesiones activas.
2. En una de las sesiones ve a `/profile`, pulsa el botón de tres puntos verticales y elige «Cambiar contraseña».
3. Prueba enviar una nueva contraseña corta o numérica para verificar la validación local sin llamada al servidor.
4. Introduce una contraseña actual incorrecta junto a una nueva válida y comprueba que se vacía solo «Contraseña actual» conservando la nueva; repite 5 veces seguidas si quieres comprobar el bloqueo temporal `429` con cuenta atrás.
5. Introduce la contraseña actual correcta y una nueva válida y pulsa «Cambiar contraseña»: verifica que vuelve a la vista de solo lectura, aparece la notificación flotante inferior derecha y que en la otra sesión abierta cualquier acción o recarga pasa a `/login`, mientras la sesión actual sigue autenticada.
