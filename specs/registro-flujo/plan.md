# Plan: registro-flujo
Estado: borrador

## Dependencias previas a implementar
- `sdd-cambio` en `procesos-pendientes`, RF-009 (S-01, CF-6): hoy rechaza cualquier código en un
  proceso con el código validado y antepone ese rechazo a comparar el código. RF-008 y RF-012 de esta
  feature exigen aceptar de nuevo el código correcto y sumar un intento con uno incorrecto. No hay
  solución dentro de esta feature: cualquier ruta que acepte el código contradice ese RF. El cambio
  se limita al registro (registro pendiente y su plaza), porque `cambio-contrasena` reutiliza RF-009.
- Los `sdd-cambio` de marketing en `procesos-pendientes` y `registro-api` ya están aprobados con
  impacto analizado: los implementa este plan (M-05).

## Módulos

### Backend

### M-01 Servicio del flujo (`apps/accounts/registration.py`)
Responsabilidad: operaciones nuevas que usa la API, todas sobre `_locked_process` (las dos tablas,
plaza primero; D-14 y D-18 de `procesos-pendientes`), para que un registro real y una plaza hagan las
mismas consultas (RF-017):
- `status(public_id)`: segundos que le quedan al código, segundos hasta poder reenviar, reenvíos
  restantes, bloqueado y caducado. Nunca dice si el código está validado (D-05). `None` si no existe.
- `verify_code(public_id, code)`: orden caducado → bloqueado → código caducado → no coincide (suma
  intento) → si ya estaba validado, lo acepta sin cambiar nada; si no, lo valida (RF-007, RF-008).
- `resend_code(public_id)`: además de RF-016 de `procesos-pendientes`, rechaza antes de 60 s desde el
  último envío o tras el quinto reenvío, y con el código validado, con el mismo resultado `UNAVAILABLE`
  en los tres casos (RF-010, C-04).
- `complete_with_code(public_id, code, password)`: orden no existe → caducado → bloqueado → no
  coincide (suma intento) → no validado (suma intento, mismo resultado que no coincide; C-03) →
  política de contraseña (sin intento; RF-013) → `complete` existente, con la concesión de marketing
  (M-05) (RF-012, RF-014).
- `purge_stale()`: borra, en una transacción, los registros pendientes y las plazas de registro cuyo
  último código caducó hace más de 24 h (RF-020, D-07).
`verify`, `resend` y `complete` actuales siguen para la consola (RF-023 de `procesos-pendientes`).
RF: RF-006, RF-007, RF-008, RF-009, RF-010, RF-012, RF-013, RF-014, RF-016, RF-017, RF-020

### M-02 Contadores de reenvío (`apps/accounts/models.py`, `apps/accounts/processes.py`, migración nueva)
Responsabilidad: `CodeProcess` gana `resend_count` (entero, 0) y `last_sent_at` (fecha). Se fijan
igual en un registro real y en una plaza (D-04): `start` crea la plaza con `last_sent_at` = ahora;
`issue_code` (registro nuevo o repetido) y `_leave_as_issued` (plaza con cuenta) ponen
`resend_count` = 0 y `last_sent_at` = ahora; `resend_code` suma uno y fija `last_sent_at`.
RF: RF-010, RF-017

### M-03 API del flujo (`apps/accounts/api/flow_views.py`, `apps/accounts/api/flow_serializers.py`, `apps/accounts/api/urls.py`, `apps/accounts/api/messages.py`)
Responsabilidad: cuatro rutas por cliente, con la misma vista y el CSRF de D-02 de `registro-api` en
la variante web:
- `POST /api/{browser,app}/v1/registration/status` `{public_id}` → `200` con el estado de M-01;
- `POST …/registration/verify` `{public_id, code}` → `200` o `400` `{"code": "wrong_code" |
  "locked" | "code_expired" | "expired"}`;
- `POST …/registration/resend` `{public_id}` → `202` o `400` `{"code": "resend_unavailable"}`;
- `POST …/registration/complete` `{public_id, code, password}` → `201`, el mismo `400` de verify, o
  `400` `{"errors": {"password": [{code, message}]}}` con cada regla incumplida.
