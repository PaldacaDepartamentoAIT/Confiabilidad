# Tareas: deshabilitar-cuenta
Estado: aprobado

- [x] T-001 Campo `disabled_at` en `User` con sincronización en guardado
  RF: RF-009, RF-010 | Depende de: — | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_disable_account.py -k disabled_at` pasa verificando que pasar `is_active` de `True` a `False` (también en `User.save()` directo o administración) registra `disabled_at` en UTC, que reactivar limpia `disabled_at` a `None` y que `HistoricalRecords` guarda ambos cambios.
  Decisiones: sincronizar `disabled_at` dentro de `User._sync_disabled_at` en `User.save()` antes de `full_clean` y añadir `"disabled_at"` a `update_fields` cuando se guarde solo `is_active` (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo; `ruff` y `black` limpios). — Motivo: asegura que cualquier desactivación o reactivación desde modelo o administración registre o limpie la fecha UTC incluso con guardado parcial. — Confianza: [Probable]. — Cómo revertirla: revertir el commit de T-001.

- [x] T-002 Modelo preliminar `Company`, panel de administración y comando CLI
  RF: RF-002, RF-015 | Depende de: — | Archivos: 8
  Hecho cuando: `pytest apps/companies/tests/test_companies.py` pasa verificando creación sin unicidad de nombre, `on_delete=PROTECT` sobre `owner`, múltiples empresas por propietario, helper `owns_company`, alta/gestión en el panel de administración y ejecución de `manage.py company create --email <EMAIL> --name "..."` y `manage.py company list --email <EMAIL>`.
  Excepción: andamiaje inicial de la nueva app `apps.companies` (`__init__.py`, `apps.py`, `models.py`, `admin.py`, `migrations/0001_initial.py`, `management/commands/company.py`, `tests/test_companies.py`) más su registro en `backend/config/settings.py`.
  Decisiones: configurar `on_delete=models.PROTECT` en `Company.owner`, normalizar el nombre con `strip()` + `full_clean(validate_unique=False)` en `Company.save()`, exponer `owns_company(user)` y añadir `delete --id` en `manage.py company` para pruebas CLI (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo; `ruff` y `black` limpios). — Motivo: protege al propietario frente a borrados accidentales a nivel de BD y facilita crear/limpiar empresas desde consola (`P-03`). — Confianza: [Probable]. — Cómo revertirla: revertir el commit de T-002.

- [x] T-003 Límite configurable e independiente de reautenticación para deshabilitar cuenta
  RF: RF-005, RF-010 | Depende de: T-001 | Archivos: 4
  Hecho cuando: `pytest apps/accounts/tests/test_disable_account.py -k throttle` pasa verificando el contador independiente en caché (5 fallos en 5 minutos con bloqueo de 5 minutos por defecto), la lectura sin consumo (`check_account_disable`), la independencia frente a `change_password` y la configuración por entorno de límites y `ACCOUNT_DISABLE_RETENTION_MONTHS`.
  Excepción: la configuración por entorno se reparte entre `backend/config/settings.py` y `backend/apps/accounts/conf.py`, junto con el limitador en `backend/apps/accounts/throttling.py` y su test en `backend/apps/accounts/tests/test_disable_account.py`.
  Decisiones: extraer helpers parametrizados `_check_user_lock`, `_record_user_failure` y `_clear_user_failures` en `throttling.py` compartidos entre `password-change` y `account-disable` con prefijos de caché separados, y añadir `ACCOUNT_DISABLE_RETENTION_MONTHS` en `conf.py`/`settings.py` (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo; `ruff` y `black` limpios). — Motivo: evita duplicación manteniendo contadores totalmente independientes por operación. — Confianza: [Probable]. — Cómo revertirla: revertir el commit de T-003.

- [x] T-004 Servicio atómico `disable_account` (empresa, último superusuario, reautenticación, revocación, auditoría y correo) y subcomando CLI
  RF: RF-001, RF-003, RF-004, RF-005, RF-006, RF-007, RF-012, RF-015, RF-016 | Depende de: T-001, T-002, T-003 | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_disable_account.py` pasa verificando el orden prioritario (`owns_company` → `last_superuser` → `throttling` → contraseña actual sin consumir intentos en rechazos previos), desactivación atómica con `disabled_at`, revocación inmediata de sesiones web/escritorio (`UserSession` y caché), invalidación de `PasswordResetRequest` pendientes, evento de auditoría `account_disabled`, encolado en `outbox` en el idioma de la cuenta, impedimento de registro con el mismo correo sin aviso «ya tienes cuenta» y ejecución de `manage.py account disable --email <EMAIL>`.
  Decisiones: al deshabilitar, invalidar `PasswordResetRequest` sustituyéndolo por una tumba `PhantomProcess(answers_expired=True)` igual que en el borrado físico de `User`, bloquear filas de superusuarios activos con `select_for_update()` para evitar condición de carrera en `last_superuser` y exponer `disable_block_reason(user)` para consulta preventiva (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo; `ruff` y `black` limpios). — Motivo: evita que un enlace de restablecimiento previo quede usable tras una posible reactivación y protege la unicidad de al menos un superusuario activo bajo concurrencia. — Confianza: [Probable]. — Cómo revertirla: revertir el commit de T-004.

