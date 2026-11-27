# Entrega E-05 · Correcciones de validación (limpieza de errores locales y cobertura de bloqueo entre sesiones)

Rama: `feat/perfil-y-cambio-contrasena-correcciones` · PR: `#160` · Líneas de código y tests: 181 (aprobado y fusionado en `#160`).

## Qué se hizo
- En `frontend/src/auth/ProfilePage.tsx` y `frontend/src/auth/ProfilePage.test.tsx` (`T-016`, `RF-012`):
  - se trasladó la clave de remonte `key={mode === "edit" ? "edit" : "view"}` al componente `PersonalInfoBlock` (retirando el `key` redundante del `<form>`) para que, al pulsar «Cancelar» o guardar tras un error de validación local, se desmonte la instancia de edición y se descarten todos los `localErrors`, `serverErrors` y mensajes previos;
  - se amplió `ProfilePage.test.tsx` para cubrir la validación al salir de un campo (`onBlur`) tanto en edición de perfil como en cambio de contraseña (considerando que `PasswordField` solo dispara `onBlur` al abandonar el input y su botón de visibilidad), así como la reapertura de «Editar» tras cancelar con errores locales comprobando que no persiste ningún error antiguo.
- En `backend/apps/accounts/tests/test_profile_service.py` y `backend/apps/accounts/tests/test_profile_api.py` (`T-017`, `RF-008`):
  - se añadieron `test_password_change_resets_failures_on_success_and_shares_across_sessions` y `test_password_change_lockout_shared_across_sessions_and_reset_on_success` con `@pytest.mark.django_db(transaction=True)` para que `transaction.on_commit` ejecute el reinicio real del contador en caché;
  - se verificó que los intentos fallidos de contraseña actual se comparten entre sesiones web (`browser`) y escritorio (`app`) de una misma cuenta, que el bloqueo `429` afecta a ambas sesiones sin cerrarlas y que completar con éxito un cambio de contraseña reinicia automáticamente el contador de fallos.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-016 | Corrección: descartar errores locales al cancelar en `PersonalInfoBlock` y cubrir `onBlur` y cancelación en `ProfilePage.test.tsx` | `007ed9e` |
| T-017 | Corrección: verificar en tests el contador compartido entre sesiones y el reinicio tras cambio de contraseña exitoso | `b02a563` |

## Cómo ejecutarlo y probarlo
En la rama de la entrega, ejecuta las comprobaciones de frontend:
```bash
pnpm --filter frontend test src/auth/ProfilePage.test.tsx
```
Deberías ver los `5` tests de `ProfilePage.test.tsx` en verde.
```bash
pnpm --filter frontend test
```
Deberías ver toda la suite de frontend (`69` archivos, `864` tests) en verde.
```bash
pnpm --filter frontend typecheck
```
Deberías ver cero errores de TypeScript.
```bash
pnpm --filter frontend lint
```
Deberías ver cero errores ni advertencias de ESLint.

En el contenedor de backend (o entorno Python del proyecto), ejecuta los tests de perfil y las comprobaciones estáticas:
```bash
docker exec confiabilidad-dev-backend-1 pytest apps/accounts/tests/test_profile_service.py apps/accounts/tests/test_profile_api.py --no-cov
```
Deberías ver `34 passed`.
```bash
docker exec confiabilidad-dev-backend-1 sh -c "ruff check . && black --check . && mypy ."
```
Deberías ver todos los checks limpios en `259` archivos.

Para comprobarlo manualmente en la interfaz (`/profile`):
1. Entra en `/profile`, abre el menú vertical de tres puntos y pulsa «Editar».
2. Borra el «Nombre completo» y sal del campo (`Tab`) para ver el error local «Completa este campo.» sin enviar el formulario.
3. Pulsa «Cancelar», vuelve a abrir el menú de tres puntos y elige «Editar»: el nombre vuelve a su valor guardado y no reaparece el error anterior.
