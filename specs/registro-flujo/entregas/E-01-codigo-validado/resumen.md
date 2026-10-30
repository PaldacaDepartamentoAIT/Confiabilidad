# Entrega E-01 · Volver a presentar un código validado

Rama: `feat/registro-flujo-codigo-validado` · PR: pendiente ·
Líneas de código y tests: 228 (límite: 400).

## Qué se hizo
- Un código de registro ya validado se puede presentar de nuevo (RF-009 de `procesos-pendientes`,
  cambio del 2026-10-30, pedido por esta feature para RF-008 y RF-012):
  - el correcto se acepta otra vez sin cambiar nada mientras el proceso no haya caducado, aunque el
    código sí (durante la gracia de 15 minutos);
  - uno incorrecto suma un intento si el código está vigente, o da «código caducado» sin sumar si
    ya no lo está;
  - bloqueado o caducado, se rechaza incluso el correcto.
- El código se compara **antes** de mirar si está validado. Un identificador sin registro detrás
  (la plaza de un correo con cuenta) nunca está validado; si el registro real respondiera «ya
  validado» sin comparar, eso delataría que es real.
- La operación nueva es `registration.verify_code`, que usará la API. El comando de consola
  `registration verify` la usa ya, así que la regla es la misma en la consola y en la API.
- La auditoría registra como verificación correcta volver a presentar el código bueno (antes, como
  fallida).
- El cambio de contraseña no cambia: conserva la regla anterior.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Verificar de nuevo un código validado | `da3913f` |
| T-002 | La consola usa la regla nueva | `b230ea7` |
| T-003 | Resumen de `procesos-pendientes`: código validado | `c3b7f88` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, con Docker. Sin proveedor de correo configurado, el código se lee en
la salida del worker.

Levanta la base de datos y Redis:
```bash
docker compose -f docker/docker-compose.yml up -d db redis
```
Aplica las migraciones:
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
```
Levanta el worker y el planificador:
```bash
docker compose -f docker/docker-compose.yml up -d worker beat
```
Inicia un registro:
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration start --email ana@example.com --name "Ana García" --birthdate 1990-05-10 --country es --language es
```
Verás una línea `public_id: …`; en los pasos siguientes, `<PUBLIC_ID>` es ese valor. Lee el código
en el worker:
```bash
docker compose -f docker/docker-compose.yml logs worker --tail 60
```
Deberías ver un correo con un código de 6 dígitos; en los pasos siguientes, `<CODE>` es ese código.
Verifícalo:
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> <CODE>
```
Deberías ver `Code verified.` Repite exactamente el mismo comando:
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> <CODE>
```
Deberías ver otra vez `Code verified.` (antes de esta entrega, «The code was already verified.»).
Prueba ahora un código incorrecto:
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> 000000
```
Deberías ver `Wrong code.`, y ese intento cuenta para el bloqueo de 5.

Los tests de la entrega:
```bash
docker compose -f docker/docker-compose.yml run --rm backend pytest apps/accounts/tests/test_registration_flow.py apps/accounts/tests/test_registration_service.py apps/audit/tests/test_registration_events.py
```
Deberías ver todos en verde.

## Marco teórico
### Oráculo
Un oráculo es cualquier respuesta que, sin pretenderlo, contesta una pregunta que el sistema quería
mantener en secreto. Aquí la pregunta es «¿este correo tiene cuenta?». Una plaza (el identificador
que se devuelve cuando el correo ya tiene cuenta) imita a un registro real cuyo código nunca se
acierta. Si un registro real validado respondiera «ya validado» a cualquier código, cualquiera con
el enlace vería una respuesta que una plaza no puede dar, y sabría que el registro es real. Por eso
el código se compara primero: con un código incorrecto, el registro validado y la plaza responden
lo mismo.
