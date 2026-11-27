# Plan: deshabilitar-cuenta
Estado: aprobado

## Módulos

### M-01 Modelo preliminar de empresas (`apps.companies`)
Responsabilidad: Definir la entidad mínima `Company` (`name` sin unicidad obligatoria, `owner` FK protegida al usuario propietario actual y `created_at`), exponer helpers de consulta de propiedad (`owns_company`), registrar el modelo en el panel de administración interno y aportar un comando de consola para crear/gestionar empresas de prueba (`P-03`), dejando la gestión por usuario final para el Módulo II.
RF: RF-002, RF-003, RF-011, RF-015

### M-02 Ciclo de vida de deshabilitación y reactivación (`apps.accounts.models`, `apps.accounts.disable`, `apps.accounts.conf`)
Responsabilidad: Añadir `disabled_at` en `User` (sincronizado automáticamente en UTC al desactivar por cualquier vía y limpiado al reactivar), implementar el cálculo configurable de 12 meses calendario en UTC (`ACCOUNT_DISABLE_RETENTION_MONTHS`, con 29 de febrero → 28 de febrero en años no bisiestos), implementar `disable_account(...)` de forma atómica (validando en orden: propiedad de empresa → último superusuario activo → bloqueo temporal → contraseña actual; desactivando cuenta, revocando todas las sesiones web/escritorio, invalidando `PasswordResetRequest` pendientes, emitiendo `account_disabled` para auditoría y encolando el aviso `account_disabled` en la bandeja de salida), e implementar `reactivate_account(...)` rechazando cuentas con 12 meses o más transcurridos.
RF: RF-001, RF-003, RF-004, RF-005, RF-006, RF-007, RF-009, RF-010, RF-012, RF-016

### M-03 Límites de reautenticación de baja (`apps.accounts.throttling`, `apps.accounts.conf`)
Responsabilidad: Añadir contador de fallos y bloqueo temporal independiente en caché para la deshabilitación de cuenta (`account-disable:attempts:<user_id>` y `account-disable:lock:<user_id>`), separado del contador de cambio de contraseña y configurable por entorno (`ACCOUNT_DISABLE_MAX_FAILED_ATTEMPTS=5`, `ACCOUNT_DISABLE_ATTEMPT_WINDOW_MINUTES=5`, `ACCOUNT_DISABLE_LOCKOUT_MINUTES=5`), con función de consulta sin consumo (`check_account_disable`) para informar los segundos restantes al cargar `/profile`.
RF: RF-005, RF-014

### M-04 Administración de soporte y comandos de consola (`apps.accounts.admin`, `apps.accounts.management.commands`)
Responsabilidad: Exponer `User` en el panel de administración con `SimpleHistoryAdmin`, restringiendo la reactivación de cuentas deshabilitadas al grupo «Soporte técnico» y superusuarios (rechazando si otro `staff` intenta reactivar o si han pasado 12 meses calendario), conservando la auditoría de autor en `HistoricalUser` y añadiendo comandos de consola (`manage.py`) para deshabilitar, reactivar y ejecutar la purga manual (`P-03`).
RF: RF-001, RF-002, RF-009, RF-010, RF-015

### M-05 Purga periódica tras 12 meses (`apps.core.models`, `apps.accounts.tasks`, `backend/config/settings.py`)
Responsabilidad: Añadir `PURGE_DISABLED_ACCOUNTS` a `MaintenanceTaskName` como cuarta tarea monitorizada integrada con `run_maintenance_task` (`tareas-purga-y-alertas`), programada diariamente por defecto (`PURGE_DISABLED_ACCOUNTS_INTERVAL_SECONDS=86400`), para eliminar físicamente cuentas cuya `disabled_at` alcance o supere el plazo configurado (conservando `HistoricalUser` y `SecurityEvent`), omitiendo cuentas que por anomalía aún posean una empresa, continuando el borrado del resto del lote, registrando la traza en logs y elevando un error controlado al finalizar el lote si hubo omisiones para generar la alerta operativa correspondiente.
RF: RF-011, RF-015

