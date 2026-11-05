# Entrega E-04 · Estado del proceso y opciones del formulario

Rama: `feat/registro-flujo-estado` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#37](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/37) ·
Líneas de código y tests: 279 (límite: 400).

## Qué se hizo
- **Estado del proceso** (RF-006, RF-009, RF-010): `registration.status` devuelve lo que necesita
  la pantalla de verificación: segundos que le quedan al código, segundos hasta poder reenviar,
  reenvíos restantes, si está bloqueado y si ha caducado. Nunca cuenta nada que no sea cero en
  negativo. **No dice si el código está validado**: una plaza (correo con cuenta) nunca lo está, y
  ese dato delataría que el registro es real (D-05).
- **Ruta de estado** para los dos clientes:
  - `POST /api/browser/v1/registration/status` (web, exige el token CSRF);
  - `POST /api/app/v1/registration/status` (aplicación).
  Cuerpo `{"public_id"}`. Responde `200` con
  `{"code_expires_in", "resend_in", "resends_left", "locked", "expired"}` o `404` si el
  identificador no existe. **No cuenta para el límite por IP** (RF-019): solo lee. El identificador
  va en el cuerpo y no en la dirección, para que no quede en los registros del servidor (D-03).
- **Opciones del formulario** (RF-001):
  - `GET /api/browser/v1/registration/options` (web) y `GET /api/app/v1/registration/options`
    (aplicación), con `?language=es|pt-BR|en` o, si falta, la cabecera `Accept-Language`;
  - responde la lista de países (códigos ISO ordenados) y los documentos vigentes de términos y de
    marketing en ese idioma (`{"version", "locale", "content"}`), o `null` si no hay ninguno;
  - la variante web pone la cookie `csrftoken` que exigen los `POST` del flujo (D-09).
- `validators.COUNTRY_CODES` pasa a ser pública; la validación del país no cambia.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-012 | Estado del proceso | `c3ba6dc` |
| T-013 | Ruta de estado | `6bad1f2` |
| T-014 | Lista pública de países | `d034bdc` |
| T-015 | Ruta de opciones del formulario | `46a6686` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, con Docker. Levanta los servicios:
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
Pide las opciones del formulario en portugués:
```bash
curl -s "http://localhost:8000/api/app/v1/registration/options?language=pt-BR"
```
Deberías ver `{"countries": ["AD", "AE", …], "terms": {"version": "1", "locale": "pt-BR", …}, "marketing": null}`.
La variante web entrega además la cookie CSRF:
```bash
curl -s -i http://localhost:8000/api/browser/v1/registration/options
```
Deberías ver una cabecera `Set-Cookie: csrftoken=…`. Empieza un registro:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration -H "Content-Type: application/json" -d '{"name": "Ana García", "birthdate": "1990-05-10", "email": "ana@example.com", "country": "ES", "terms": {"version": "1", "locale": "es", "accepted": true}}'
```
En los pasos siguientes, `<PUBLIC_ID>` es el `public_id` de esa respuesta. Consulta su estado:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/status -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>"}'
```
Deberías ver algo como `{"code_expires_in": 897, "resend_in": 57, "resends_left": 5, "locked": false, "expired": false}`.
Prueba tres códigos incorrectos y vuelve a consultar el estado: verás que no cambia nada salvo los
tiempos, porque el estado no cuenta los intentos fallidos hasta que llegan a 5 y bloquean el código.
Con un identificador inventado:
```bash
curl -s -i -X POST http://localhost:8000/api/app/v1/registration/status -H "Content-Type: application/json" -d '{"public_id": "inventado"}'
```
Deberías ver `404`.

Los tests de la entrega:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_registration_flow.py apps/accounts/tests/test_registration_flow_api.py apps/accounts/tests/test_validators.py
```
Deberías ver todos en verde.
