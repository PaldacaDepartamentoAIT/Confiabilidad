# Entrega E-03 · Reactivación por soporte técnico en administración y consola con regla de 12 meses

Rama: `feat/deshabilitar-cuenta-reactivacion` · PR: pendiente · Líneas de código y tests: 425 (límite excepcional: 500).

## Qué se hizo
- En [disable.py](../../../../backend/apps/accounts/disable.py) se implementaron `retention_deadline`, `is_retention_expired` y `reactivate_account` calculando `ACCOUNT_DISABLE_RETENTION_MONTHS` meses calendario exactos en UTC (incluyendo el ajuste del 29 de febrero al 28 de febrero en años no bisiestos), conservando contraseña y consentimientos al reactivar y limpiando `disabled_at` (`RF-009` reactivación por soporte técnico, `RF-010` bloqueo tras 12 meses).
- En [account.py](../../../../backend/apps/accounts/management/commands/account.py) se añadió el subcomando `manage.py account reactivate --email <EMAIL>` (`RF-015` verificación desde consola).
- En [admin.py](../../../../backend/apps/accounts/admin.py) se registró `UserAdmin(SimpleHistoryAdmin)` restringiendo la reactivación de cuentas inactivas al grupo «Soporte técnico» y superusuarios (mediante `has_change_permission`, `UserAdminForm.clean` y la acción `reactivate_selected`), rechazando cuentas vencidas (≥ 12 meses), protegiendo los campos de privilegios (`is_staff`, `is_superuser`, `groups`, `user_permissions`) como solo lectura para no superusuarios, registrando el autor en `HistoricalUser` e impidiendo revertir el historial por `POST` (`RF-009`, `RF-010`).
- En [test_reactivation_and_purge.py](../../../../backend/apps/accounts/tests/test_reactivation_and_purge.py) se añadieron tests unitarios, de CLI y de administración para la aritmética de calendario, reactivación antes/después del plazo, permisos de soporte vs otro `staff` y conservación del historial.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [tasks.md](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-005 | Servicio `reactivate_account` con regla de 12 meses calendario UTC (incluido 29 de febrero) y subcomando CLI | `c70e01b` |
| T-006 | Panel de administración de `User` con reactivación restringida a «Soporte técnico» y superusuarios | `66b64fb` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con Docker, PostgreSQL y Redis levantados, actualiza las ramas remotas y cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/deshabilitar-cuenta-reactivacion
```
Ejecuta los tests de esta entrega (sin medir cobertura global de otros módulos; la cobertura ≥ 80 % se valida en la suite completa):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_reactivation_and_purge.py -v --no-cov
```
Deberías ver los 5 tests de `test_reactivation_and_purge.py` en verde.

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

Para probar la reactivación desde consola usando el correo `<EMAIL>` de una cuenta deshabilitada hace menos de 12 meses:
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py account reactivate --email <EMAIL>
```
Deberías ver `reactivated: <EMAIL>` (y si superó los 12 meses, el error indicando que el plazo ha vencido).

## Marco teórico
### Aritmética de meses calendario frente a días fijos (`RF-010`)
Contar «12 meses» como `365 días` fijos introduce un desfase de un día en años bisiestos. Calcular los meses calendario sumando el número de meses sobre año y mes y ajustando el día al máximo válido del mes destino (`calendar.monthrange`) garantiza que un 29 de febrero venza exactamente el 28 de febrero del año siguiente no bisiesto a la misma hora UTC, de forma coherente con la regla de mayoría de edad del sistema.
