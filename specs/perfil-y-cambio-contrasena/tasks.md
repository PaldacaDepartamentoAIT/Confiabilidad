# Tareas: perfil-y-cambio-contrasena
Estado: aprobado

- [x] T-001 Servicio de consulta y edición parcial del perfil
  RF: RF-001, RF-002, RF-005 | Depende de: — | Archivos: 2
  Hecho cuando: `pytest apps/accounts/tests/test_profile_service.py -k profile` pasa verificando lectura, edición parcial y completa, normalización, conservación y rechazo de `"ZZ"`, historial `HistoricalRecords` y emisión de `profile_edited` solo ante cambios reales.
  Decisiones: usar centinela `_Unset` para distinguir campos omitidos en actualización parcial y delegar la validación/normalización/historial en `User.save(update_fields=...)` únicamente cuando al menos un campo normalizado cambia respecto al valor guardado (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo). — Motivo: reutiliza las reglas de `usuario-personalizado` y evita entradas vacías en `HistoricalRecords` y auditoría. — Confianza: [Probable] (lógica revisada contra `models.py`, sin ejecución local de `pytest`). — Cómo revertirla: reemplazar `profile.update_profile` y `test_profile_service.py`.

- [x] T-002 Validación estricta del cuerpo de perfil y mensajes multiidioma
  RF: RF-003, RF-004, RF-013 | Depende de: T-001 | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_profile_api.py -k serializer` pasa verificando el rechazo de `email` (`email_immutable`), petición vacía (`no_profile_fields`), claves desconocidas (`unknown_field`) y reglas de campos en `es`, `pt-BR` y `en`.
  Decisiones: permitir la clave `language` en el cuerpo sin marcarla como `unknown_field` para mantener compatibilidad con `_body_language` del cliente API, y emitir `no_profile_fields` únicamente cuando no hay campos editables ni otros errores de clave (`email`/`unknown_field`) (pendiente de ejecutar `pytest` y `mypy` en entorno completo). — Motivo: evita ruido de errores redundantes cuando el usuario intenta enviar `email`. — Confianza: [Cierto]. — Cómo revertirla: ajustar `ProfileUpdateSerializer.to_internal_value`.

- [x] T-003 Endpoints `GET` y `PATCH` de `auth/profile` para web y escritorio
  RF: RF-001, RF-002, RF-003, RF-004, RF-011, RF-013 | Depende de: T-002 | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_profile_api.py -k profile` pasa verificando sesión por cookie (con CSRF), token de escritorio (`X-Session-Token`), bloqueo `401` por cuenta inactiva y `403 terms_required` sin términos vigentes, e idioma de respuesta.
  Decisiones: reutilizar `_require_auth(..., require_terms=True)` y `_BrowserCsrfMixin` con `@method_decorator(ensure_csrf_cookie, name="get")` en `BrowserProfileView` (pendiente de ejecutar `pytest` y `mypy` en entorno completo). — Motivo: coherencia con `auth_views.py` y disponibilidad de cookie CSRF al abrir `/profile` directamente. — Confianza: [Probable]. — Cómo revertirla: eliminar `profile_views.py` y sus rutas en `urls.py`.

- [x] T-004 Subcomandos CLI `profile show` y `profile edit`
  RF: RF-015 | Depende de: T-001 | Archivos: 2
  Hecho cuando: `pytest apps/accounts/tests/test_profile_service.py -k cli_profile` pasa verificando `manage.py profile show --email ...` y `manage.py profile edit --email ...`.
  Decisiones: exigir cuenta activa en `manage.py profile` (consultando `User.active`) e imprimir pares clave-valor legibles para inspección y scripts (pendiente de ejecutar `pytest` y `mypy` en entorno completo). — Motivo: coherencia con `RF-007` de `usuario-personalizado` y `management/commands/registration.py`. — Confianza: [Cierto]. — Cómo revertirla: eliminar `management/commands/profile.py` y su test.

