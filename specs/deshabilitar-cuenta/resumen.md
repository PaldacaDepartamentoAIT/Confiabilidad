# Resumen — deshabilitar-cuenta

## Qué se hizo
Se completó el ciclo de autodeshabilitación segura de cuentas de usuario con bloqueo preventivo por propiedad de empresa (modelo preliminar) o protección del último superusuario activo, revocación inmediata de sesiones y restablecimientos pendientes, reactivación por soporte técnico dentro de 12 meses calendario en UTC y purga física periódica transcurrido ese plazo, junto con los clientes web y de escritorio. Cada entrega tiene su resumen en [`entregas/`](entregas/).

**Backend** (`backend/apps/`):
- **Modelo preliminar de empresas (`E-01`, `apps/companies/`):** nuevo modelo `Company` (`name` normalizado sin restricción de unicidad, `owner` con `on_delete=models.PROTECT` y `created_at`), helper `owns_company(user)`, registro en Django Admin (`CompanyAdmin`) y comandos CLI `manage.py company {create,list,delete}`.
- **Fecha de deshabilitación y límites (`E-01`, `E-02`, `accounts/models.py`, `accounts/throttling.py`, `accounts/conf.py`):** campo `User.disabled_at` (sincronizado automáticamente en UTC al pasar `is_active` de `True` a `False` y limpiado al reactivar, cubierto por `HistoricalRecords`) y contador independiente de reautenticación para baja (`5` intentos en `5` minutos con bloqueo de `5` minutos por defecto, consultable sin consumo mediante `check_account_disable`), además de `ACCOUNT_DISABLE_RETENTION_MONTHS=12`.
- **Servicio de baja, reactivación y purga (`E-02`, `E-03`, `E-04`, `accounts/disable.py`, `accounts/tasks.py`, `apps/core/`):**
  - `disable_account`: valida por orden prioritario propiedad de empresa (`owns_company`) → último superusuario activo (`last_superuser` con `select_for_update()`) → bloqueo temporal → contraseña actual; desactiva atómicamente la cuenta, revoca todas las sesiones web y de escritorio (`UserSession` y caché), invalida `PasswordResetRequest` pendientes sustituyéndolos por tumbas `PhantomProcess(answers_expired=True)`, registra evento de auditoría `ACCOUNT_DISABLE`, encola el aviso `account_disabled` en el idioma de la cuenta y mantiene reservado el correo para nuevos registros sin enviar «ya tienes cuenta».
  - `reactivate_account` y `UserAdmin`: cálculo exacto de 12 meses calendario en UTC con `calendar.monthrange` (29 de febrero vence el 28 de febrero en años no bisiestos), reactivación permitida al grupo «Soporte técnico» y superusuarios dentro del plazo conservando contraseña y consentimientos (y trazabilidad de autor en `HistoricalUser`), bloqueada para otro `staff` y rechazada tras vencer los 12 meses; comandos CLI `manage.py account {disable,reactivate}`.
  - Cuarta tarea periódica `purge_disabled_accounts` integrada en `MaintenanceTaskName` (`tareas-purga-y-alertas`), programada diariamente en `CELERY_BEAT_SCHEDULE` (`86400 s` por defecto) y ejecutable con `manage.py maintenance_tasks run purge_disabled_accounts`: elimina físicamente cuentas vencidas conservando `HistoricalUser` y `SecurityEvent` (liberando el correo), respeta heredadas sin `disabled_at` y realiza purga parcial si alguna cuenta vencida conservara empresa, registrando el error y disparando `MaintenanceAlert`.
- **API dual y login de cuentas deshabilitadas (`E-05`, `accounts/api/`):** ampliación de `GET`/`PATCH auth/profile` con `can_disable`, `disable_block_reason` y `disable_retry_after`; endpoints `POST /api/{browser,app}/v1/auth/account/disable` protegidos por sesión y términos vigentes (`403 terms_required`), CSRF en `browser` y exención en `app`; y ajuste en `AppLoginView._authenticate` para que credenciales válidas de una cuenta deshabilitada sumen al límite de intentos, auditen `inactive_account` y devuelvan `account_disabled` (< 12 meses, con correo de soporte) o `account_disabled_expired` (≥ 12 meses), manteniendo `invalid_credentials` neutro en cualquier otro caso.