Un identificador inexistente da `404` en las cuatro (RF-016). El idioma de los textos sale del campo
`language` y de `Accept-Language` (M-05 de `registro-api`). El identificador va en el cuerpo, nunca
en la ruta (D-03). Antes de evaluar, M-04 (RF-019).
RF: RF-007, RF-010, RF-012, RF-013, RF-016, RF-017, RF-019, RF-021, RF-022

### M-04 Límite por IP del flujo (`apps/accounts/throttling.py`, `apps/accounts/conf.py`)
Responsabilidad: `check_flow_ip(ip)`: 60 peticiones por hora entre verificar, reenviar y completar,
con el registro deslizante existente (D-07 de `registro-api`) y otra clave. La consulta de estado no
cuenta (RF-019). Configuración `REGISTRATION_RATE_FLOW_IP_PER_HOUR`,
`REGISTRATION_RESEND_INTERVAL_SECONDS` (60), `REGISTRATION_MAX_RESENDS` (5) y
`REGISTRATION_PURGE_AFTER_HOURS` (24) en `settings.py` y `.env.example` (RF-023).
RF: RF-019, RF-023

### M-05 Marketing en el registro (`apps/accounts/models.py`, `apps/accounts/registration.py`, `apps/accounts/api/serializers.py`, `apps/accounts/api/views.py`, migración nueva)
Responsabilidad, sobre los cambios aprobados de `procesos-pendientes` y `registro-api`:
- `PendingRegistration` gana `marketing_version` y `marketing_locale`, vacíos por defecto (como D-10
  de `registro-api`);
- el serializador del formulario gana `marketing`, un campo tolerante: todo lo que no sea un objeto
  con `version` y `locale` de texto, sin nulos ni sustitutos y dentro de 20 y 5 caracteres, pasa a
  `None`, nunca a un error (RF-015 de `registro-api`, D-06). El idioma se normaliza con
  `locales.normalize`;
- `start` comprueba el documento con `current_document_shown(MARKETING)` y, si lo rechaza, lo descarta
  (C-03 de `procesos-pendientes`); si no, lo guarda en el `payload`. `_register_or_repeat` lo copia
  al crear y conserva el del existente al repetir;
- `complete` llama a `grant_marketing` en un punto de guardado y traga su rechazo
  (`ValidationError`, `IntegrityError`) sin rastro (C-01 de `procesos-pendientes`), como
  `_accept_stored_terms`;
- actualiza el `resumen.md` de `procesos-pendientes` y de `registro-api`.
RF: RF-018 (y RF-001, RF-005, RF-020, RF-024 de `procesos-pendientes`; RF-001, RF-007, RF-015 de
`registro-api`)

### M-06 Opciones del formulario (`apps/accounts/api/flow_views.py`, `apps/accounts/validators.py`)
Responsabilidad: `GET /api/{browser,app}/v1/registration/options?language=<idioma>` →
`{"countries": [códigos ISO], "terms": {version, locale, content} | null, "marketing": … | null}`,
con `current_document` de `consents.versions` en el idioma pedido. La variante web lleva
`ensure_csrf_cookie`, que da al navegador la cookie `csrftoken` que exigen los `POST` (D-09).
`validators.py` publica `COUNTRY_CODES` (hoy `_ISO_ALPHA_2`, privado), sin cambiar la validación.
RF: RF-001, RF-021

### M-07 Limpieza programada (`apps/accounts/tasks.py`, `config/settings.py`, `management/commands/registration.py`)
Responsabilidad: tarea `purge_stale_registrations` que llama a `purge_stale()` (M-01), en
`CELERY_BEAT_SCHEDULE` cada hora (margen ≤ 1 h, C-08), y subcomando `registration purge-stale` para
dispararla desde consola (P-03).
RF: RF-020

### Frontend

### M-08 Cliente de la API (`frontend/src/api/client.ts`, `frontend/src/api/registration.ts`)
Responsabilidad: `fetch` con JSON, `Accept-Language` y el campo `language` del idioma activo. En el
navegador usa `/api/browser/v1` (mismo origen) y la cabecera `X-CSRFToken` con la cookie `csrftoken`;
en Tauri usa `/api/app/v1` sobre `VITE_API_BASE_URL` (D-10). Devuelve resultados tipados: éxito,
errores por campo (código y parámetros), código de error, `404`, límite superado con `retry_after`
y fallo de red.
RF: RF-004, RF-021, RF-022, RF-024