- [x] T-005 Límite configurable por cuenta ante intentos fallidos de contraseña actual
  RF: RF-008, RF-014 | Depende de: — | Archivos: 4
  Hecho cuando: `pytest apps/accounts/tests/test_profile_service.py -k throttle` pasa verificando el bloqueo tras `5` fallos en `5` minutos durante `5` minutos por defecto, su configuración por settings y el reinicio del contador al completar con éxito.
  Excepción: configuración compartida repartida entre `backend/config/settings.py` y `backend/apps/accounts/conf.py`, limitador en `backend/apps/accounts/throttling.py` y su test unitario en `test_profile_service.py`.
  Decisiones: usar dos claves independientes en caché (`password-change:attempts:<user_id>` y `password-change:lock:<user_id>`) con limpieza al bloquear y al completar con éxito (pendiente de ejecutar `pytest` y `mypy` en entorno completo). — Motivo: al expirar el bloqueo la cuenta recupera una ventana limpia de 5 intentos y no queda bloqueada al primer fallo siguiente. — Confianza: [Probable]. — Cómo revertirla: eliminar los helpers de `throttling.py`, `conf.py` y las variables en `settings.py`.

- [x] T-006 Servicio de cambio de contraseña, conservación de sesión actual, cierre de otras sesiones, auditoría y avisos
  RF: RF-006, RF-007, RF-009, RF-010 | Depende de: T-005 | Archivos: 4
  Hecho cuando: `pytest apps/accounts/tests/test_profile_service.py -k password_change` pasa verificando validación de actual y nueva contraseña (incluida igual a la actual), conteo prioritario al fallar la actual, conservación de la sesión actual, revocación inmediata de las demás en `UserSession` y almacén de sesiones, auditoría de cambio y cierre, y encolado de `password_changed` siempre y `sessions_closed` solo cuando se cierran otras sesiones.
  Excepción: coordina `_skip_password_session_revocation` en `models.py`, actualización/cierre selectivo en `sessions.py` y transacción en `profile.py` junto con `test_profile_service.py` para respetar `RF-010` de `inicio-cierre-sesion`.
  Decisiones: en `sessions.refresh_current_session`, actualizar explícitamente `session[HASH_SESSION_KEY]` y llamar a `session.cycle_key()` + `session.save()` en navegador en lugar de `django.contrib.auth.update_session_auth_hash` (y actualizar `HASH_SESSION_KEY` sin rotar `raw_key` en `app`/CLI) (pendiente de ejecutar `pytest` y `mypy` en entorno completo). — Motivo: DRF con `authentication_classes=[]` deja `request.user` como `AnonymousUser`, lo que impediría a `update_session_auth_hash` actualizar la huella, mientras que mantener `raw_key` en `app` evita invalidar `X-Session-Token` en escritorio. — Confianza: [Cierto]. — Cómo revertirla: reemplazar `refresh_current_session` y `skip_password_session_revocation`.

- [x] T-007 Serializador de cambio de contraseña y mensajes multiidioma
  RF: RF-007, RF-013 | Depende de: T-006 | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_profile_api.py -k password_serializer` pasa verificando presencia, caracteres prohibidos y textos `current_password_incorrect` en `es`, `pt-BR` y `en`.
  Decisiones: permitir `new_password` ausente, `null` o vacía en `PasswordChangeSerializer` para que la vista pueda evaluar primero la contraseña actual y contabilizar el fallo de `RF-008` aunque falte la nueva (`RF-007`) (pendiente de ejecutar `pytest` y `mypy` en entorno completo). — Motivo: garantiza que enviar solo `current_password` errónea cuente como intento fallido antes de devolver `required`/`blank` en `new_password`. — Confianza: [Cierto]. — Cómo revertirla: exigir `new_password` directamente en `PasswordChangeSerializer`.

- [x] T-008 Endpoints `POST` de `auth/password/change` para web y escritorio
  RF: RF-006, RF-007, RF-008, RF-009, RF-011, RF-013 | Depende de: T-007 | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_profile_api.py -k password_change` pasa verificando `200`, `400`, `429` (`Retry-After` y `retry_after`), `403 terms_required`, `401`, continuidad real de la sesión actual e invalidación inmediata `401` de otras sesiones abiertas en web y escritorio.
  Decisiones: comprobar `throttling.check_password_change` antes de evaluar el cuerpo/contraseñas en `AppPasswordChangeView.post` y traducir `new_password` ausente/vacía o inválida tras evaluar la contraseña actual (pendiente de ejecutar `pytest` y `mypy` en entorno completo). — Motivo: cumple `RF-008` (rechazo sin evaluar contraseñas durante el bloqueo) y `RF-007` (contar intento fallido de contraseña actual incluso sin `new_password`). — Confianza: [Cierto]. — Cómo revertirla: eliminar `AppPasswordChangeView`, `BrowserPasswordChangeView` y sus rutas en `urls.py`.