- [x] T-005 Servicio `reactivate_account` con regla de 12 meses calendario UTC (incluido 29 de febrero) y subcomando CLI
  RF: RF-009, RF-010, RF-015 | Depende de: T-001, T-004 | Archivos: 3
  Hecho cuando: `pytest apps/accounts/tests/test_reactivation_and_purge.py -k reactivate` pasa verificando la aritmética de 12 meses calendario en UTC (29 de febrero venciendo el 28 de febrero en año no bisiesto) y umbral configurable, reactivación exitosa antes del vencimiento conservando contraseña y consentimientos y limpiando `disabled_at`, rechazo al alcanzarse o superarse los 12 meses, y ejecución de `manage.py account reactivate --email <EMAIL>`.
  Decisiones: implementar `retention_deadline`, `is_retention_expired` y `reactivate_account` con `calendar.monthrange` en `disable.py` y el subcomando `account reactivate` sobre `User.objects` (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo; `ruff` y `black` limpios). — Motivo: evita dependencias externas y calcula con exactitud los 12 meses calendario en UTC incluyendo años bisiestos. — Confianza: [Probable]. — Cómo revertirla: revertir el commit de T-005.

- [x] T-006 Panel de administración de `User` con reactivación restringida a «Soporte técnico» y superusuarios
  RF: RF-009, RF-010 | Depende de: T-005 | Archivos: 2
  Hecho cuando: `pytest apps/accounts/tests/test_reactivation_and_purge.py -k admin` pasa verificando que miembros del grupo «Soporte técnico» y superusuarios pueden reactivar cuentas dentro de los 12 meses (conservando el autor en `HistoricalUser`), que otro personal `staff` queda impedido, que tras 12 meses el panel rechaza la reactivación y que desactivar manualmente desde admin registra `disabled_at`.
  Decisiones: registrar `UserAdmin(SimpleHistoryAdmin)` con `UserAdminForm` validando `is_support(request)` e `is_retention_expired` (además de `has_change_permission` bloqueando cuentas inactivas para otro `staff`), protegiendo campos de privilegios (`is_staff`, `is_superuser`, `groups`, `user_permissions`) como solo lectura para no superusuarios y bloqueando la reversión del historial por `POST` (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo; `ruff` y `black` limpios). — Motivo: evita escalada de privilegios por soporte y respeta la inmutabilidad del historial. — Confianza: [Probable]. — Cómo revertirla: revertir el commit de T-006.

- [x] T-007 Lógica de purga parcial de cuentas deshabilitadas vencidas tras 12 meses
  RF: RF-011, RF-012 | Depende de: T-002, T-005 | Archivos: 2
  Hecho cuando: `pytest apps/accounts/tests/test_reactivation_and_purge.py -k purge_accounts` pasa verificando la eliminación física de cuentas con `disabled_at` vencido (conservando `HistoricalUser` y `SecurityEvent` y liberando el correo para un nuevo registro), la preservación de cuentas sin `disabled_at` heredadas, y la omisión parcial sin abortar el resto del lote si alguna cuenta vencida conservara una empresa.
  Decisiones: ejecutar el borrado físico por cada cuenta vencida en su propia transacción atómica dentro de `purge_expired_accounts`, registrando el `id` en logs sin correo en claro y elevando `DisabledAccountPurgeAnomaly` al finalizar si hubo cuentas omitidas por empresa (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo; `ruff` y `black` limpios). — Motivo: garantiza que una anomalía de empresa en una cuenta no haga rollback sobre las cuentas válidas ya purgadas y permite al runner de mantenimiento registrar la alerta operativa. — Confianza: [Probable]. — Cómo revertirla: revertir el commit de T-007.