### M-06 Contratos HTTP de perfil, baja y login (`apps.accounts.api.profile_views`, `apps.accounts.api.profile_serializers`, `apps.accounts.api.auth_views`, `apps.accounts.api.urls`, `apps.accounts.api.messages`)
Responsabilidad: Ampliar `GET browser/v1/auth/profile` y `GET app/v1/auth/profile` con `can_disable`, `disable_block_reason` (`"owns_company" | "last_superuser" | null`) y `disable_retry_after`; exponer `POST browser/v1/auth/account/disable` (CSRF) y `POST app/v1/auth/account/disable` (token en cabecera) protegidos con `_require_auth(..., require_terms=True)` y mensajes localizados en `es`, `pt-BR` y `en`; y ajustar `AppLoginView._authenticate` para que, cuando las credenciales correspondan a una cuenta deshabilitada, sume al límite de intentos y registre `inactive_account` mediante `adapter.record_inactive_login_attempt` devolviendo `account_disabled` (dentro de 12 meses) o `account_disabled_expired` (plazo vencido), manteniendo `invalid_credentials` neutro en cualquier otro fallo.
RF: RF-001, RF-003, RF-004, RF-005, RF-008, RF-013, RF-015, RF-016

### M-07 Interfaz en `/profile` y `/login` (`frontend/src/api/profile.ts`, `frontend/src/auth/ProfilePage.tsx`, `frontend/src/auth/LoginPage.tsx`, `frontend/src/i18n/`, `frontend/src/registration/serverErrors.ts`)
Responsabilidad: Añadir `disableAccount` en el cliente API y extender `ProfileData`; habilitar la opción `disable` en el menú de acciones de `/profile` para abrir la vista/confirmación en dos pasos conforme a `docs/identidad-visual.md` (consecuencias, bloqueo preventivo si es dueño de empresa o último superusuario, campo de contraseña actual con visibilidad, validación local en `onBlur`/envío, errores bajo campo o generales y cuenta atrás inicializada con `disable_retry_after` persistente al recargar); al completarse la baja, limpiar la credencial/sesión local y redirigir a `/login` con aviso informativo de baja y soporte; y traducir `account_disabled` y `account_disabled_expired` en `/login` en `es`, `pt-BR` y `en`.
RF: RF-001, RF-003, RF-004, RF-005, RF-008, RF-013, RF-014, RF-015, RF-016

## Modelo de datos

### Ampliación de `accounts.User`
- `disabled_at`: `DateTimeField(null=True, blank=True, db_index=True)`. Registra la marca temporal exacta en UTC de la deshabilitación. Se asigna automáticamente en `User.save()` cuando `is_active` cambia de `True` a `False` (si está vacío), y se limpia a `None` cuando `is_active` cambia de `False` a `True`. Queda cubierto por `HistoricalRecords` para conservar la trazabilidad de deshabilitaciones y reactivaciones.

### Nuevo modelo `companies.Company` (preliminar)
- `name`: `CharField(max_length=150)` (normalizado sin espacios iniciales ni finales y no vacío; sin restricción de unicidad).
- `owner`: `ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_companies")` (un usuario puede ser propietario actual de una o varias empresas).
- `created_at`: `DateTimeField(auto_now_add=True)`.

### Ampliación de `core.MaintenanceTaskName`
- Añadir el valor `PURGE_DISABLED_ACCOUNTS = "purge_disabled_accounts"` a las opciones de `MaintenanceTaskName` en `MaintenanceTaskStatus` y `MaintenanceAlert`.

## Decisiones

### D-01 App dedicada `apps.companies` para el modelo preliminar de empresa
Elegida: Crear la app `apps.companies` con el modelo `Company` y su consulta pública `owns_company(user)`.
Descartada: Definir el modelo `Company` dentro de `apps.accounts`.
Motivo: Mantiene la separación de dominios de cara al futuro Módulo II de empresas, evitando migraciones futuras de traslado de tabla o acoplamiento estructural en `accounts`.

### D-02 Integridad referencial `PROTECT` en `Company.owner`
Elegida: Configurar `on_delete=models.PROTECT` en `Company.owner` además de la comprobación explícita previa en `disable_account` y en la tarea de purga.
Descartada: Usar `on_delete=models.CASCADE` o `SET_NULL`.
Motivo: Impide a nivel de base de datos que una cuenta propietaria de una empresa quede borrada por error o dejando empresas huérfanas; en la purga periódica se filtra/verifica antes de `delete()` para permitir el borrado parcial del resto del lote sin abortar por una excepción en la primera cuenta anómala.