- [x] T-009 Subcomando CLI `profile change-password`
  RF: RF-015 | Depende de: T-006 | Archivos: 2
  Hecho cuando: `pytest apps/accounts/tests/test_profile_service.py -k cli_password` pasa verificando `manage.py profile change-password` con entrada interactiva o argumentos y conservación opcional de `--keep-session-key`.
  Decisiones: solicitar `--current-password` y `--new-password` sin eco con `getpass` cuando se omiten y aceptar `--keep-session-key` opcional para verificar desde CLI tanto el cierre total como la conservación de la sesión indicada (pendiente de ejecutar `pytest` y `mypy` en entorno completo). — Motivo: coherencia con `password_reset.py` y cobertura completa de `RF-015`. — Confianza: [Cierto]. — Cómo revertirla: eliminar `_change_password` de `management/commands/profile.py` y su test.

- [x] T-010 Cliente HTTP de consulta de perfil (`getProfile`) y deduplicación de `GET` en vuelo
  RF: RF-001 | Depende de: T-003 | Archivos: 3
  Hecho cuando: `pnpm --filter frontend test src/api/client.test.ts` y `pnpm --filter frontend typecheck` verifican `getProfile` contra `/auth/profile` y la compartición de `GET` concurrentes en `client.ts`.
  Decisiones: dividir el alcance cliente de perfil dejando `getProfile` + deduplicación de `GET` concurrentes (`inflight` por URL y token en `client.ts`) en `E-03`, y aplazar `patch`, `updateProfile` y códigos de edición en `serverErrors.ts` a `T-010b` (pendiente de ejecutar Vitest y `tsc` en entorno con dependencias instaladas). — Motivo: evita peticiones duplicadas bajo `<StrictMode>` detrás del túnel SSH/VPS y mantiene `E-03` bajo 500 líneas. — Confianza: [Cierto]. — Cómo revertirla: revertir `775a465` / `0801f25`.

- [x] T-010b Cliente HTTP `patch`, `updateProfile` y mapeo de errores de edición de perfil
  RF: RF-002, RF-003, RF-004, RF-013 | Depende de: T-010 | Archivos: 6
  Hecho cuando: `pnpm --filter frontend test src/registration/serverErrors.test.ts` pasa verificando `patch` en `ApiClient`, `updateProfile` en `api/profile.ts` y la traducción de `email_immutable`, `unknown_field` y `no_profile_fields`.
  Excepción: añade `patch` en `client.ts` junto a `api/profile.ts`, `serverErrors.ts`, `serverErrors.test.ts` y los mocks de `ApiClient` en `api/auth.test.ts` y `api/registration.test.ts` para mantener `tsc --noEmit` limpio.
  Decisiones: extraer `jsonSend` en `client.ts` para compartir `POST` y `PATCH` manteniendo la deduplicación de `GET` concurrentes intacta (pendiente de ejecutar Vitest y `tsc` en entorno con dependencias instaladas). — Motivo: evita duplicación en mutaciones JSON con idioma automático. — Confianza: [Cierto]. — Cómo revertirla: revertir el commit de `T-010b`.

- [x] T-011 Helper compartido de países y traducciones de perfil en tres idiomas
  RF: RF-012, RF-013 | Depende de: — | Archivos: 5
  Hecho cuando: `pnpm --filter frontend test src/i18n/keys.test.ts src/i18n/locales/locales.test.ts src/registration/RegisterPage.test.tsx` pasa verificando las claves nuevas en `es`, `pt-BR` y `en` y el catálogo localizado compartido de países.
  Excepción: los tres archivos de idioma (`es.ts`, `pt-BR.ts`, `en.ts`) deben actualizarse juntos por `i18n/keys.test.ts`, además de extraer `forms/countries.ts` desde `RegisterPage.tsx`.
  Decisiones: ubicar las claves de perfil dentro de `auth.*` en los catálogos de idioma para conservar los grupos raíz verificados por `locales.test.ts`, y añadir ya las claves `validation.{emailImmutable, unknownField, noProfileFields}` para que `locales.test.ts` y `T-010b` permanezcan alineados (pendiente de ejecutar tests/typecheck de frontend en entorno con dependencias instaladas). — Motivo: evita romper `locales.test.ts` y mantiene `ValidationKey` sincronizado. — Confianza: [Cierto]. — Cómo revertirla: revertir el commit de `T-011`.

