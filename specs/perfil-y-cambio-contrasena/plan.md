# Plan: perfil-y-cambio-contrasena
Estado: aprobado

## Módulos

### M-01 Servicio de perfil y cambio de contraseña (`backend/apps/accounts/profile.py`, `models.py`, `sessions.py`, `conf.py`, `throttling.py`, `config/settings.py`)
Responsabilidad:
- `get_profile(user)` y `update_profile(user, *, name=..., birthdate=..., country=...)`: lee y actualiza parcialmente o por completo `name`, `birthdate` y `country` aplicando normalización y validaciones de `usuario-personalizado` (conservando `"ZZ"` si el país no cambia), guarda en `User` (registrando historial en `HistoricalRecords`) y emite `signals.profile_edited` únicamente cuando algún campo normalizado cambia efectivamente.
- `change_password(user, *, current_password, new_password, current_session_key=None, request=None)`: verifica bloqueo por intentos fallidos por cuenta en caché (`throttling.py`, configurado en `conf.py` y `settings.py` con valores por defecto `5` intentos / `5` minutos / `5` minutos), comprueba la contraseña actual (contabilizando cualquier fallo incluso si `new_password` también es inválida o falta), valida la nueva contraseña con la política vigente (`validate_password`), actualiza la contraseña dentro de `transaction.atomic()`, preserva la sesión actual actualizando su `HASH_SESSION_KEY` (y rotando la clave de sesión en web mediante `sessions.refresh_current_session` para mantener `UserSession` sincronizada, sin cambiar el `X-Session-Token` del cliente de escritorio), revoca de inmediato el resto de sesiones mediante `sessions.revoke_all_other_sessions`, emite auditoría de cambio de contraseña y de cierre por cada sesión revocada, y encola en `outbox` `password_changed` siempre y `sessions_closed` si se cerró al menos otra sesión, en el idioma guardado del usuario.
RF: RF-001, RF-002, RF-005, RF-006, RF-007, RF-008, RF-009, RF-010, RF-014

### M-02 API de perfil y cambio de contraseña (`backend/apps/accounts/api/profile_serializers.py`, `profile_views.py`, `urls.py`, `messages.py`)
Responsabilidad:
- Exponer `AppProfileView` / `BrowserProfileView` (`GET` y `PATCH` en `app/v1/auth/profile` y `browser/v1/auth/profile`) y `AppPasswordChangeView` / `BrowserPasswordChangeView` (`POST` en `app/v1/auth/password/change` y `browser/v1/auth/password/change`), exigiendo sesión válida y términos vigentes aceptados (`_require_auth(..., require_terms=True)`), protección CSRF en `browser` (`_BrowserCsrfMixin`) y exención en `app` (`X-Session-Token`).
- `ProfileUpdateSerializer`: valida actualización parcial exigiendo al menos uno de `{name, birthdate, country}`, rechazando explícitamente `email` (`email_immutable`) y claves desconocidas (`unknown_field`), y validando `name`, `birthdate` y `country`.
- `PasswordChangeSerializer`: valida presencia y ausencia de caracteres prohibidos en `current_password` y `new_password`; devuelve errores por campo con códigos estables (`current_password_incorrect`, códigos de política de contraseñas) o `429` (`Retry-After` y `retry_after`) ante bloqueo temporal.
- Traducir todos los códigos nuevos en `messages.py` a `es`, `pt-BR` y `en`.
RF: RF-001, RF-002, RF-003, RF-004, RF-006, RF-007, RF-008, RF-011, RF-013

### M-03 Comando de consola de perfil (`backend/apps/accounts/management/commands/profile.py`)
Responsabilidad:
- Subcomandos `show --email ...`, `edit --email ... [--name ...] [--birthdate ...] [--country ...]` y `change-password --email ... [--current-password ...] [--new-password ...] [--keep-session-key ...]` (solicitando contraseñas sin eco con `getpass` si se omiten) para ejecutar y verificar desde CLI el perfil, el cambio de contraseña, el cierre de otras sesiones y la conservación opcional de la sesión indicada.
RF: RF-015