### M-09 Rutas (`frontend/src/routing/router.ts`, `frontend/src/App.tsx`)
Responsabilidad: enrutador mínimo con la API de historial (D-08): `/register`,
`/register/continue#<public_id>` (verificación y contraseña) y `/register/done`; `/` sigue siendo la
página de muestra (S-06 de `componentes-base-accesibles`). La ruta de verificación es la misma que
la del enlace del correo (`/register/continue#<public_id>`, D-09 de `correo-asincrono-plantillas`).
RF: RF-004, RF-005, RF-015

### M-10 Pantalla del formulario (`frontend/src/registration/RegisterPage.tsx`, `frontend/src/registration/serverErrors.ts`)
Responsabilidad: carga las opciones (M-06); campos de nombre, fecha (`type="date"`), correo, país
(lista de M-06 con nombres de `Intl.DisplayNames` en el idioma activo), términos (casilla obligatoria
con el texto en un bloque desplegable) y marketing (casilla opcional, sin marcar, oculta si
`marketing` es `null`). Comprobaciones del navegador de RF-002 con `useFormValidation` (M-12). Envía
`marketing` solo con la casilla marcada (S-23 de `registro-api`). Traduce cada código del servidor a
una clave propia, con un texto genérico para un código desconocido (D-11). Con `202`, navega a la
verificación.
RF: RF-001, RF-002, RF-003, RF-004, RF-018, RF-022, RF-024

### M-11 Pantallas de verificación, contraseña y cuenta creada (`frontend/src/registration/VerifyPage.tsx`, `PasswordStep.tsx`, `DonePage.tsx`, `useCountdown.ts`)
Responsabilidad:
- verificación: lee el identificador del fragmento, se asegura de tener la cookie CSRF (D-09), pide
  el estado (M-03) y muestra el texto fijo,
  el temporizador y la cuenta atrás de reenvío, que cuentan en el navegador desde los segundos del
  servidor y se refrescan al recargar (RF-006); con `404`, la pantalla de enlace no válido (RF-016);
- verificar: código aceptado → paso de contraseña con el código en el estado de React (S-08);
  incorrecto, bloqueado o caducado → su mensaje bajo el campo (RF-007, RF-009);
- reenviar: botón con cuenta atrás y tope; agotado, acceso al formulario (RF-010);
- contraseña: `PasswordField` nuevo con `newPasswordRules` (RF-013); envía código y contraseña; un
  rechazo del código descarta el código y vuelve a verificación con su mensaje (RF-011, C-02); `201`
  → `/register/done` (RF-015);
- límite superado en cualquier acción: mensaje con cuenta atrás y acción reactivada al llegar a cero
  (RF-024).
Ninguna pantalla muestra el correo: el cliente no lo recibe en ninguna respuesta (RF-005).
RF: RF-005, RF-006, RF-007, RF-008, RF-009, RF-010, RF-011, RF-013, RF-015, RF-016, RF-022, RF-024

### M-12 Ampliaciones de componentes (`frontend/src/forms/useFormValidation.ts`, `frontend/src/components/fields/`, `frontend/src/forms/passwordRules.ts`)
Responsabilidad, sin cambiar el comportamiento actual de `componentes-base-accesibles`:
- `useFormValidation` lee también `<select>` y casillas (`"true"` o `""`), admite varios errores por
  campo y una opción `scrollToError` que hace `scrollIntoView` antes del foco (RF-003). Sin la opción,
  todo sigue igual y sus tests no cambian;
- componentes nuevos `Checkbox` y `SelectField`, con la misma estructura accesible que `TextField`
  (etiqueta, `aria-invalid`, `aria-describedby`), y `TextField` admite `type="date"`;
- `passwordRules.ts`: «solo números» pasa a usar la misma noción de dígito que `str.isdigit()` del
  servidor (D-12), lo que cierra el riesgo residual (2) de `componentes-base-accesibles`.
RF: RF-002, RF-003, RF-013 (CF-8)