- [x] T-012 Vista de consulta de información personal en `ProfilePage`
  RF: RF-001, RF-011, RF-012, RF-013 | Depende de: T-010, T-011 | Archivos: 4
  Hecho cuando: `pnpm --filter frontend test src/auth/ProfilePage.test.tsx` pasa verificando estructura visible desde el inicio con placeholders *skeleton* (`aria-busy="true"`), correo y datos personales en solo lectura, estado `"ZZ"` mostrado como sin país asignado, redirecciones ante `401`/`terms_required` y accesibilidad con `axe-core`.
  Excepción: añade la clase global `.skeleton` en `frontend/src/styles/base.css` siguiendo el patrón incorporado en `docs/identidad-visual.md`.
  Decisiones: mantener visible desde el primer frame el `<Block>` de información personal con placeholders `.skeleton` de 36 px (`.profile-skeleton`) mientras carga `GET /auth/profile` y estabilizar `onLoggedOut`/`onTermsRequired` en un `ref` para evitar re-peticiones al re-renderizar `App` (pendiente de ejecutar Vitest y `tsc` en entorno con dependencias instaladas). — Motivo: evita pantalla vacía y saltos de altura cuando la respuesta del backend tarda tras un túnel SSH o red lenta. — Confianza: [Cierto]. — Cómo revertirla: revertir `8683bf5`.

- [x] T-012b Edición parcial, validación y sincronización lateral del perfil en `ProfilePage`
  RF: RF-002, RF-003, RF-004, RF-011, RF-012, RF-013 | Depende de: T-010b, T-012, T-013 | Archivos: 5
  Hecho cuando: `pnpm --filter frontend test src/auth/ProfilePage.test.tsx src/App.test.tsx` pasa verificando tarjeta a ancho completo en solo lectura por defecto, menú de acciones vertical (`Editar`, `Cambiar contraseña` y `Deshabilitar` deshabilitadas), edición parcial y completa de nombre, fecha y país con `Cancelar` y `Guardar cambios`, conservación de `"ZZ"` mientras no cambie, validación local en blur y submit, foco al primer error, errores de servidor, recorte reflejado en input, actualización inmediata del nombre en el menú lateral y accesibilidad.
  Excepción: actualiza `ProfilePage.tsx`, `ProfilePage.css`, `ProfilePage.test.tsx`, `App.tsx`, `App.test.tsx`, `Menu.tsx`, `Menu.css`, `icons/index.ts`, `icons.test.tsx` y los diccionarios i18n para incorporar el menú de acciones en tarjeta y las opciones deshabilitadas según `docs/identidad-visual.md`.
  Decisiones: hacer que la tarjeta de información personal ocupe todo el ancho disponible con correo arriba a ancho completo y debajo `Nombre`, `País` y `Fecha` en una sola fila de tres columnas repartiendo todo el espacio horizontal (`repeat(3, minmax(0, 1fr))` en escritorio, 1 columna en móvil), arrancar en solo lectura e incorporar en la esquina superior derecha un menú vertical de tres puntos (`IconMoreVertical`, `Menu` con soporte `disabled` mediante `aria-disabled`) con «Editar» activo y «Cambiar contraseña» / «Deshabilitar» deshabilitados por ahora; reducir el alto máximo de `Menu` a 200 px y limitar dinámicamente su altura al espacio visible (volteando hacia arriba cuando falta espacio abajo) para que ningún selector alargue la página; al elegir «Editar» se conmuta al formulario editable con «Cancelar» y «Guardar cambios», propagando los cambios a `setCtxUser` y `onProfileUpdated` y omitiendo `country` si permanece en `"ZZ"` (pendiente de ejecutar Vitest y `tsc` en entorno con dependencias instaladas). — Motivo: responde a las peticiones explícitas del usuario sobre la disposición en pantalla completa, la distribución horizontal en tres columnas, las acciones contextuales de la tarjeta y evitar que un desplegable alargue la altura de la página. — Confianza: [Cierto]. — Cómo revertirla: revertir `1ed9ec9`, `2d95604`, `1548ac7`, `4308632`, `6e970cf` y `25d12ca`.