### M-04 Cliente API, validadores compartidos e i18n frontend (`frontend/src/api/client.ts`, `api/profile.ts`, `forms/countries.ts`, `registration/serverErrors.ts`, `i18n/locales/*.json`)
Responsabilidad:
- Añadir `patch` a `ApiClient` (`client.ts`) y crear `api/profile.ts` con `getProfile`, `updateProfile` y `changePassword`.
- Extraer la ordenación/localización de países (`Intl.DisplayNames`) a `forms/countries.ts` para reutilizarla entre registro y perfil.
- Mapear en `serverErrors.ts` los nuevos códigos del servidor (`email_immutable`, `unknown_field`, `no_profile_fields`, `current_password_incorrect`) y añadir traducciones completas en `es`, `pt-BR` y `en`.
RF: RF-001, RF-002, RF-003, RF-004, RF-006, RF-007, RF-008, RF-012, RF-013

### M-05 Pantalla `/profile` y navegación del área privada (`frontend/src/auth/ProfilePage.tsx`, `ProfilePage.css`, `privateNav.ts`, `HomePage.tsx`, `App.tsx`, `icons/index.ts`)
Responsabilidad:
- Registrar la ruta `/profile` en `App.tsx` dentro de `AppLayout` (con las mismas redirecciones de sesión/términos que `/`) y añadir el enlace «Perfil» en el menú lateral compartido (`privateNav.ts`) usado por `HomePage` y `ProfilePage`.
- Construir `ProfilePage.tsx` siguiendo `docs/identidad-visual.md` con dos bloques independientes:
  1. **Información personal**: correo electrónico en solo lectura (`readOnly`), `name`, `birthdate` y `country` (mostrando estado sin seleccionar «Sin país asignado» cuando el valor almacenado es `"ZZ"` y conservándolo si no se elige un país nuevo).
  2. **Cambio de contraseña**: `current_password` y `new_password` (un solo campo con mostrar/ocultar y lista de requisitos en vivo, sin confirmación adicional).
- Validación local al salir de campo y al enviar, foco al primer campo con error, confirmación al guardar cada bloque, vaciado selectivo en contraseña (ambos al éxito, solo `current_password` al fallar esta, ambos conservados en error de política/red) y cuenta atrás con bloqueo de envío (`useCountdown`) ante `429`. Propagar el `name` actualizado al estado de sesión en `App.tsx`.
RF: RF-001, RF-002, RF-003, RF-004, RF-006, RF-007, RF-008, RF-011, RF-012, RF-013

## Modelo de datos
No se requieren nuevas tablas, campos ni migraciones en base de datos:
- Los datos del perfil (`email`, `name`, `birthdate`, `country`, `password`, `language`, `is_active`) y su historial (`HistoricalRecords`) ya existen en `apps.accounts.models.User`.
- El inventario de sesiones (`UserSession`), los eventos de auditoría (`SecurityEvent`) y la bandeja de correo (`OutboundEmail` con tipos `password_changed` y `sessions_closed`) ya existen.
- Los contadores de fallos y bloqueo temporal de contraseña actual se almacenan en la caché (`django.core.cache`) por identificador de cuenta (`user.pk`), con TTL igual a la ventana/bloqueo configurados.

## Decisiones

### D-01 Conservación de la sesión actual frente a `User.save()`
Elegida: Mantener el comportamiento de `User._revoke_sessions_on_change()` para cambios externos de contraseña (restablecimiento olvidado, admin o guardado directo del modelo) e introducir un atributo transitorio no persistido en `User` (`_skip_password_session_revocation`, análogo a `skip_history_when_saving`) usado únicamente dentro de `profile.change_password`. Dicho servicio actualiza la sesión actual (`sessions.refresh_current_session`: rota la clave en web actualizando cookie, `UserSession` y clave inversa; y actualiza `HASH_SESSION_KEY` en el almacén para `app` manteniendo el mismo `X-Session-Token`) y revoca el resto mediante `sessions.revoke_all_other_sessions`.
Descartada: Modificar `inicio-cierre-sesion` (`RF-010`) para que `User.save()` deje de revocar sesiones o emitir un nuevo `session_token` en `app`.
Motivo: Respeta sin regresiones `RF-010` de `inicio-cierre-sesion` y evita cambiar otra spec (`AGENTS.md`), protege contra fijación de sesión en navegador y mantiene el token de escritorio válido sin cambios en `tokenStorage`.