### M-13 Estilo (`frontend/src/styles/tokens.css`, `frontend/src/styles/base.css`, `frontend/src/main.tsx`, `frontend/package.json`)
Responsabilidad: variables CSS de la paleta Niebla marina para los temas claro y oscuro según el
sistema operativo (`prefers-color-scheme`), formas, foco visible, espaciado y las fuentes
`@fontsource-variable/manrope` y `@fontsource-variable/jetbrains-mono` (aprobadas por el usuario el
2026-10-30), con JetBrains Mono en el campo del código. Sin selector de tema (D-13).
RF: RF-001, RF-005 (S-14)

### M-14 Desarrollo y documentación (`frontend/vite.config.ts`, `docker/docker-compose.yml`, `specs/registro-flujo/resumen.md`, `specs/cambio-contrasena/HUMAN_TODO.md`)
Responsabilidad: `server.proxy` de Vite para `/api` hacia el backend (destino por la variable
`VITE_BACKEND_URL`; en Docker, `http://backend:8000`), para que la web sea mismo origen en
desarrollo; `resumen.md` con el recorrido en la web y con `curl` (CF-7); y en el `HUMAN_TODO.md` de
`cambio-contrasena`, que los límites de reenvío y verificación del registro ya existen y los del
restablecimiento siguen pendientes.
RF: RF-021 (CF-7)

## Modelo de datos
- `accounts.CodeProcess` (abstracto; afecta a `PendingRegistration`, `PhantomProcess` y
  `PasswordResetRequest`): `resend_count` PositiveSmallIntegerField(0) y `last_sent_at`
  DateTimeField(null) (migración propia; los procesos existentes quedan con 0 y nulo, que se trata
  como «se puede reenviar»).
- `accounts.PendingRegistration`: `marketing_version` CharField(20, blank, `""`) y
  `marketing_locale` CharField(5, blank, `""`) (migración propia).
- `accounts.PhantomProcess.payload` (JSON, sin migración): añade `marketing_version` y
  `marketing_locale`.
- Caché (Redis): `registration-rate:flow-ip:<IP>` → marcas de tiempo, caduca a la hora.
- Frontend: sin almacenamiento; el código validado vive solo en el estado de React (S-08).

## Decisiones

### D-01 Operaciones nuevas en el servicio, no cambios en las de la consola
Elegida: `status`, `verify_code`, `resend_code` y `complete_with_code` nuevas en `registration.py`,
y las de la consola sin cambios de firma.
Descartada: cambiar `verify`, `resend` y `complete` para que pidan el código y apliquen los límites.
Motivo: la consola de RF-023 de `procesos-pendientes` completa sin código y sin límites de reenvío;
cambiar su firma obligaría a otro `sdd-cambio`. Las nuevas reutilizan `_locked_process`, el cálculo
de la huella y `complete`, así que las reglas siguen en un solo sitio.

### D-02 Comparar el código antes de mirar si está validado
Elegida: en `verify_code` y `complete_with_code`, comparar el código antes de mirar
`code_validated_at`.
Descartada: el orden de `processes.check_code` (validado primero).
Motivo: con el orden actual, cualquier código enviado a un proceso validado da «ya validado» y una
plaza nunca puede darlo: delataría que el registro es real (RF-017). Comparando antes, un código
incorrecto suma intento igual en los dos. `check_code` sigue como está para `cambio-contrasena`.

### D-03 El identificador va en el cuerpo de un `POST`
Elegida: `public_id` en el cuerpo JSON de las cuatro rutas, también en la consulta de estado.
Descartada: `GET /registration/<public_id>`.
Motivo: el correo pone el identificador en el fragmento para que no quede en los registros del
servidor ni del proxy (D-09 de `correo-asincrono-plantillas`); en la ruta acabaría en ellos.

### D-04 Contadores de reenvío en el proceso, fijados en los mismos puntos
Elegida: `resend_count` y `last_sent_at` en `CodeProcess`, puestos a cero en `issue_code` y
`_leave_as_issued`.
Descartada: contarlos en la caché, como el límite por IP.
Motivo: deben nacer, reiniciarse y morir con el proceso, igual en un registro real y en una plaza
(RF-017). En la caché sobrevivirían a un registro repetido o se perderían al vaciarla, de forma
distinta en cada caso.