- [x] T-008 Cuarta tarea periódica `purge_disabled_accounts` integrada en `tareas-purga-y-alertas`, Celery Beat y CLI
  RF: RF-011, RF-015 | Depende de: T-007 | Archivos: 7
  Hecho cuando: `pytest apps/accounts/tests/test_reactivation_and_purge.py -k maintenance` pasa verificando el registro en `MaintenanceTaskName`, programación diaria configurable en `CELERY_BEAT_SCHEDULE`, ejecución mediante `run_maintenance_task` y `manage.py maintenance_tasks run purge_disabled_accounts` (incluido `simulate-failure`), y generación de `MaintenanceAlert` + correo operativo cuando el lote omite alguna cuenta por empresa anómala.
  Excepción: añade `PURGE_DISABLED_ACCOUNTS` en `apps/core/models.py` (con su migración en `apps/core/migrations/`), registra la tarea en `apps/core/management/commands/maintenance_tasks.py`, implementa la tarea Celery en `apps/accounts/tasks.py`, configura `CELERY_BEAT_SCHEDULE` en `backend/config/settings.py`, documenta la variable en `backend/.env.example` (exigido por `test_maintenance_command.py`) y cubre el flujo en `apps/accounts/tests/test_reactivation_and_purge.py`.
  Decisiones: integrar `purge_disabled_accounts` mediante `run_maintenance_task` con `PURGE_DISABLED_ACCOUNTS_INTERVAL_SECONDS=86400` y documentar la variable en `.env.example` para mantener consistencia con `test_env_example_documents_all_maintenance_variables` (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo; `ruff` y `black` limpios). — Motivo: aprovecha el bloqueo distribuido, historial de estado y alertas operativas ya existentes sin duplicar infraestructura. — Confianza: [Probable]. — Cómo revertirla: revertir el commit de T-008.

- [x] T-009 Extensión de `GET auth/profile` con estado de baja, serializador y mensajes multiidioma
  RF: RF-003, RF-004, RF-005, RF-014, RF-016 | Depende de: T-004 | Archivos: 5
  Hecho cuando: `pytest apps/accounts/tests/test_disable_api.py -k profile_eligibility` pasa verificando `can_disable`, `disable_block_reason` (`"owns_company"`, `"last_superuser"` o `null`) y `disable_retry_after` en `GET auth/profile` para web y escritorio, el serializador de contraseña actual y los mensajes localizados en `es`, `pt-BR` y `en`.
  Excepción: añade la proyección en `apps/accounts/api/profile_views.py`, el serializador en `apps/accounts/api/profile_serializers.py`, los textos localizados en `apps/accounts/api/messages.py`, su test en `apps/accounts/tests/test_disable_api.py` y actualiza las aserciones de igualdad exacta del payload en `apps/accounts/tests/test_profile_api.py`.
  Decisiones: incluir `can_disable`, `disable_block_reason` y `disable_retry_after` en `_profile_payload` (compartido por `GET` y `PATCH auth/profile`) para que la UI conserve el estado actualizado tras editar el perfil, e incluir `%(support_email)s` en el mensaje `account_disabled` (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo; `ruff` y `black` limpios). — Motivo: evita desincronizar el estado de elegibilidad tras un `PATCH` en `/profile` y muestra al usuario la dirección configurada de soporte. — Confianza: [Probable]. — Cómo revertirla: revertir el commit de T-009.