**Frontend** (`frontend/src/`):
- **Cliente, errores globales en *toast* y `/login` (`E-06a`, `api/profile.ts`, `LoginPage.tsx`, `useFormValidation.ts`, `ToastProvider.tsx`, `serverErrors.ts`):** función `disableAccount`, ampliación de `ProfileData`, comunicación de aviso post-baja en `sessionStorage`, presentación de errores generales de formulario mediante notificación flotante de error (`.toast-error`) y mensajes traducidos (`es`, `pt-BR`, `en`) en `/login` para cuentas deshabilitadas y confirmación tras baja.
- **Confirmación en dos pasos desde `/profile` (`E-06b`, `ProfilePage.tsx`):** opción «Deshabilitar» habilitada en el menú contextual de la tarjeta de perfil; paso 1 con consecuencias y bloqueo preventivo (`<Notice>` y botón deshabilitado) ante propiedad de empresa o último superusuario; paso 2 con contraseña actual (mostrar/ocultar, validación local en `onBlur` y envío, vaciado selectivo y cuenta atrás persistente inicializada con `disable_retry_after`); al completarse, limpia sesión/token, marca el aviso y redirige a `/login`.

### Entregas
| Entrega | Rama | PR |
|---|---|---|
| E-01 Modelo preliminar de empresas (`apps.companies`), `disabled_at` en `User` y CLI | `feat/deshabilitar-cuenta-empresas` | Fusionada en `feat/deshabilitar-cuenta` |
| E-02 Servicio de deshabilitación, límites, revocación y CLI | `feat/deshabilitar-cuenta-servicio` | Fusionada en `feat/deshabilitar-cuenta` |
| E-03 Reactivación por soporte técnico en administración y consola (12 meses) | `feat/deshabilitar-cuenta-reactivacion` | Fusionada en `feat/deshabilitar-cuenta` |
| E-04 Purga periódica a los 12 meses en `tareas-purga-y-alertas` | `feat/deshabilitar-cuenta-purga` | Fusionada en `feat/deshabilitar-cuenta` |
| E-05 Endpoints HTTP de perfil ampliado, baja y login de cuentas deshabilitadas | `feat/deshabilitar-cuenta-api` | Fusionada en `feat/deshabilitar-cuenta` |
| E-06a Cliente API, traducciones, *toast* de error global y avisos en `/login` | `feat/deshabilitar-cuenta-ui-login` | Fusionada en `feat/deshabilitar-cuenta` |
| E-06b Confirmación en dos pasos desde `/profile` (web y escritorio) | `feat/deshabilitar-cuenta-ui-perfil` | `#168` |

## Cómo probarlo

### En el navegador (o en el cliente de escritorio)
1. Levanta los servicios de desarrollo:

```bash
docker compose -f docker/docker-compose.yml up -d db redis backend worker frontend
```
Deberías ver los cinco servicios en marcha.

2. Inicia sesión en `http://localhost:5173/login` con una cuenta de prueba (no propietaria de empresas y que no sea el último superusuario activo) con términos aceptados, ve a `/profile` y abre el menú vertical de tres puntos:
   - Verás habilitada la opción «Deshabilitar».
   - Si asocias una empresa preliminar a esa cuenta desde consola o admin (`manage.py company create`), al abrir «Deshabilitar» aparecerá de entrada el aviso de bloqueo y el botón «Continuar para confirmar» permanecerá deshabilitado.
3. Sin empresas asociadas, pulsa «Continuar para confirmar»:
   - Si envías el campo vacío verás «Completa este campo.» sin llamada al servidor.
   - Si fallas la contraseña actual `5` veces seguidas en `5` minutos, verás la cuenta atrás de espera y el botón deshabilitado incluso si recargas `/profile` y vuelves a abrir «Deshabilitar».
   - Al introducir la contraseña actual correcta y confirmar, el cliente limpiará la sesión y te redirigirá a `/login` mostrando el aviso de cuenta deshabilitada (y cualquier otra sesión abierta perderá acceso de inmediato).
4. En `/login`, intenta iniciar sesión con el correo y contraseña correctos de esa cuenta recién deshabilitada: verás el aviso de cuenta deshabilitada con contacto a soporte durante el plazo de 12 meses.

### Con `curl` en cliente `app` (sin frontend)
Inicia sesión con una cuenta activa y términos aceptados para obtener `<TOKEN>`:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"ana@planta.com","password":"turbina-compresor-7-marea"}'
```
Deberías ver `session_token` en el JSON de respuesta.

Consulta la elegibilidad de baja en `/auth/profile`:

```bash
curl -s http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <TOKEN>"
```
Deberías ver `can_disable`, `disable_block_reason` (`null`, `"owns_company"` o `"last_superuser"`) y `disable_retry_after`.

Deshabilita la cuenta enviando la contraseña actual:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/account/disable -H "Content-Type: application/json" -H "X-Session-Token: <TOKEN>" -d '{"current_password":"turbina-compresor-7-marea"}'
```
Deberías ver `{"result":"account_disabled"}`.

Comprueba que `<TOKEN>` quedó invalidado al instante y que el login informa de cuenta deshabilitada:

```bash
curl -i -s http://localhost:8000/api/app/v1/auth/profile -H "X-Session-Token: <TOKEN>"
```
Deberías ver HTTP `401` (`unauthenticated`).

