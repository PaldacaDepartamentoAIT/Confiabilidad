# Entrega E-03b · Edición parcial de datos personales y menú de tarjeta en `/profile`

Rama: `feat/perfil-y-cambio-contrasena-ui-perfil-edicion` · Líneas de código y tests: 1160 (supera el límite de 500 líneas de `sdd.max_lineas_pr_excepcion` por añadir la tarjeta a ancho completo, el límite de altura en `Menu`, el menú contextual de tres puntos y el componente reutilizable de notificaciones flotantes en esta misma entrega; pendiente de confirmación del usuario para aceptarlo en un único PR o dividirlo).

## Qué se hizo
- En `frontend/src/api/client.ts`, `frontend/src/api/profile.ts`, `frontend/src/registration/serverErrors.ts`, `frontend/src/registration/serverErrors.test.ts`, `frontend/src/api/auth.test.ts` y `frontend/src/api/registration.test.ts` (`T-010b`, `RF-002`…`RF-004`, `RF-013`) se añadió `patch` al `ApiClient` compartiendo `jsonSend` con `post`, `updateProfile` (`PATCH /auth/profile`) y la traducción de `email_immutable`, `unknown_field` y `no_profile_fields`.
- En `frontend/src/icons/index.ts`, `frontend/src/icons/icons.test.tsx`, `frontend/src/components/menu/Menu.tsx`, `frontend/src/components/menu/Menu.css`, `frontend/src/components/menu/Menu.test.tsx`, `frontend/src/components/fields/Field.css` y `frontend/src/i18n/locales/{en,es,pt-BR}.ts` (`T-012b`):
  - se añadieron `IconMoreVertical` e `IconX`;
  - se incorporó en `Menu` el soporte de opciones `disabled` (`aria-disabled="true"`), la reducción del alto máximo del desplegable a 200 px y el ajuste automático al espacio de la ventana (volteando hacia arriba cuando falta hueco abajo para no alargar la página);
  - se añadió el estilo estándar `.field:disabled` en `Field.css` (fondo con gris mezclado, borde neutro, texto secundario y cursor `not-allowed`) conforme a `docs/identidad-visual.md`.
- En `frontend/src/components/toast/toastContext.ts`, `frontend/src/components/toast/ToastProvider.tsx`, `frontend/src/components/toast/Toast.css` y `frontend/src/components/toast/ToastProvider.test.tsx` (`T-012b`) se creó el componente reutilizable de notificaciones flotantes (`ToastProvider` + `useToast`):
  - se muestra en la esquina inferior derecha respetando la estética plana y el borde izquierdo de `docs/identidad-visual.md`;
  - entra de derecha a izquierda y sale de izquierda a derecha;
  - expira tras 5 s por defecto, reinicia el plazo al situar el cursor encima (o tomar el foco) y dispone de un botón «×» para cerrarlo al instante.
- En `frontend/src/auth/ProfilePage.tsx`, `frontend/src/auth/ProfilePage.css` y `frontend/src/auth/ProfilePage.test.tsx` (`T-012b`, `RF-002`…`RF-004`, `RF-011`…`RF-013`) se actualizó la tarjeta de información personal dentro del `Block` con *skeletons* de carga (`ProfileSkeleton`):
  - ocupa todo el ancho disponible de la vista, con `Correo electrónico` siempre deshabilitado (`disabled`) arriba a ancho completo y debajo `Nombre completo`, `País` y `Fecha de nacimiento` en una sola fila de tres columnas que abarca todo el ancho en escritorio (y se apila en móvil);
  - arranca en modo solo lectura con un botón de tres puntos verticales (`IconMoreVertical`) en la esquina superior derecha que despliega «Editar», «Cambiar contraseña» (deshabilitada) y «Deshabilitar» (deshabilitada);
  - al elegir «Editar» cambia a modo edición con «Cancelar» y «Guardar cambios»;
  - muestra «Sin país asignado» cuando está en `"ZZ"` y omite `country` del `PATCH` mientras siga sin seleccionarse (`C-02`), exigiéndolo una vez asignado;
  - valida en `blur` y al enviar con `useFormValidation`, sustituye el aviso inline de éxito por la notificación flotante con `useToast` y actualiza al instante `ProfilePage`, `UserProvider` y `App`.
- En `frontend/src/App.tsx` y `frontend/src/App.test.tsx` (`T-012b`) se montó `ToastProvider` en la raíz de la aplicación, se conectó `onProfileUpdated` y se verificó que abrir «Editar» desde el menú de tres puntos y guardar el nombre muestra la notificación y actualiza en vivo el botón de usuario de la barra lateral.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-010b | Cliente HTTP `patch`, `updateProfile` y mapeo de errores de edición | `41ec34f` |
| T-012b | Edición parcial, tarjeta a ancho completo, correo deshabilitado, fila de tres columnas, control de altura en `Menu`, notificaciones flotantes y sincronización lateral | `1ed9ec9`, `2d95604`, `1548ac7`, `4308632`, `6e970cf`, `25d12ca`, `2665653` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con las dependencias de frontend instaladas, actualiza ramas y pasa a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/perfil-y-cambio-contrasena-ui-perfil-edicion
```
```bash
git pull origin feat/perfil-y-cambio-contrasena-ui-perfil-edicion
```
Ejecuta los tests, comprobación de tipos, ESLint y Prettier:
```bash
pnpm --filter frontend test
```
Deberías ver toda la suite de frontend (`ProfilePage.test.tsx`, `ToastProvider.test.tsx`, `Menu.test.tsx`, `App.test.tsx`, etc.) en verde.
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
2. Comprueba que el correo tiene aspecto deshabilitado (`not-allowed`, fondo gris sutil) tanto en solo lectura como al editar, y que `Nombre completo`, `País` y `Fecha de nacimiento` aparecen debajo en una sola fila abarcando todo el ancho.
3. Pulsa el botón de tres puntos y comprueba «Editar», «Cambiar contraseña» (deshabilitada) y «Deshabilitar» (deshabilitada).
4. Pulsa «Editar», despliega «País» y comprueba que el menú no alarga la altura de la página.
5. Modifica el nombre y pulsa «Guardar cambios»: verifica que la notificación flotante entra desde la derecha en la esquina inferior derecha, permanece visible mientras dejes el cursor encima, reinicia su cuenta atrás al retirar el cursor y puede cerrarse al instante con el botón «×».
6. Prueba enviar el nombre vacío o con dos espacios seguidos para comprobar la validación local y la del servidor con foco en el campo.
