# Entrega E-01 · Modelo preliminar de empresas (`apps.companies`), `disabled_at` en `User` y CLI de empresas

Rama: `feat/deshabilitar-cuenta-empresas` · PR: pendiente · Líneas de código y tests: 365 (límite: 400).

## Qué se hizo
- Se añadió el campo `disabled_at` (fecha y hora en UTC, indexado y anulable) en `accounts.User` y en su modelo histórico `HistoricalUser` mediante [0016_user_disabled_at.py](../../../../backend/apps/accounts/migrations/0016_user_disabled_at.py).
- En [models.py](../../../../backend/apps/accounts/models.py) se implementó `_sync_disabled_at` dentro de `User.save()`, de modo que toda transición de `is_active` de `True` a `False` (incluso usando `update_fields=["is_active"]` o desde administración) registra `disabled_at` en UTC, toda reactivación lo limpia a `None` y el historial conserva ambos cambios (`RF-009` reactivación por soporte, `RF-010` plazo de 12 meses).
- Se creó la app preliminar `apps.companies` ([models.py](../../../../backend/apps/companies/models.py), [admin.py](../../../../backend/apps/companies/admin.py), [0001_initial.py](../../../../backend/apps/companies/migrations/0001_initial.py)) y se registró en [settings.py](../../../../backend/config/settings.py), definiendo el modelo `Company` (`name` normalizado sin restricción de unicidad, `owner` con `on_delete=models.PROTECT` para impedir borrar propietarios con empresas activas y `created_at`) y el helper `owns_company(user)` (`RF-002` modelo preliminar de empresas).
- Se añadió el comando de consola [company.py](../../../../backend/apps/companies/management/commands/company.py) (`manage.py company create`, `list` y `delete`) para crear y verificar empresas preliminares sin depender del frontend (`RF-015` verificación desde consola).
- Se añadieron tests unitarios, de migración, administración y CLI en [test_disable_account.py](../../../../backend/apps/accounts/tests/test_disable_account.py) y [test_companies.py](../../../../backend/apps/companies/tests/test_companies.py).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [tasks.md](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Campo `disabled_at` en `User` con sincronización en guardado | `f3e735e` |
| T-002 | Modelo preliminar `Company`, panel de administración y comando CLI | `f4d6eba` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con Docker, PostgreSQL y Redis levantados, actualiza las ramas remotas y cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/deshabilitar-cuenta-empresas
```
Aplica las migraciones nuevas sobre la base de datos:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py migrate
```
Deberías ver aplicadas `accounts.0016_user_disabled_at` y `companies.0001_initial`.

Ejecuta los tests nuevos de esta entrega (sin medir cobertura global de otros módulos; la cobertura ≥ 80 % se valida en la suite completa):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/companies/tests/test_companies.py apps/accounts/tests/test_disable_account.py -v --no-cov
```
Deberías ver los 10 tests nuevos en verde.

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

Para probar el comando de consola de empresas preliminares usando el correo `<EMAIL>` de una cuenta activa existente (crea una antes con `seed_test_user` o `registration` si hace falta):
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py company create --email <EMAIL> --name "Planta Norte"
```
Deberías ver una línea con `id=<COMPANY_ID> name=Planta Norte owner=<EMAIL>`, usando ese `<COMPANY_ID>` si luego quieres borrar la empresa de prueba.
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py company list --email <EMAIL>
```
Deberías ver listada `Planta Norte` asociada a `<EMAIL>`.
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py company delete --id <COMPANY_ID>
```
Deberías ver `deleted=<COMPANY_ID>`.

## Marco teórico
### Integridad referencial `PROTECT` frente a `CASCADE` (`RF-002`, `RF-011`)
En una relación `ForeignKey`, `CASCADE` borra automáticamente los hijos al eliminar el padre, mientras que `PROTECT` lanza un error (`ProtectedError`) e impide el borrado mientras exista algún registro asociado. En el modelo preliminar `Company`, usar `PROTECT` sobre `owner` protege a nivel de base de datos contra cualquier borrado accidental de un usuario que aún figure como propietario de una empresa, reforzando la comprobación explícita de negocio y de purga periódica.