### D-03 Sincronización automática de `disabled_at` en `User.save()`
Elegida: Asignar y limpiar `disabled_at` dentro del ciclo de guardado de `User` cuando transiciona `is_active`, además de fijarlo explícitamente en `disable_account` y `reactivate_account`.
Descartada: Asignar `disabled_at` únicamente en el servicio `disable_account`.
Motivo: Garantiza que cualquier desactivación manual desde el panel de administración interno también registre su fecha UTC para quedar sujeta al plazo de 12 meses y a la purga (`RF-009`), manteniendo una única fuente de verdad.

### D-04 Prioridad de validaciones en `disable_account`
Elegida: Comprobar en orden: (1) propiedad de empresa, (2) protección del último superusuario activo, (3) bloqueo temporal de throttling y (4) contraseña actual.
Descartada: Validar la contraseña actual antes de comprobar empresa o último superusuario.
Motivo: Evita que un usuario bloqueado por poseer empresa o ser el último superusuario consuma intentos de contraseña y reciba mensajes engañosos (`RF-003`, `RF-016`, `S-04`).

### D-05 Reutilización del adaptador de auditoría y throttling en `AppLoginView`
Elegida: Mantener la llamada a `adapter.record_inactive_login_attempt(django_request, user)` cuando el usuario autenticado está inactivo y devolver `account_disabled` o `account_disabled_expired` según el vencimiento de los 12 meses.
Descartada: Implementar un contador de fuerza bruta paralelo o una vista de login aparte para cuentas deshabilitadas.
Motivo: Conserva intactos el recuento único de intentos fallidos de `allauth` (`RF-006` de `auditoria-eventos-seguridad`) y el registro `inactive_account`, limitando el ajuste de `inicio-cierre-sesion` únicamente al código y mensaje de respuesta cuando las credenciales coinciden (`RF-008`).

### D-06 Cálculo de 12 meses calendario sin dependencias externas
Elegida: Calcular la fecha límite sumando `ACCOUNT_DISABLE_RETENTION_MONTHS` meses calendario sobre año/mes/día/hora UTC con sujeción al último día del mes destino (29 de febrero + 12 meses → 28 de febrero en año no bisiesto).
Descartada: Aproximar con `timedelta(days=365)` o añadir la dependencia `python-dateutil`.
Motivo: `timedelta(days=365)` falla en años bisiestos y `AGENTS.md` prohíbe añadir dependencias innecesarias cuando la aritmética estándar de `calendar.monthrange` cubre exactamente `RF-010`.

### D-07 Exposición del estado de baja dentro de `GET auth/profile`
Elegida: Incluir `can_disable`, `disable_block_reason` y `disable_retry_after` en el payload de `GET auth/profile` tanto para web como para escritorio.
Descartada: Crear un endpoint separado `GET auth/account/disable-status`.
Motivo: Evita una llamada adicional al cargar `/profile` y permite mostrar de inmediato el aviso proactivo de bloqueo y la cuenta atrás persistente tras recargar la página (`RF-003`, `RF-005`, `RF-014`).

### D-08 Confirmación en dos pasos integrada en el menú de acciones de `/profile`
Elegida: Habilitar la opción `disable` ya prevista en el menú de acciones de `ProfilePage.tsx` para abrir la vista de confirmación de deshabilitación dentro de `/profile` (sin nueva ruta).
Descartada: Crear una ruta separada `/profile/disable` o un formulario siempre visible debajo del perfil.
Motivo: Respeta el punto de entrada definido por el usuario en `/profile` y cumple `RF-014` con confirmación en dos pasos acorde a [identidad-visual.md](../../docs/identidad-visual.md).

## Estrategia de tests

- **Unitarios y de servicio (backend)**:
  - Cálculo exacto de 12 meses calendario (incluyendo 29 de febrero y umbral configurable) (`RF-010`).
  - Orden de validaciones en `disable_account` (empresa > último superusuario > bloqueo > contraseña) y contador independiente respecto a `change_password` (`RF-003`, `RF-004`, `RF-005`, `RF-016`).
  - `User.save()` fijando y limpiando `disabled_at`, y `Company.owner` con `PROTECT` (`RF-002`, `RF-009`).