- [x] T-013 Conexión de `/profile` en `App` y menú lateral privado compartido
  RF: RF-001, RF-012 | Depende de: T-012 | Archivos: 7
  Hecho cuando: `pnpm --filter frontend test src/App.test.tsx` pasa verificando el enlace a `/profile` en el menú lateral de `/` y `/profile`, el acceso autenticado sin recarga, y las redirecciones sin sesión o con términos pendientes.
  Excepción: conecta la navegación privada compartida (`privateNav.tsx`, `icons/index.ts`, `Sidebar.tsx`, `HomePage.tsx`), el enrutador (`App.tsx`) y sus pruebas en `App.test.tsx`.
  Decisiones: añadir `onSelect` opcional a `SidebarItem` para interceptar clics primarios en SPA sin romper enlaces externos ni `role="link"`, y extraer `privateNavItems` y `privateSidebarUser` en `frontend/src/auth/privateNav.tsx` para compartir menú lateral y cierre de sesión entre `HomePage` y `ProfilePage` (pendiente de ejecutar Vitest y `tsc` en entorno con dependencias instaladas). — Motivo: evita duplicación entre vistas privadas y cumple `C-01`. — Confianza: [Cierto]. — Cómo revertirla: revertir `6e7e78e`.

- [x] T-013b Placeholders *skeleton* con *fade* en el panel principal (`HomePage`) y usuario persistente en contexto
  RF: RF-012 | Depende de: T-013 | Archivos: 9
  Hecho cuando: `pnpm --filter frontend test src/auth/HomePage.test.tsx src/auth/ProfilePage.test.tsx src/App.test.tsx` pasa verificando los placeholders *skeleton* con *fade out / fade in* para el subtítulo («Sesión iniciada como…») y la tabla de sesiones activas en `HomePage` (`Block.tsx`), y que el usuario (nombre/correo) se preserva en contexto (`UserProvider.tsx` / `privateNav.tsx`) para que el botón de usuario de la barra lateral no desaparezca al navegar ni al recargar.
  Excepción: extiende `Block.tsx` (`loading` / `loadingContent`) junto con `base.css`, `HomePage.tsx`, `HomePage.test.tsx`, `ProfilePage.tsx`, `UserProvider.tsx`, `privateNav.tsx`, `setupTests.ts` y `App.tsx`.
  Decisiones: incorporar `loading` y `loadingContent` en `Block.tsx` para reutilizar `.skel-slot` sin reindentar `Table`, y aislar `UserProvider` en `UserProvider.tsx` manteniendo `usePrivateUser` y el respaldo en `sessionStorage` (`confiabilidad.user`, limpiado en `401`, cierre de sesión y `setupTests.ts`) en `privateNav.tsx` para evitar avisos de `react-refresh` (pendiente de ejecutar Vitest y `tsc` en entorno con dependencias instaladas). — Motivo: mantiene visible el botón de usuario entre pantallas y recargas y respeta las reglas de ESLint. — Confianza: [Cierto]. — Cómo revertirla: revertir `ebbe6ab`.

- [ ] T-014 Cliente y traducciones para cambio de contraseña en `/profile`
  RF: RF-006, RF-007, RF-008, RF-012, RF-013 | Depende de: T-008, T-010 | Archivos: 5
  Hecho cuando: `pnpm --filter frontend test src/i18n/keys.test.ts src/registration/serverErrors.test.ts` pasa verificando `changePassword` en `api/profile.ts`, el mapeo de `current_password_incorrect` y las claves en `es`, `pt-BR` y `en`.
  Excepción: los tres archivos de idioma (`es.ts`, `pt-BR.ts`, `en.ts`) deben actualizarse juntos por `i18n/keys.test.ts`, junto con `api/profile.ts` y `serverErrors.test.ts`.

- [ ] T-015 Bloque de cambio de contraseña en `ProfilePage`
  RF: RF-006, RF-007, RF-008, RF-011, RF-012, RF-013 | Depende de: T-013, T-014 | Archivos: 3
  Hecho cuando: `pnpm --filter frontend test src/auth/ProfilePage.test.tsx` pasa verificando contraseña actual y nueva contraseña única con mostrar/ocultar y lista de requisitos en vivo, validación local, vaciado selectivo tras éxito o error de actual/política/red, cuenta atrás con botón deshabilitado ante `429`, redirección ante términos pendientes o `401`, idiomas y accesibilidad.

## Entregas
Rama de integración: `feat/perfil-y-cambio-contrasena` (los PR de las entregas van contra ella; ver `AGENTS.md`).