### D-05 El estado no expone la validación
Elegida: la consulta de estado devuelve tiempos, reenvíos, bloqueo y caducidad, pero no si el código
está validado; la pantalla sabe que lo validó porque lo acaba de aceptar el servidor.
Descartada: un campo `validated`.
Motivo: una plaza nunca está validada; con ese campo, cualquiera con el enlace sabría que el registro
es real. *Riesgo aceptado (C-04):* con el código validado, el reenvío se rechaza y en una plaza no;
solo lo ve quien tiene el enlace después de que su dueño validara el código.

### D-06 Campo de marketing tolerante propio
Elegida: un campo del serializador que convierte cualquier entrada no válida en `None`, comprobando
a mano tipos, longitudes, nulos y sustitutos, con la protección de anidamiento de `_BoundedJSONField`.
Descartada: un `Serializer` anidado de DRF con `required=False`.
Motivo: un serializador anidado produce errores de campo y su `400`, que RF-015 de `registro-api`
prohíbe; los errores `500` de las validaciones de esa feature vinieron justo de estas entradas.

### D-07 Limpieza por la caducidad del último código, en una transacción
Elegida: `code_expires_at <= ahora - 24 h` en `PendingRegistration` y en `PhantomProcess` de
registro, borrados en la misma transacción por una tarea horaria.
Descartada: borrar cada tabla en su propia tarea, o usar la caducidad del proceso (`expires_at`).
Motivo: RF-020 pide el mismo criterio y la misma operación, para que un registro real y una plaza
pasen a «no encontrado» a la vez (RF-017). `code_expires_at` es el mismo campo en los dos.

### D-08 Enrutador propio con la API de historial
Elegida: un módulo de unas decenas de líneas con `pushState`, `popstate` y un `switch` de rutas.
Descartada: `react-router`.
Motivo: cuatro rutas no justifican una dependencia nueva (`AGENTS.md`). Si la aplicación crece, se
reemplaza.

### D-09 Cookie CSRF desde la consulta de opciones
Elegida: `ensure_csrf_cookie` en la ruta web de opciones (un `GET`). El formulario la carga siempre
primero, y la pantalla de verificación la llama antes de su primer `POST` si el navegador aún no
tiene la cookie `csrftoken` (por ejemplo, al abrir el enlace del correo en otro navegador).
Descartada: pedir la sesión de allauth (`/_allauth/browser/v1/auth/session`) para obtener la
cookie, o eximir de CSRF la consulta de estado.
Motivo: no mezcla el registro con las sesiones (S-07); y sin CSRF la consulta de estado sería la
única ruta web del flujo sin esa protección.

### D-10 Cliente de aplicación solo en Tauri
Elegida: detectar Tauri (`__TAURI_INTERNALS__`) y usar las rutas `app` con `VITE_API_BASE_URL`; en
el navegador, las rutas `browser` relativas.
Descartada: las rutas `browser` también en Tauri.
Motivo: en producción Tauri sirve el frontend desde su propio origen, y la cookie CSRF de otro origen
no llega; es el reparto de S-07 de `auth-headless`.

### D-11 Errores del servidor por código, traducidos en el navegador
Elegida: un mapa código → clave de i18n del frontend (los de M-04 de `registro-api`, los de la
contraseña y los del flujo), con un texto genérico para un código desconocido.
Descartada: mostrar el `message` que ya devuelve el servidor.
Motivo: el error se guarda como clave y se traduce al pintar (D-05 de `componentes-base-accesibles`);
con el texto del servidor, cambiar de idioma dejaría los errores en el anterior. *Coste:* la lista
de códigos se mantiene en los dos lados; un código nuevo sin traducir muestra el genérico.

### D-12 Dígitos como `str.isdigit()`
Elegida: `\p{Nd}` más la lista explícita de caracteres con `Numeric_Type=Digit` de Unicode
(superíndices, subíndices, dígitos rodeados…), generada con `unicodedata` y con un test que la
compara con los casos compartidos.
Descartada: dejar `\p{Nd}`, que solo cubre `Numeric_Type=Decimal`.
Motivo: CF-8 exige el resultado del servidor (S-17); las expresiones regulares de JavaScript no
tienen la propiedad `Numeric_Type`.