### D-02 Límite de intentos fallidos de contraseña actual por cuenta en caché
Elegida: Añadir en `throttling.py` un limitador por `user.pk` con marcas de tiempo en ventana móvil (`PASSWORD_CHANGE_ATTEMPT_WINDOW_MINUTES`, por defecto `5`) y bloqueo temporal (`PASSWORD_CHANGE_LOCKOUT_MINUTES`, por defecto `5`) al alcanzar `PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS` (por defecto `5`), verificando el bloqueo antes de comprobar contraseñas, registrando cada fallo de contraseña actual (aunque `new_password` falte o sea inválida) y limpiando el estado al completar un cambio con éxito.
Descartada: Reutilizar el rate limit `login_failed` de allauth o añadir columnas en `User`.
Motivo: Evita acoplar el bloqueo del perfil con el del inicio de sesión y no requiere migraciones de esquema ni tabla adicional.

### D-03 Contratos duales `auth/profile` (`GET`/`PATCH`) y `auth/password/change` (`POST`)
Elegida: Crear endpoints dedicados `/api/{browser,app}/v1/auth/profile` (`GET`, `PATCH`) y `/api/{browser,app}/v1/auth/password/change` (`POST`), con `_require_auth(..., require_terms=True)` y `_BrowserCsrfMixin` para navegador.
Descartada: Mezclar edición de perfil en `auth/session` o usar `PUT` obligando a enviar siempre todos los campos.
Motivo: Mantiene `auth/session` acotado al estado de sesión y términos (`inicio-cierre-sesion`), soporta actualización parcial por `PATCH` (`C-03`, `S-08`) y aísla el endpoint sujeto a bloqueo por contraseña actual.

### D-04 Validación estricta del cuerpo en `PATCH auth/profile` y auditoría solo si hay cambios reales
Elegida: Inspeccionar las claves del objeto JSON recibido (ignorando únicamente `language`, usado por `_body_language` como en el resto de endpoints): rechazar `email` (`email_immutable`), cualquier otra clave desconocida (`unknown_field`) y el cuerpo sin ninguno de `{name, birthdate, country}` (`no_profile_fields`). Comparar los valores normalizados frente a los almacenados para guardar en `User` y emitir `signals.profile_edited` solo si al menos un campo cambió.
Descartada: Permitir claves extra ignoradas o registrar `profile_edited` y una versión histórica en cada `PATCH` sin cambios reales.
Motivo: Cumple `RF-003`, `RF-004`, `RF-005` y `C-03`, evitando ruido en `HistoricalRecords` y en `SecurityEvent`.

### D-05 Manejo del país relleno `"ZZ"` en API y UI
Elegida: `GET auth/profile` devuelve el valor real almacenado en `User.country` (incluyendo `"ZZ"` si la cuenta lo conserva). En `ProfilePage.tsx`, `"ZZ"` se representa en el selector de país como opción inicial vacía / «Sin país asignado»; si el usuario guarda cambios de nombre o fecha sin elegir un país oficial, la petición omite `country` (o conserva `"ZZ"`), manteniéndolo válido según `RF-005` de `usuario-personalizado`.
Descartada: Ocultar `"ZZ"` devolviendo vacío en la API o exigir elegir un país antes de guardar cualquier cambio de perfil en pantalla.
Motivo: Mantiene fidelidad entre el modelo y la API y respeta la excepción de `"ZZ"` (`C-02`).

### D-06 Auditoría y correos al cambiar la contraseña
Elegida: Dentro de la transacción confirmada de `profile.change_password`, emitir `allauth.account.signals.password_changed` (que `apps/audit/receivers.py` ya convierte en `EventType.PASSWORD_CHANGE`), revocar las demás sesiones con `sessions.revoke_all_other_sessions` (que emite `user_logged_out` -> `EventType.LOGOUT` por cada otra sesión activa) y encolar en `outbox` `password_changed` siempre más `sessions_closed` únicamente si `revoked_count > 0`, en `user.language`.
Descartada: Añadir señales nuevas duplicadas o enviar correos fuera de la transacción.
Motivo: Reutiliza receptores y outbox transaccional existentes (`RF-003` de `correo-asincrono-plantillas`, `RF-010` de `auditoria-eventos-seguridad`).

### D-07 Catálogo de países y diseño visual de `/profile`
Elegida: Reutilizar `registration/options` (`fetchOptions`) junto con `Intl.DisplayNames` en un helper compartido (`forms/countries.ts`) para el selector de países, y maquetar `ProfilePage.tsx` con los componentes del sistema de diseño (`AppLayout`, `Block`, `TextField`, `SelectField`, `PasswordField`, `Button`, `FormMessage`, `RequiredLegend`) y las reglas de `docs/identidad-visual.md`.
Descartada: Duplicar el listado ISO 3166-1 en frontend o crear controles fuera de `components/`.
Motivo: Única fuente de verdad para códigos ISO válidos y cumplimiento estricto de `docs/identidad-visual.md` y WCAG 2.2 AA.

