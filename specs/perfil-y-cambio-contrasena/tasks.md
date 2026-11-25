# Tareas: perfil-y-cambio-contrasena
Estado: aprobado

- [ ] T-001 Servicio de consulta y edición parcial del perfil
  RF: RF-001, RF-002, RF-005 | Depende de: — | Archivos: 2
  Hecho cuando: `pytest apps/accounts/tests/test_profile_service.py -k profile` pasa verificando lectura, edición parcial y completa, normalización, conservación y rechazo de `"ZZ"`, historial `HistoricalRecords` y emisión de `profile_edited` solo ante cambios reales.

- [ ] T-002 Validación estricta del cuerpo de perfil y mensajes multiidioma
  RF: RF-003, RF-004, RF-013 | Depende de: T-001 | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_profile_api.py -k serializer` pasa verificando el rechazo de `email` (`email_immutable`), petición vacía (`no_profile_fields`), claves desconocidas (`unknown_field`) y reglas de campos en `es`, `pt-BR` y `en`.

- [ ] T-003 Endpoints `GET` y `PATCH` de `auth/profile` para web y escritorio
  RF: RF-001, RF-002, RF-003, RF-004, RF-011, RF-013 | Depende de: T-002 | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_profile_api.py -k profile` pasa verificando sesión por cookie (con CSRF), token de escritorio (`X-Session-Token`), bloqueo `401` por cuenta inactiva y `403 terms_required` sin términos vigentes, e idioma de respuesta.

- [ ] T-004 Subcomandos CLI `profile show` y `profile edit`
  RF: RF-015 | Depende de: T-001 | Archivos: 2
  Hecho cuando: `pytest apps/accounts/tests/test_profile_service.py -k cli_profile` pasa verificando `manage.py profile show --email ...` y `manage.py profile edit --email ...`.

- [ ] T-005 Límite configurable por cuenta ante intentos fallidos de contraseña actual
  RF: RF-008, RF-014 | Depende de: — | Archivos: 4
  Hecho cuando: `pytest apps/accounts/tests/test_profile_service.py -k throttle` pasa verificando el bloqueo tras `5` fallos en `5` minutos durante `5` minutos por defecto, su configuración por settings y el reinicio del contador al completar con éxito.
  Excepción: configuración compartida repartida entre `backend/config/settings.py` y `backend/apps/accounts/conf.py`, limitador en `backend/apps/accounts/throttling.py` y su test unitario en `test_profile_service.py`.

- [ ] T-006 Servicio de cambio de contraseña, conservación de sesión actual, cierre de otras sesiones, auditoría y avisos
  RF: RF-006, RF-007, RF-009, RF-010 | Depende de: T-005 | Archivos: 4
  Hecho cuando: `pytest apps/accounts/tests/test_profile_service.py -k password_change` pasa verificando validación de actual y nueva contraseña (incluida igual a la actual), conteo prioritario al fallar la actual, conservación de la sesión actual, revocación inmediata de las demás en `UserSession` y almacén de sesiones, auditoría de cambio y cierre, y encolado de `password_changed` siempre y `sessions_closed` solo cuando se cierran otras sesiones.
  Excepción: coordina `_skip_password_session_revocation` en `models.py`, actualización/cierre selectivo en `sessions.py` y transacción en `profile.py` junto con `test_profile_service.py` para respetar `RF-010` de `inicio-cierre-sesion`.

- [ ] T-007 Serializador de cambio de contraseña y mensajes multiidioma
  RF: RF-007, RF-013 | Depende de: T-006 | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_profile_api.py -k password_serializer` pasa verificando presencia, caracteres prohibidos y textos `current_password_incorrect` en `es`, `pt-BR` y `en`.

- [ ] T-008 Endpoints `POST` de `auth/password/change` para web y escritorio
  RF: RF-006, RF-007, RF-008, RF-009, RF-011, RF-013 | Depende de: T-007 | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_profile_api.py -k password_change` pasa verificando `200`, `400`, `429` (`Retry-After` y `retry_after`), `403 terms_required`, `401`, continuidad real de la sesión actual e invalidación inmediata `401` de otras sesiones abiertas en web y escritorio.

- [ ] T-009 Subcomando CLI `profile change-password`
  RF: RF-015 | Depende de: T-006 | Archivos: 2
  Hecho cuando: `pytest apps/accounts/tests/test_profile_service.py -k cli_password` pasa verificando `manage.py profile change-password` con entrada interactiva o argumentos y conservación opcional de `--keep-session-key`.

- [ ] T-010 Cliente HTTP `patch`, `api/profile.ts` y mapeo de errores de perfil
  RF: RF-001, RF-002, RF-003, RF-004, RF-013 | Depende de: T-003 | Archivos: 4
  Hecho cuando: `pnpm --filter frontend test src/registration/serverErrors.test.ts` pasa verificando `patch` en `ApiClient`, `getProfile`/`updateProfile` y la traducción de `email_immutable`, `unknown_field` y `no_profile_fields`.
  Excepción: añade `patch` en `client.ts` junto al módulo consumidor `api/profile.ts`, `serverErrors.ts` y `serverErrors.test.ts`.