```bash
curl -i -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"ana@planta.com","password":"turbina-compresor-7-marea"}'
```
Deberías ver HTTP `400` con código `account_disabled`.

### Desde consola (`manage.py`)
Crea o lista empresas preliminares de prueba para verificar el bloqueo `owns_company`:

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py company create --email ana@planta.com --name "Planta Norte"
```
Deberías ver la empresa creada asociada a la cuenta; mientras exista, `account disable` y `/auth/account/disable` rechazarán la baja sin evaluar contraseña.

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py company list --email ana@planta.com
```
Deberías ver el `<COMPANY_ID>` de la empresa; puedes borrarla con `delete --id <COMPANY_ID>` cuando quieras habilitar la baja.

Deshabilita y reactiva una cuenta desde consola, o ejecuta la purga periódica manualmente:

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py account disable --email ana@planta.com
```
Deberías ver la confirmación de cuenta deshabilitada tras introducir la contraseña actual sin eco (`getpass`).

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py account reactivate --email ana@planta.com
```
Deberías ver la cuenta reactivada (si no han transcurrido 12 meses calendario en UTC desde `disabled_at`).

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py maintenance_tasks run purge_disabled_accounts
```
Deberías ver el resultado de ejecución de la cuarta tarea periódica de mantenimiento.

### Tests y análisis estático
En el backend:

```bash
docker compose -f docker/docker-compose.yml exec backend pytest --cov --cov-report=term-missing
```
Deberías ver toda la suite de backend en verde (`2206 passed`, cobertura ≥ 80 %; en entorno dev pausa `confiabilidad-dev-worker-1` si compite por la cola Redis con los tests de worker real).

```bash
docker compose -f docker/docker-compose.yml exec backend sh -c "ruff check . && black --check . && mypy ."
```
Deberías ver todos los análisis estáticos limpios en `278` archivos.

En el frontend:

```bash
pnpm --filter frontend test
```
Deberías ver `69` archivos y `876` tests en verde.

```bash
pnpm --filter frontend lint && pnpm --filter frontend typecheck
```
Deberías ver ESLint y `tsc --noEmit` sin errores.

## Marco teórico

### Protección referencial `PROTECT` y prioridad de bloqueos
Cuando existen entidades críticas asociadas a un titular (como una empresa en `Company.owner`), borrar o desactivar al usuario sin control dejaría registros huérfanos o sin responsable operativo. Combinar `on_delete=models.PROTECT` en base de datos con una comprobación preventiva y prioritaria en `disable_account` (y en `/profile`) impide deshabilitar la cuenta antes siquiera de evaluar la contraseña, evitando que el usuario consuma intentos fallidos de reautenticación cuando no puede darse de baja. Lo mismo aplica al último superusuario activo, bloqueado con `select_for_update()` para evitar condiciones de carrera concurrentes.

### Plazo de retención de 12 meses calendario en UTC y años bisiestos
Aproximar un año como `365 días` falla en años bisiestos (desplaza un día la fecha límite). Calcular la fecha de caducidad sumando `12` meses calendario en UTC mediante `calendar.monthrange` mantiene la misma hora y día del mes, y ajusta el 29 de febrero al 28 de febrero en años no bisiestos. Guardar `disabled_at` automáticamente en `User.save()` garantiza que tanto la autodeshabilitación como cualquier desactivación manual desde el panel administrativo queden sujetas exactamente al mismo plazo.

### Purga física parcial e invalidación con tumbas (`PhantomProcess`)
Al deshabilitar una cuenta, un enlace o código previo de restablecimiento de contraseña no debe seguir activo si soporte reactiva la cuenta después; sustituir los procesos pendientes por `PhantomProcess(answers_expired=True)` los invalida de inmediato sin romper la trazabilidad. Cuando vencen los 12 meses y corre la purga periódica (`purge_disabled_accounts`), borrar cada cuenta vencida en su propia transacción permite continuar purgando el resto del lote si por anomalía alguna cuenta conservara una empresa, registrando además la alerta operativa en `tareas-purga-y-alertas` mientras preserva el historial y los eventos de auditoría.

### Excepción controlada a la neutralidad de login tras validar credenciales
En el flujo estándar (`inicio-cierre-sesion`), los fallos de acceso devuelven respuestas neutras para impedir enumerar correos. Sin embargo, cuando la persona introduce tanto el correo como la contraseña correctos de una cuenta deshabilitada, confirmar su estado (indicando si puede reactivar vía soporte dentro de los 12 meses o si el plazo venció) evita confundir al titular sin exponer cuentas ante contraseñas erróneas o correos inexistentes, manteniendo además el conteo en el limitador de fuerza bruta y la auditoría `inactive_account`.
