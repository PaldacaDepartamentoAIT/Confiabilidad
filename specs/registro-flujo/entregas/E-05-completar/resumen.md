# Entrega E-05 · Completar el registro con código y contraseña

Rama: `feat/registro-flujo-completar` · PR: pendiente ·
Líneas de código y tests: 383 (límite: 400).

## Qué se hizo
- **Completar con código y contraseña** (RF-012, RF-013, RF-014): `registration.complete_with_code`
  vuelve a comprobar el código en cada petición y crea la cuenta solo si coincide y ya estaba
  validado. En orden:
  - identificador desconocido, proceso caducado o bloqueado: se rechaza;
  - código incorrecto, **o correcto pero nunca validado** (C-03): suma un intento fallido y se
    rechaza igual que un código incorrecto, **sin mirar la contraseña**;
  - contraseña que incumple la política: devuelve cada regla incumplida, **sin sumar intento**, y
    el código sigue valiendo para probar otra contraseña;
  - todo correcto: crea la cuenta con el correo verificado, registra la aceptación de los términos
    y borra el registro pendiente, en una sola operación (RF-020 de `procesos-pendientes`).
  Los datos de la cuenta salen del registro pendiente; del cliente solo llega la contraseña. Una
  plaza (correo con cuenta) nunca crea cuenta: su código nunca coincide. Durante la gracia de 15
  minutos tras caducar el código se puede completar.
- **Ruta de compleción** para los dos clientes:
  - `POST /api/browser/v1/registration/complete` (web, exige el token CSRF);
  - `POST /api/app/v1/registration/complete` (aplicación).
  Cuerpo `{"public_id", "code", "password"}` y, opcional, `language`. Responde `201`
  `{"result": "created"}`; `400` `{"code": "wrong_code" | "locked" | "expired", "message"}`; `400`
  `{"errors": {"password": [{"code", "message"}]}}` con cada regla; `404`; y `429`, porque cuenta
  para el límite por IP.
- **Textos de la política de contraseña** en tres idiomas. La longitud mínima del texto sale de la
  propia política, no está escrita a mano.
- **Casos compartidos de contraseña** (CF-8): un test del servidor recorre la tabla de la spec con
  los validadores de longitud y de «solo números». El del navegador llega en E-11.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-016 | Completar con código y contraseña | `b439739` |
| T-017 | Textos de la política de contraseña | `a60d193` |
| T-018 | Ruta de compleción | `c5de07e` |
| T-019 | Casos compartidos de contraseña en el servidor | `07be0a1` |

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
Publica unos términos de prueba si aún no hay unos vigentes:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from datetime import timedelta; from django.utils import timezone; from apps.consents.models import Terms; [Terms.objects.get_or_create(kind='terms', version='1', locale=locale, defaults={'content': 'Términos de prueba.', 'published_at': timezone.now() - timedelta(days=1)}) for locale in ('es', 'pt-BR', 'en')]"
```
Empieza un registro con un correo que aún no tenga cuenta:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration -H "Content-Type: application/json" -d '{"name": "Ana García", "birthdate": "1990-05-10", "email": "ana.flujo@example.com", "country": "ES", "terms": {"version": "1", "locale": "es", "accepted": true}}'
```
En los pasos siguientes, `<PUBLIC_ID>` es el `public_id` de esa respuesta. Lee el código en el
worker:
```bash
docker compose -f docker/docker-compose.yml logs worker --tail 60
```
En los pasos siguientes, `<CODE>` es el código de 6 dígitos del correo. Intenta completar sin haber
validado el código:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/complete -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>", "code": "<CODE>", "password": "Kq7#mZ2!vR9p"}'
```
Deberías ver `{"code": "wrong_code", …}`: aún no está validado, y el intento cuenta. Valida el
código:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/verify -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>", "code": "<CODE>"}'
```
Deberías ver `{"result": "verified"}`. Completa con una contraseña débil:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/complete -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>", "code": "<CODE>", "password": "12345", "language": "es"}'
```
Deberías ver `{"errors": {"password": [...]}}` con «al menos 12 caracteres» y «solo números».
Completa con una contraseña válida:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/complete -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>", "code": "<CODE>", "password": "Kq7#mZ2!vR9p"}'
```
Deberías ver `{"result": "created"}`. Repite el mismo comando:
```bash
curl -s -i -X POST http://localhost:8000/api/app/v1/registration/complete -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>", "code": "<CODE>", "password": "Kq7#mZ2!vR9p"}'
```
Deberías ver `404`: el registro pendiente ya no existe. La cuenta sí, con el correo verificado:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from allauth.account.models import EmailAddress; print(EmailAddress.objects.filter(email='ana.flujo@example.com').values_list('verified', flat=True).first())"
```
Deberías ver `True`.

Los tests de la entrega:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_registration_flow.py apps/accounts/tests/test_registration_flow_api.py apps/accounts/tests/test_password_shared_cases.py apps/accounts/tests/test_registration_api_messages.py
```
Deberías ver todos en verde.

## Marco teórico
### Por qué un código correcto pero no validado cuenta como incorrecto
La pantalla siempre valida el código antes de pedir la contraseña. Quien llama a completar sin
haberlo validado se ha saltado ese paso a propósito, y completar es la única ruta que además evalúa
la contraseña. Si ahí un código correcto no gastara intentos, alguien podría probar códigos por esa
ruta sin el freno de los 5 intentos de la verificación. Por eso cuenta igual que uno incorrecto.