- [x] T-010 Endpoints `POST auth/account/disable` (web y escritorio) y rechazo informativo en login
  RF: RF-001, RF-003, RF-004, RF-005, RF-006, RF-007, RF-008, RF-013, RF-015, RF-016 | Depende de: T-009 | Archivos: 5
  Hecho cuando: `pytest apps/accounts/tests/test_disable_api.py apps/accounts/tests/test_auth_neutrality.py` pasa verificando `POST browser/v1/auth/account/disable` (CSRF) y `POST app/v1/auth/account/disable` (`X-Session-Token`), rechazo `403 terms_required` sin términos vigentes, `400` prioritario por `owns_company`/`last_superuser` o `current_password_incorrect`, `429` con `Retry-After`, revocación inmediata `401` en todas las sesiones activas tras `200`, y login devolviendo `account_disabled` (< 12 meses) o `account_disabled_expired` (≥ 12 meses) con credenciales válidas (sumando a fuerza bruta y auditoría `inactive_account`) frente a `invalid_credentials` neutro si falla la clave.
  Excepción: conecta rutas en `apps/accounts/api/urls.py`, la vista de baja en `apps/accounts/api/profile_views.py`, el ajuste en `AppLoginView._authenticate` en `apps/accounts/api/auth_views.py`, sus pruebas en `apps/accounts/tests/test_disable_api.py` y actualiza las aserciones de `inactive_right` en `apps/accounts/tests/test_auth_neutrality.py`.
  Decisiones: evaluar `disable_block_reason(user)` y `throttling.check_account_disable(user.pk)` en `AppAccountDisableView.post` antes de parsear o validar `current_password`, y emitir `account_disabled` / `account_disabled_expired` en `AppLoginView._authenticate` manteniendo `adapter.record_inactive_login_attempt` (pendiente de ejecutar `pytest` y `mypy` en entorno con PostgreSQL/venv completo; `ruff` y `black` limpios). — Motivo: evita que un propietario de empresa o último superusuario consuma intentos de contraseña o reciba errores de campo, y conserva intacto el contador de fuerza bruta y la auditoría en el login. — Confianza: [Probable]. — Cómo revertirla: revertir el commit de T-010.

- [ ] T-011 Cliente `disableAccount`, `ProfileData` ampliado y traducciones en `es`, `pt-BR` y `en`
  RF: RF-001, RF-008, RF-014, RF-015 | Depende de: T-010 | Archivos: 6
  Hecho cuando: `pnpm --filter frontend test src/i18n/keys.test.ts src/i18n/locales/locales.test.ts src/registration/serverErrors.test.ts` y `pnpm --filter frontend typecheck` pasan verificando `disableAccount` y el tipado ampliado de `ProfileData` en `api/profile.ts`, el mapeo de `account_disabled`, `account_disabled_expired`, `owns_company` y `last_superuser` en `serverErrors.ts` y la paridad completa en los tres idiomas.
  Excepción: los tres archivos de idioma (`es.ts`, `pt-BR.ts`, `en.ts`) deben actualizarse juntos por `i18n/keys.test.ts`, junto con `api/profile.ts`, `serverErrors.ts` y `serverErrors.test.ts`.

- [ ] T-012 Mensajes específicos de cuenta deshabilitada y confirmación post-baja en `LoginPage`
  RF: RF-008, RF-014 | Depende de: T-011 | Archivos: 2
  Hecho cuando: `pnpm --filter frontend test src/auth/LoginPage.test.tsx` pasa verificando la visualización de `account_disabled` (soporte/12 meses) y `account_disabled_expired` en el formulario de acceso y el aviso informativo de confirmación cuando se llega redirigido tras deshabilitar la cuenta, en `es`, `pt-BR` y `en`.

- [ ] T-013 Interfaz de deshabilitación en dos pasos desde el menú de `/profile` con bloqueos preventivos y cuenta atrás persistente
  RF: RF-001, RF-003, RF-004, RF-005, RF-013, RF-014, RF-015, RF-016 | Depende de: T-011, T-012 | Archivos: 3
  Hecho cuando: `pnpm --filter frontend test src/auth/ProfilePage.test.tsx src/auth/a11y.test.tsx` pasa verificando la opción habilitada en el menú de acciones de `/profile`, el flujo en dos pasos acorde a `docs/identidad-visual.md`, el aviso preventivo con botón bloqueado ante empresa o último superusuario, la validación local y errores bajo campo/generales, la cuenta atrás persistente inicializada con `disable_retry_after` al cargar/recargar, la limpieza local de credenciales y redirección a `/login` con confirmación al completarse la baja, y accesibilidad con `axe-core` en `es`, `pt-BR` y `en`.

## Entregas
Rama de integración: `feat/deshabilitar-cuenta` (los PR de las entregas van contra ella; ver `AGENTS.md`).

- E-01 Modelo preliminar de empresas (`apps.companies`), `disabled_at` en `User` y CLI de empresas
  Tareas: T-001, T-002 | Líneas estimadas: 240 | Rama: `feat/deshabilitar-cuenta-empresas`
  Cómo probarlo: ejecutar `pytest apps/companies/tests/test_companies.py apps/accounts/tests/test_disable_account.py -k disabled_at` y probar `python manage.py company create --email <EMAIL> --name "Planta Norte"` y `python manage.py company list --email <EMAIL>`.