- **Integración (backend + API + admin + Celery + CLI)**:
  - Flujo completo en `browser/v1/` (cookie + CSRF) y `app/v1/` (cabecera `X-Session-Token` sin CSRF): términos pendientes (403), deshabilitación exitosa, revocación inmediata de todas las sesiones y tokens en peticiones posteriores (401), invalidación de `PasswordResetRequest`, evento de auditoría `account_disabled` y correo en bandeja de salida (`RF-001`, `RF-006`, `RF-007`, `RF-013`, `RF-015`).
  - `AppLoginView` / `BrowserLoginView`: credenciales válidas en cuenta deshabilitada (< 12 meses → `account_disabled`; ≥ 12 meses → `account_disabled_expired`), conteo de fuerza bruta y bloqueo, auditoría `inactive_account`, y respuesta neutra `invalid_credentials` con contraseña errónea o correo inexistente (`RF-008`).
  - Registro impedido mientras sigue deshabilitada (`email_has_account` sin aviso «ya tienes cuenta») y permitido tras purga física (`RF-011`, `RF-012`).
  - Panel de administración (`UserAdmin` y `CompanyAdmin`): permisos de «Soporte técnico» vs otro `staff` vs superusuario, rechazo tras 12 meses, historial conservado (`RF-002`, `RF-009`, `RF-010`).
  - Tarea periódica `purge_disabled_accounts` integrada en `run_maintenance_task` (`tareas-purga-y-alertas`): purga física de cuentas vencidas, conservación de `HistoricalUser` y `SecurityEvent`, purga parcial omitiendo cuentas con empresa y generando `MaintenanceAlert` + correo operativo, y verificación por comandos CLI (`RF-011`, `RF-015`).
- **Frontend (Vitest + Testing Library + a11y)**:
  - `ProfilePage.test.tsx`: menú con `disable` habilitado, vista de confirmación en dos pasos, aviso preventivo por empresa o último superusuario, validación local de contraseña actual, errores por campo y generales, cuenta atrás persistente al cargar con `disable_retry_after`, limpieza de token/sesión y redirección a `/login` tras baja exitosa (`RF-001`, `RF-003`, `RF-004`, `RF-005`, `RF-013`, `RF-014`, `RF-016`).
  - `LoginPage.test.tsx`: aviso de confirmación post-baja tras redirección y renderizado de `account_disabled` y `account_disabled_expired` en `es`, `pt-BR` y `en` (`RF-008`, `RF-014`).

## Trazabilidad

| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-02, M-04, M-06, M-07 | Integración + Frontend |
| RF-002 | M-01, M-04 | Unitario + Integración |
| RF-003 | M-01, M-02, M-06, M-07 | Unitario + Integración + Frontend |
| RF-004 | M-02, M-06, M-07 | Unitario + Integración + Frontend |
| RF-005 | M-02, M-03, M-06, M-07 | Unitario + Integración + Frontend |
| RF-006 | M-02, M-06 | Integración |
| RF-007 | M-02 | Integración |
| RF-008 | M-06, M-07 | Integración + Frontend |
| RF-009 | M-02, M-04 | Unitario + Integración |
| RF-010 | M-02, M-04 | Unitario + Integración |
| RF-011 | M-01, M-05 | Integración |
| RF-012 | M-02 | Integración |
| RF-013 | M-06, M-07 | Integración + Frontend |
| RF-014 | M-03, M-06, M-07 | Frontend + a11y |
| RF-015 | M-01, M-04, M-05, M-06, M-07 | Integración (CLI + Web + App) |
| RF-016 | M-02, M-06, M-07 | Unitario + Integración + Frontend |

## RF sin cobertura
ninguno

## Nota de coordinación entre specs
Antes de implementar `M-05` y `M-06`, se formalizarán mediante `sdd-cambio` los ajustes correspondientes en `specs/inicio-cierre-sesion/spec.md` (`RF-002`, excepción para credenciales válidas en cuentas deshabilitadas según `S-06`) y `specs/tareas-purga-y-alertas/spec.md` (ampliación de tres a cuatro tareas monitorizadas según `S-10`).
