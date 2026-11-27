# Entrega E-02 · Servicio de deshabilitación con reautenticación, límites, revocación inmediata y CLI

Rama: `feat/deshabilitar-cuenta-servicio` · PR: pendiente · Líneas de código y tests: 498 (límite excepcional: 500).

## Qué se hizo
- En [settings.py](../../../../backend/config/settings.py), [conf.py](../../../../backend/apps/accounts/conf.py) y [throttling.py](../../../../backend/apps/accounts/throttling.py) se añadió la configuración por entorno (`ACCOUNT_DISABLE_MAX_FAILED_ATTEMPTS=5`, `ACCOUNT_DISABLE_ATTEMPT_WINDOW_MINUTES=5`, `ACCOUNT_DISABLE_LOCKOUT_MINUTES=5`, `ACCOUNT_DISABLE_RETENTION_MONTHS=12`) y el contador independiente de reautenticación para deshabilitar cuenta (`check_account_disable`, `record_account_disable_failure`, `clear_account_disable_failures`), parametrizado con helpers compartidos para evitar duplicación con el cambio de contraseña (`RF-005` límite de intentos fallidos, `RF-010` plazo configurable).
- En [disable.py](../../../../backend/apps/accounts/disable.py) se implementó `disable_block_reason(user)` y la operación atómica `disable_account(...)` con orden de prioridad estricto (`owns_company` → `last_superuser` → `throttling` → contraseña actual) sin consumir intentos ni registrar fallos en rechazos previos, desactivando la cuenta con `disabled_at`, revocando todas las sesiones web y de escritorio, invalidando `PasswordResetRequest` pendientes mediante tumba `PhantomProcess`, registrando auditoría `account_disabled` y encolando el correo `account_disabled` en el idioma de la cuenta (`RF-001`, `RF-003`, `RF-004`, `RF-006`, `RF-007`, `RF-012`, `RF-016`).
- En [account.py](../../../../backend/apps/accounts/management/commands/account.py) se añadió el subcomando `manage.py account disable --email <EMAIL>` (`RF-015` verificación desde consola).
- En [test_disable_account.py](../../../../backend/apps/accounts/tests/test_disable_account.py) se añadieron tests unitarios y de integración para límites independientes, prioridad de bloqueos, último superusuario activo, revocación de sesiones/restablecimientos, auditoría, bandeja de salida, reserva de correo y CLI.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [tasks.md](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-003 | Límite configurable e independiente de reautenticación para deshabilitar cuenta | `0cea34f` |
| T-004 | Servicio atómico `disable_account` (empresa, último superusuario, reautenticación, revocación, auditoría y correo) y subcomando CLI | `cd03913` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con Docker, PostgreSQL y Redis levantados, actualiza las ramas remotas y cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/deshabilitar-cuenta-servicio
```
Ejecuta los tests de esta entrega (sin medir cobertura global de otros módulos; la cobertura ≥ 80 % se valida en la suite completa):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_disable_account.py -v --no-cov
```
Deberías ver los 11 tests de `test_disable_account.py` en verde.

Ejecuta la suite completa, el comprobador de tipos, el linter y el formateador:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver toda la suite en verde con cobertura ≥ 80 %.
```bash
docker compose -f docker/docker-compose.yml exec backend mypy .
```
Deberías ver `Success: no issues found`.
```bash
docker compose -f docker/docker-compose.yml exec backend ruff check .
```
Deberías ver `All checks passed!`.
```bash
docker compose -f docker/docker-compose.yml exec backend black --check .
```
Deberías ver `All done!`.

Para probar la baja desde consola usando el correo `<EMAIL>` de una cuenta activa existente (con su contraseña al solicitarse en consola):
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py account disable --email <EMAIL>
```
Deberías ver `disabled: <EMAIL>` si no es propietaria de ninguna empresa (si posee una empresa creada con `company create`, verás el rechazo indicando que debes transferirla o eliminarla primero).

## Marco teórico
### Tumba `PhantomProcess` al invalidar restablecimientos pendientes (`RF-006`)
Cuando una cuenta se deshabilita mientras tiene un código de restablecimiento de contraseña abierto (`PasswordResetRequest`), borrar sin más esa fila haría que un cliente que conserve el `public_id` viera un error distinto al de un código caducado o inexistente. Sustituirla por una entrada `PhantomProcess` marcada como caducada (`answers_expired=True`) elimina de inmediato la capacidad de completar el restablecimiento (incluso si soporte reactiva la cuenta después) manteniendo uniforme la respuesta externa.
