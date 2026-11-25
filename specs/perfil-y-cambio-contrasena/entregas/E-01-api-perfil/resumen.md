# Entrega E-01 · Servicio y comandos CLI de consulta y edición de perfil

Rama: `feat/perfil-y-cambio-contrasena-api-perfil` · PR: pendiente · Líneas de código y tests: 320 (límite: 400).

## Qué se hizo
- Se dividió la entrega original `E-01` en `E-01` (servicio + CLI, 320 líneas) y `E-01b` (endpoints HTTP `GET`/`PATCH auth/profile`, pendiente tras fusionar `E-01`) para mantener cada PR por debajo del límite de 400 líneas de código y tests.
- En `backend/apps/accounts/profile.py` se implementó `get_profile` (`RF-001`, consulta del perfil autenticado) y `update_profile` (`RF-002`, modificación de datos personales, y `RF-005`, edición sin cambios reales y auditoría de perfil):
  - lee exclusivamente `email`, `name`, `birthdate` y `country` sin exponer idioma guardado ni consentimientos;
  - admite actualización parcial mediante el centinela `UNSET` (`_Unset`), normaliza `name` y `country` y reutiliza `User.save(update_fields=...)` para validar las reglas de `usuario-personalizado`, conservar `"ZZ"` mientras el país no cambie y registrar la versión en `HistoricalRecords`;
  - compara los valores normalizados con los guardados y solo guarda y emite `signals.profile_edited` cuando al menos un campo cambia realmente.
- En `backend/apps/accounts/management/commands/profile.py` se añadieron los subcomandos `profile show --email ...` y `profile edit --email ... [--name ...] [--birthdate ...] [--country ...]` (`RF-015`, verificación desde consola) sobre cuentas activas (`User.active`).
- En `backend/apps/accounts/tests/test_profile_service.py` se añadieron tests unitarios y de CLI para lectura, edición parcial/completa, normalización, conservación y rechazo de `"ZZ"`, historial `HistoricalRecords`, no emisión de auditoría sin cambios reales y subcomandos CLI.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Servicio de consulta y edición parcial del perfil | `b06443b` |
| T-004 | Subcomandos CLI `profile show` y `profile edit` | `cc23074` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con Docker, PostgreSQL y Redis levantados, actualiza las ramas remotas y cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/perfil-y-cambio-contrasena-api-perfil
```
Ejecuta los tests nuevos de esta entrega (sin medir cobertura global de otros módulos; la cobertura ≥ 80 % se valida en la suite completa):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_profile_service.py -v --no-cov
```
Deberías ver los 6 tests de `test_profile_service.py` en verde.

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

Para probar el comando de consola sin frontend (usa el correo de una cuenta activa existente o créala primero con `registration`; `<EMAIL>` es ese correo):
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py profile show --email <EMAIL>
```
Deberías ver cuatro líneas con `email`, `name`, `birthdate` y `country`. Actualiza uno o varios campos:
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py profile edit --email <EMAIL> --name "Nombre Editado" --country br
```
Deberías ver el perfil actualizado con `country: BR` y `name: Nombre Editado`.

## Marco teórico
### Centinela `UNSET` y edición sin cambios reales (`RF-002`, `RF-005`)
En una actualización parcial hay tres estados posibles para cada campo: «no enviado», «enviado con valor distinto» y «enviado igual al actual (tras normalizar)». Usar un centinela propio (`UNSET`) en vez de `None` evita confundir un campo omitido con un valor nulo, y comparar cada valor ya normalizado frente al valor persistido evita escribir filas innecesarias en el historial (`HistoricalRecords`) y ruido en los eventos de auditoría (`SecurityEvent`) cuando el usuario guarda sin modificar nada real.