### D-08 Navegación lateral compartida y actualización del nombre en sesión
Elegida: Extraer la configuración de ítems del menú lateral privado (`/` y `/profile`) a `privateNav.ts`, registrar `/profile` en `App.tsx` dentro de `AppLayout` (no `PublicLayout`) y actualizar `session.user.name` en el estado raíz tras guardar el perfil para reflejar al instante el nombre y las iniciales en el menú lateral.
Descartada: Recargar la página o hacer un `getSession` extra tras actualizar el perfil.
Motivo: Respuesta inmediata en la interfaz y mantenimiento sencillo sin duplicar la navegación lateral.

## Estrategia de tests
- **Unitarios y de servicio (backend, `pytest`)**:
  - `apps/accounts/tests/test_profile_service.py`: lectura y actualización parcial/completa (`RF-001`, `RF-002`), normalización, conservación de `"ZZ"` mientras no cambie, rechazo de `"ZZ"` si el usuario ya tenía país oficial, historial `HistoricalRecords`, no-op sin auditoría (`RF-005`), cambio de contraseña válido e igual a la actual (`RF-006`), rechazo por actual incorrecta o política inválida con prioridad de conteo (`RF-007`), bloqueo por cuenta `5/5m/5m` y reinicio al acertar (`RF-008`, `RF-014`), preservación de sesión actual web/app y revocación de todas las demás (`RF-009`), auditoría y encolado condicional de `password_changed` y `sessions_closed` (`RF-010`), y subcomandos CLI (`RF-015`).
- **Integración API (backend, `pytest`)**:
  - `apps/accounts/tests/test_profile_api.py`: `GET`/`PATCH auth/profile` y `POST auth/password/change` en rutas `browser/v1` (cookie + CSRF obligatorio) y `app/v1` (`X-Session-Token`, exento de CSRF), inmutabilidad de `email` (`RF-003`), rechazo de payload vacío y campos desconocidos (`RF-004`), bloqueo `401` con cuenta inactiva y `403 terms_required` sin términos vigentes (`RF-011`), `429` con `Retry-After` (`RF-008`), continuidad real de la sesión actual e invalidación inmediata `401` de las otras sesiones en ambos clientes (`RF-009`), e idiomas `es`/`pt-BR`/`en` (`RF-013`).
- **Unitarios y de componente (frontend, Vitest + Testing Library + axe)**:
  - `frontend/src/auth/ProfilePage.test.tsx` y actualización de `frontend/src/App.test.tsx`: enlace en menú lateral, redirecciones `/profile` ↔ `/login` y `/terms` (`RF-011`, `RF-012`), lectura de correo en solo lectura, estado `"ZZ"` como sin país asignado conservable al editar nombre/fecha, validación local en blur y submit, foco al primer error, errores de servidor por campo, actualización de nombre reflejada en el menú lateral, vaciado selectivo de campos de contraseña, cuenta atrás con botón deshabilitado ante `429`, idiomas `es`/`pt-BR`/`en` y chequeo de accesibilidad (`axe`) (`RF-012`, `RF-013`).

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-02, M-04, M-05 | Unitario + Integración API + Frontend |
| RF-002 | M-01, M-02, M-04, M-05 | Unitario + Integración API + Frontend |
| RF-003 | M-02, M-04, M-05 | Integración API + Frontend |
| RF-004 | M-02, M-04, M-05 | Integración API + Frontend |
| RF-005 | M-01 | Unitario + Integración API |
| RF-006 | M-01, M-02, M-04, M-05 | Unitario + Integración API + Frontend |
| RF-007 | M-01, M-02, M-04, M-05 | Unitario + Integración API + Frontend |
| RF-008 | M-01, M-02, M-04, M-05 | Unitario + Integración API + Frontend |
| RF-009 | M-01 | Unitario + Integración API |
| RF-010 | M-01 | Unitario + Integración API |
| RF-011 | M-02, M-05 | Integración API + Frontend |
| RF-012 | M-04, M-05 | Frontend (componente + rutas + axe) |
| RF-013 | M-02, M-04, M-05 | Integración API + Frontend |
| RF-014 | M-01 | Unitario + Integración API |
| RF-015 | M-03 | Unitario (CLI `call_command`) |

## RF sin cobertura
ninguno
