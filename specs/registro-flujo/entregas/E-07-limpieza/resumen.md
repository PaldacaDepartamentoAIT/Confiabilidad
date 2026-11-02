# Entrega E-07 · Limpieza programada y equivalencia completa

Rama: `feat/registro-flujo-limpieza` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#41](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/41) ·
Líneas de código y tests: 273 (límite: 400).

## Qué se hizo
- **Borrado de procesos antiguos** (RF-020): `registration.purge_stale` borra cada registro
  pendiente sin completar y cada plaza de registro cuyo código caducó hace 24 horas o más
  (`REGISTRATION_PURGE_AFTER_HOURS`), **con el mismo criterio y en la misma transacción para los
  dos**: así un registro real y una plaza pasan a «no encontrado» a la vez (RF-017, D-07). Las
  plazas del cambio de contraseña no se tocan.
- **Tarea programada**: `purge_stale_registrations` se ejecuta cada hora desde el planificador de
  Celery, así que un registro se borra entre 24 y 25 horas después de caducar su código (C-08).
- **Desde consola** (P-03): el subcomando `registration purge-stale` hace lo mismo y dice cuántos
  borró. La orden `registration purge`, que borra los caducados en cuanto caducan, sigue igual.
- **Equivalencia completa** (CF-2): un test recorre por la API un registro real cuyo código no se
  acierta y una plaza (consultar, reenviar, verificar hasta el bloqueo, completar, caducar) y
  comprueba que dan **las mismas respuestas, cabeceras y número de consultas** en cada paso. Otros
  tests comprueban que los dos pasan a `404` a la vez al repetir el registro y al borrarse, y que un
  identificador desconocido de cualquier forma da `404` sin escribir nada.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-025 | Borrado de procesos antiguos | `8506920` |
| T-026 | Tarea programada de borrado | `97f284b` |
| T-027 | Borrado desde consola | `0df4960` |
| T-028 | Equivalencia de plaza y registro real en el flujo | `64656f4` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, con Docker. Sin proveedor de correo configurado, el código se lee en
la salida del worker.

Levanta los servicios:
```bash
docker compose -f docker/docker-compose.yml up -d db redis backend worker beat
```
Aplica las migraciones:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py migrate
```
Inicia un registro desde la consola:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py registration start --email dora@example.com --name "Dora Gil" --birthdate 1990-05-10 --country es --language es
```
Envejece su código como si hubiera caducado hace 25 horas:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from datetime import timedelta; from django.utils import timezone; from apps.accounts.models import PendingRegistration; print(PendingRegistration.objects.filter(email='dora@example.com').update(code_expires_at=timezone.now() - timedelta(hours=25)))"
```
Deberías ver `1`. Borra los procesos antiguos:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py registration purge-stale
```
Deberías ver `deleted: 1` (o más, si había otros registros antiguos). La misma limpieza se puede
lanzar como tarea de Celery:
```bash
docker compose -f docker/docker-compose.yml exec backend celery -A config call apps.accounts.tasks.purge_stale_registrations
```
Deberías ver el identificador de la tarea; en la salida del worker aparece como ejecutada.

Los tests de la entrega, incluida la equivalencia completa:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_registration_flow_equivalence.py apps/accounts/tests/test_registration_flow.py apps/accounts/tests/test_registration_background.py apps/accounts/tests/test_registration_command.py
```
Deberías ver todos en verde.

## Marco teórico
### Por qué el borrado de registros y plazas va en la misma transacción
Un identificador que deja de existir responde `404`. Si los registros reales se borraran en una
operación y las plazas en otra, habría un instante en que un registro de un correo nuevo ya diera
`404` y la plaza de un correo con cuenta todavía no, o al revés: esa diferencia, aunque breve,
diría qué correos tienen cuenta. Borrarlos juntos, con el mismo criterio, cierra ese hueco.