- [ ] T-011 Helper compartido de países y traducciones de perfil en tres idiomas
  RF: RF-012, RF-013 | Depende de: — | Archivos: 5
  Hecho cuando: `pnpm --filter frontend test src/i18n/keys.test.ts src/i18n/locales/locales.test.ts src/registration/RegisterPage.test.tsx` pasa verificando las claves nuevas en `es`, `pt-BR` y `en` y el catálogo localizado compartido de países.
  Excepción: los tres archivos de idioma (`es.ts`, `pt-BR.ts`, `en.ts`) deben actualizarse juntos por `i18n/keys.test.ts`, además de extraer `forms/countries.ts` desde `RegisterPage.tsx`.

- [ ] T-012 Bloque de información personal en `ProfilePage`
  RF: RF-001, RF-002, RF-003, RF-004, RF-011, RF-012, RF-013 | Depende de: T-010, T-011 | Archivos: 3
  Hecho cuando: `pnpm --filter frontend test src/auth/ProfilePage.test.tsx` pasa verificando correo en solo lectura, estado `"ZZ"` como sin país asignado conservable al editar nombre/fecha, validación local en blur y submit, foco al primer error, mensajes por campo/confirmación, redirecciones y accesibilidad.

- [ ] T-013 Conexión de `/profile` en `App` y menú lateral privado compartido
  RF: RF-001, RF-012 | Depende de: T-012 | Archivos: 5
  Hecho cuando: `pnpm --filter frontend test src/App.test.tsx` pasa verificando el enlace a `/profile` en el menú lateral de `/` y `/profile`, el acceso autenticado, las redirecciones sin sesión o con términos pendientes y la actualización inmediata del nombre en el menú lateral tras editar el perfil.
  Excepción: conecta la navegación privada compartida (`privateNav.ts`, `icons/index.ts`, `HomePage.tsx`), el enrutador (`App.tsx`) y sus pruebas en `App.test.tsx`.

- [ ] T-014 Cliente y traducciones para cambio de contraseña en `/profile`
  RF: RF-006, RF-007, RF-008, RF-012, RF-013 | Depende de: T-008, T-010 | Archivos: 5
  Hecho cuando: `pnpm --filter frontend test src/i18n/keys.test.ts src/registration/serverErrors.test.ts` pasa verificando `changePassword` en `api/profile.ts`, el mapeo de `current_password_incorrect` y las claves en `es`, `pt-BR` y `en`.
  Excepción: los tres archivos de idioma (`es.ts`, `pt-BR.ts`, `en.ts`) deben actualizarse juntos por `i18n/keys.test.ts`, junto con `api/profile.ts` y `serverErrors.test.ts`.

- [ ] T-015 Bloque de cambio de contraseña en `ProfilePage`
  RF: RF-006, RF-007, RF-008, RF-011, RF-012, RF-013 | Depende de: T-013, T-014 | Archivos: 3
  Hecho cuando: `pnpm --filter frontend test src/auth/ProfilePage.test.tsx` pasa verificando contraseña actual y nueva contraseña única con mostrar/ocultar y lista de requisitos en vivo, validación local, vaciado selectivo tras éxito o error de actual/política/red, cuenta atrás con botón deshabilitado ante `429`, redirección ante términos pendientes o `401`, idiomas y accesibilidad.

## Entregas
Rama de integración: `feat/perfil-y-cambio-contrasena` (los PR de las entregas van contra ella; ver `AGENTS.md`).

- E-01 Consulta y edición de perfil en backend (API y consola)
  Tareas: T-001, T-002, T-003, T-004 | Líneas estimadas: 290 | Rama: `feat/perfil-y-cambio-contrasena-api-perfil`
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_profile_service.py apps/accounts/tests/test_profile_api.py`, probar `python manage.py profile show --email <EMAIL>` y `python manage.py profile edit --email <EMAIL> --name "..."` y hacer `GET`/`PATCH` con `curl` a `/api/app/v1/auth/profile` verificando que cambiar el correo se rechaza.

- E-02 Cambio de contraseña con cierre de otras sesiones en backend (API y consola)
  Tareas: T-005, T-006, T-007, T-008, T-009 | Líneas estimadas: 340 | Rama: `feat/perfil-y-cambio-contrasena-api-password`
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_profile_service.py apps/accounts/tests/test_profile_api.py`, iniciar dos sesiones con `curl` (`/api/app/v1/auth/login`), llamar a `POST /api/app/v1/auth/password/change` con una de ellas y comprobar que la sesión actual sigue devolviendo `200` en `/api/app/v1/auth/profile` mientras la otra devuelve `401`, revisando además los correos encolados y el comando `python manage.py profile change-password`.

- E-03 Pantalla `/profile` para consultar y editar datos personales en web y escritorio
  Tareas: T-010, T-011, T-012, T-013 | Líneas estimadas: 340 | Rama: `feat/perfil-y-cambio-contrasena-ui-perfil`
  Cómo probarlo: ejecutar `pnpm --filter frontend test` y entrar con sesión iniciada en el navegador a `/`, pulsar «Perfil» en el menú lateral para abrir `/profile`, verificar el correo en solo lectura y editar nombre, fecha o país comprobando que el nombre se actualiza al instante en el menú lateral.

- E-04 Formulario de cambio de contraseña en `/profile`
  Tareas: T-014, T-015 | Líneas estimadas: 250 | Rama: `feat/perfil-y-cambio-contrasena-ui-password`
  Cómo probarlo: ejecutar `pnpm --filter frontend test`, abrir `/profile` con sesión iniciada, cambiar la contraseña introduciendo la contraseña actual y la nueva, y comprobar la confirmación, el vaciado de campos y que otra sesión abierta pasa a `/login` al hacer una acción.

## RF sin tarea
ninguno