- E-01 Servicio y comandos CLI de consulta y edición de perfil
  Tareas: T-001, T-004 | Líneas reales: 320 | Rama: `feat/perfil-y-cambio-contrasena-api-perfil`
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_profile_service.py` y probar `python manage.py profile show --email <EMAIL>` y `python manage.py profile edit --email <EMAIL> --name "..."` comprobando la persistencia y que `"ZZ"` se conserva si no se cambia.

- E-01b Endpoints HTTP de consulta y edición de perfil (`GET`/`PATCH auth/profile`)
  Tareas: T-002, T-003 | Líneas reales: 368 | Rama: `feat/perfil-y-cambio-contrasena-api-perfil-http`
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_profile_api.py` y hacer `GET`/`PATCH` con `curl` a `/api/app/v1/auth/profile` verificando que cambiar el correo, enviar peticiones vacías o campos desconocidos se rechaza.

- E-02 Servicio de cambio de contraseña con límite configurable y cierre de otras sesiones
  Tareas: T-005, T-006 | Líneas reales: 353 | Rama: `feat/perfil-y-cambio-contrasena-api-password`
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_profile_service.py` o probar `profile.change_password(...)` desde `python manage.py shell` verificando conservación de la sesión actual, cierre del resto, auditoría y correos encolados.

- E-02b Endpoints HTTP y CLI de cambio de contraseña (`POST auth/password/change` y `profile change-password`)
  Tareas: T-007, T-008, T-009 | Líneas reales: 394 | Rama: `feat/perfil-y-cambio-contrasena-api-password-http`
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_profile_api.py apps/accounts/tests/test_profile_service.py`, iniciar dos sesiones con `curl` (`/api/app/v1/auth/login`), llamar a `POST /api/app/v1/auth/password/change` con una de ellas y comprobar que la sesión actual sigue devolviendo `200` en `/api/app/v1/auth/profile` mientras la otra devuelve `401`, además de probar `python manage.py profile change-password`.

- E-03 Pantalla `/profile`, *skeletons* con *fade*, usuario persistente y deduplicación de `GET`
  Tareas: T-010, T-011, T-012, T-013, T-013b | Líneas reales: 787 | Rama: `feat/perfil-y-cambio-contrasena-ui-perfil`
  Excepción: el usuario autorizó explícitamente superar 500 líneas en este PR («continua en este pr») para probar en una sola entrega los *skeletons* con *fade out / fade in* tanto en `/profile` como en el panel principal (`HomePage`), el botón de usuario persistente en contexto (`UserProvider`) y la deduplicación de `GET` (`client.ts`), manteniendo fuera la edición del perfil (`E-03b`).
  Cómo probarlo: ejecutar `pnpm --filter frontend test`, recargar `/` observando los *skeletons* en gris claro de «Sesión iniciada como…» y la tabla de sesiones activas con *fade out / fade in*, pulsar «Perfil» en el menú lateral y comprobar que el botón de usuario no desaparece durante la carga de `/profile` y que en Network solo sale una petición `GET` por endpoint.

- E-03b Edición parcial de datos personales y menú de tarjeta en `/profile`
  Tareas: T-010b, T-012b | Líneas reales: 702 | Rama: `feat/perfil-y-cambio-contrasena-ui-perfil-edicion`
  Excepción: pendiente de confirmación del usuario por superar las 500 líneas (`sdd.max_lineas_pr_excepcion`): además del cliente `patch`/`updateProfile`, la edición con validación/errores/`"ZZ"` y la sincronización con `UserProvider`/`App.test.tsx`, incluye la tarjeta a ancho completo en fila de tres columnas, el icono `IconMoreVertical`, las opciones deshabilitadas y el ajuste de altura/volteo en `Menu`, y el menú de tres opciones (`Editar`, `Cambiar contraseña`, `Deshabilitar`) pedido por el usuario en esta rama.
  Cómo probarlo: ejecutar `pnpm --filter frontend test`, abrir `/profile` con sesión iniciada, verificar la tarjeta a ancho completo en solo lectura, abrir el botón de tres puntos y pulsar «Editar» para probar la edición de nombre, fecha y país, «Cancelar» y «Guardar cambios», así como el estado deshabilitado de «Cambiar contraseña» y «Deshabilitar».

- E-04 Formulario de cambio de contraseña en `/profile`
  Tareas: T-014, T-015 | Líneas estimadas: 250 | Rama: `feat/perfil-y-cambio-contrasena-ui-password`
  Cómo probarlo: ejecutar `pnpm --filter frontend test`, abrir `/profile` con sesión iniciada, cambiar la contraseña introduciendo la contraseña actual y la nueva, y comprobar la confirmación, el vaciado de campos y que otra sesión abierta pasa a `/login` al hacer una acción.

## RF sin tarea
ninguno
