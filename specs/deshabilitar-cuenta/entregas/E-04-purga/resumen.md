# Entrega E-04 · Purga periódica a los 12 meses integrada en `tareas-purga-y-alertas`

Rama: `feat/deshabilitar-cuenta-purga` · PR: pendiente · Líneas de código y tests: 247 (límite: 400).

## Qué se hizo
- En [disable.py](../../../../backend/apps/accounts/disable.py) se implementó `purge_expired_accounts` y `DisabledAccountPurgeAnomaly`: elimina físicamente en transacciones individuales por cuenta las deshabilitadas cuyo `disabled_at` alcanza o supera los 12 meses calendario en UTC (conservando `HistoricalUser` y `SecurityEvent`, liberando el correo para nuevos registros y respetando cuentas sin `disabled_at`), omitiendo sin abortar el resto del lote aquellas que por anomalía conserven alguna empresa y dejando error en logs (`RF-011` purga periódica tras 12 meses, `RF-012` reserva de correo mientras esté deshabilitada).
- En [models.py](../../../../backend/apps/core/models.py), [0003_alter_maintenance_task_name_choices.py](../../../../backend/apps/core/migrations/0003_alter_maintenance_task_name_choices.py), [maintenance_tasks.py](../../../../backend/apps/core/management/commands/maintenance_tasks.py), [tasks.py](../../../../backend/apps/accounts/tasks.py), [settings.py](../../../../backend/config/settings.py) y [.env.example](../../../../backend/.env.example) se añadió `PURGE_DISABLED_ACCOUNTS` como cuarta tarea monitorizada en `tareas-purga-y-alertas`, programada diariamente por defecto (`PURGE_DISABLED_ACCOUNTS_INTERVAL_SECONDS=86400`) y operable desde CLI (`RF-011`, `RF-015` verificación desde consola).
- En [test_reactivation_and_purge.py](../../../../backend/apps/accounts/tests/test_reactivation_and_purge.py) se añadieron pruebas de purga física, conservación de historial/auditoría, liberación de correo, purga parcial ante empresa anómala, fallo simulado, alertas operativas y comando `maintenance_tasks`.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [tasks.md](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-007 | Lógica de purga parcial de cuentas deshabilitadas vencidas tras 12 meses | `784a571` |
| T-008 | Cuarta tarea periódica `purge_disabled_accounts` integrada en `tareas-purga-y-alertas`, Celery Beat y CLI | `a977215` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con Docker, PostgreSQL y Redis levantados, actualiza las ramas remotas y cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/deshabilitar-cuenta-purga
```
Aplica la migración nueva de `core`:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py migrate
```
Deberías ver aplicada `core.0003_alter_maintenance_task_name_choices`.

Ejecuta los tests de esta entrega y los de mantenimiento (sin medir cobertura global):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_reactivation_and_purge.py apps/core/tests/test_maintenance_command.py apps/core/tests/test_maintenance_models.py -v --no-cov
```
Deberías ver los tests de `test_reactivation_and_purge.py` y mantenimiento en verde.

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

Para probar la cuarta tarea y su estado desde consola:
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py maintenance_tasks run purge_disabled_accounts
```
Deberías ver `completed purge_disabled_accounts: deleted=<N>` (donde `<N>` es el número de cuentas vencidas eliminadas).
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py maintenance_tasks status
```
Deberías ver `purge_disabled_accounts` registrado junto al resto de tareas periódicas.

## Marco teórico
### Purga parcial por cuenta frente a transacción global (`RF-011`)
Si una tarea periódica de borrado envuelve todo el lote en una única transacción y lanza una excepción al encontrar un registro anómalo (una cuenta vencida que aún posee una empresa protegida por `PROTECT`), la base de datos deshace también los borrados válidos previos. Ejecutar el borrado físico de cada cuenta válida en su propia transacción y notificar las omisiones al final permite avanzar con las cuentas limpias mientras `run_maintenance_task` deja constancia del fallo y dispara la alerta operativa.