- E-02 Servicio de deshabilitación con reautenticación, límites, revocación inmediata y CLI
  Tareas: T-003, T-004 | Líneas reales: 498 | Rama: `feat/deshabilitar-cuenta-servicio`
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_disable_account.py` y verificar con `python manage.py account disable --email <EMAIL>` que rechaza si posee empresa, bloquea tras 5 fallos, revoca sesiones al completarse y registra auditoría y correo en bandeja de salida.
  Excepción: `T-003` (limitador y configuración) y `T-004` (servicio atómico `disable_account` y CLI) conforman un único corte vertical indivisible por debajo del tope excepcional de 500 líneas (`498`); separar `T-003` dejaría un limitador sin consumidor ni comportamiento funcional observable en la entrega.

- E-03 Reactivación por soporte técnico en administración y consola con regla de 12 meses
  Tareas: T-005, T-006 | Líneas reales: 425 | Rama: `feat/deshabilitar-cuenta-reactivacion`
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_reactivation_and_purge.py -k "reactivate or admin"` y verificar `python manage.py account reactivate --email <EMAIL>` y la reactivación desde Django Admin como miembro de «Soporte técnico» (< 12 meses permitido, ≥ 12 meses rechazado).
  Excepción: `T-005` (servicio y CLI) y `T-006` (panel de administración `UserAdmin` y pruebas conjuntas en `test_reactivation_and_purge.py`) cubren las dos vías de reactivación de `RF-009` y `RF-010` en un único corte por debajo del límite excepcional de 500 líneas (`425`).

- E-04 Purga periódica a los 12 meses integrada en `tareas-purga-y-alertas`
  Tareas: T-007, T-008 | Líneas reales: 255 | Rama: `feat/deshabilitar-cuenta-purga`
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_reactivation_and_purge.py` y correr `python manage.py maintenance_tasks run purge_disabled_accounts`, `python manage.py maintenance_tasks status` y `python manage.py maintenance_tasks simulate-failure purge_disabled_accounts`.

- E-05 Endpoints HTTP de perfil ampliado, baja de cuenta y login de cuentas deshabilitadas
  Tareas: T-009, T-010 | Líneas reales: 448 | Rama: `feat/deshabilitar-cuenta-api`
  Cómo probarlo: ejecutar `pytest apps/accounts/tests/test_disable_api.py apps/accounts/tests/test_auth_neutrality.py apps/accounts/tests/test_profile_api.py`, consultar `GET /api/app/v1/auth/profile` con token, llamar a `POST /api/app/v1/auth/account/disable` verificando el `401` inmediato en sesiones activas y probar `POST /api/app/v1/auth/login` con las credenciales de la cuenta deshabilitada.
  Excepción: `T-009` (extensión de perfil, serializador y catálogo de mensajes) y `T-010` (endpoint de baja, ajuste en login y pruebas integradas en `test_disable_api.py`) conforman un único corte vertical HTTP de 448 líneas reales dentro del tope excepcional de 500 líneas; separar `T-009` dejaría el serializador y los códigos de baja sin endpoint que los ejercite.

- E-06a Cliente API, traducciones y avisos de cuenta deshabilitada en `/login`
  Tareas: T-011, T-012 | Líneas estimadas: 260 | Rama: `feat/deshabilitar-cuenta-ui-login`
  Cómo probarlo: ejecutar `pnpm --filter frontend test src/auth/LoginPage.test.tsx src/registration/serverErrors.test.ts src/i18n/keys.test.ts src/i18n/locales/locales.test.ts` y comprobar en `/login` los avisos de confirmación y error en `es`, `pt-BR` y `en`.

- E-06b Confirmación en dos pasos desde el menú de `/profile` (web y escritorio)
  Tareas: T-013 | Líneas estimadas: 350 | Rama: `feat/deshabilitar-cuenta-ui-perfil`
  Cómo probarlo: ejecutar `pnpm --filter frontend test src/auth/ProfilePage.test.tsx src/auth/a11y.test.tsx`, abrir `/profile`, seleccionar «Deshabilitar cuenta» en el menú de acciones y verificar el bloqueo preventivo (con empresa o último superusuario), la cuenta atrás tras fallos y la redirección a `/login` tras confirmar.

## RF sin tarea
ninguno