### D-13 Tema por el sistema operativo, sin selector
Elegida: los dos temas de `docs/identidad-visual.md` por `prefers-color-scheme`.
Descartada: añadir ahora el selector de tema recordado.
Motivo: el selector es de la aplicación entera, no del registro; esta feature deja las variables
listas para él.

## Estrategia de tests
- Servicio (`backend/apps/accounts/tests/test_registration_flow.py`, pytest): cada rama de
  `verify_code`, `resend_code`, `complete_with_code` y `status` (RF-007…RF-014, RF-016); contadores de
  reenvío al empezar, repetir, resolver la plaza y reenviar (RF-010); `purge_stale` con el borde de
  24 h (RF-020). El tiempo se mueve con `update()` (D-07 de `procesos-pendientes`).
- Equivalencia (`test_registration_flow_equivalence.py`, pytest): un registro real cuyo código no se
  acierta y una plaza recorren consultar, verificar, reenviar, completar y caducar, con las mismas
  respuestas (estado, cuerpo, cabeceras y cookies), los mismos plazos y las mismas consultas
  (`django_assert_num_queries`); y pasan a `404` a la vez al repetir el registro y con `purge_stale`
  (CF-2, RF-017). Un identificador desconocido, de cualquier formato, da `404` sin escribir nada.
- API (`test_registration_flow_api.py`, pytest): códigos de respuesta, CSRF en la ruta web, límite
  por IP con su `429` y la consulta de estado fuera de él (RF-019, RF-021), textos en los tres
  idiomas (RF-022), y que completar sin código, con uno incorrecto o con uno no validado no crea la
  cuenta (CF-3).
- Marketing (`test_registration_service.py`, `test_registration_api.py`, pytest): los tests del
  análisis de impacto de `procesos-pendientes` y `registro-api` (CF-4, CF-8 de `registro-api`).
- Casos compartidos de contraseña: un test de pytest y otro de Vitest recorren la tabla de la spec
  (CF-8).
- Frontend (Vitest + Testing Library, `fetch` simulado): formulario (comprobaciones, errores de
  servidor bajo cada campo, desplazamiento y foco al primero, marketing solo marcado, redirección),
  verificación (temporizador, reenvío, bloqueo, `404`), contraseña (rechazo del código vuelve a
  verificación, recarga vuelve a verificación), límite con cuenta atrás, ninguna pantalla con el
  correo y `axe-core` en cada pantalla (CF-5).
- Manual: el recorrido de `resumen.md` en la web con el correo del proveedor local (CF-7).

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-06, M-10, M-13 | API + frontend |
| RF-002 | M-10, M-12 | frontend |
| RF-003 | M-10, M-12 | frontend |
| RF-004 | M-08, M-09, M-10 | frontend |
| RF-005 | M-09, M-11, M-13 | frontend |
| RF-006 | M-01, M-11 | servicio + frontend |
| RF-007 | M-01, M-03, M-11 | servicio + API + frontend |
| RF-008 | M-01, M-11 | servicio + frontend |
| RF-009 | M-01, M-11 | servicio + frontend |
| RF-010 | M-01, M-02, M-03, M-11 | servicio + API + frontend |
| RF-011 | M-11 | frontend |
| RF-012 | M-01, M-03, M-11 | servicio + API |
| RF-013 | M-01, M-03, M-11, M-12 | servicio + API + frontend + casos compartidos |
| RF-014 | M-01, M-05 | servicio |
| RF-015 | M-09, M-11 | frontend |
| RF-016 | M-01, M-03, M-11 | equivalencia + API + frontend |
| RF-017 | M-01, M-02, M-03, M-07 | equivalencia |
| RF-018 | M-05, M-10 | servicio + API + frontend |
| RF-019 | M-03, M-04 | API |
| RF-020 | M-01, M-07 | servicio + equivalencia |
| RF-021 | M-03, M-06, M-08, M-14 | API |
| RF-022 | M-03, M-08, M-10, M-11 | API + frontend |
| RF-023 | M-04 | servicio |
| RF-024 | M-08, M-10, M-11 | frontend |

## RF sin cobertura
Ninguno.
