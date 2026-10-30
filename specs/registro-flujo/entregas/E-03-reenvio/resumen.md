# Entrega E-03 · Reenviar el código con espera y tope

Rama: `feat/registro-flujo-reenvio` · PR: pendiente ·
Líneas de código y tests: 400 (límite: 400).

## Qué se hizo
- **Contadores de reenvío** en todo proceso con código (registro pendiente, plaza y solicitud de
  cambio de contraseña): `resend_count` (reenvíos del proceso) y `last_sent_at` (último envío),
  con su migración `0013_codeprocess_resend`. Los procesos que ya existían quedan con 0 y sin
  último envío, que se trata como «se puede reenviar».
- **Se ponen al día igual en un registro real y en una plaza** (RF-017): la plaza nace con el envío
  de ahora; al resolverse, un registro nuevo, uno repetido y una plaza con cuenta quedan con 0
  reenvíos y el envío del momento de la resolución.
- **Reenvío con espera y tope** (RF-010): `registration.resend_code` reenvía solo pasados 60
  segundos desde el último envío y como mucho 5 veces por proceso. Antes de tiempo, tras el quinto
  reenvío o con el código ya validado, responde lo mismo, «reenvío no disponible», sin cambiar nada.
  El reenvío de la consola (`registration resend`) no cambia: no tiene espera ni tope.
- **Ruta de reenvío** para los dos clientes:
  - `POST /api/browser/v1/registration/resend` (web, exige el token CSRF);
  - `POST /api/app/v1/registration/resend` (aplicación).
  Cuerpo `{"public_id"}` y, opcional, `language`. Responde `202` `{"result": "resent"}`, `400`
  `{"code": "resend_unavailable" | "expired", "message"}`, `404` con un identificador que no
  existe y `429` al superar el límite por IP, que comparte con la verificación.
- Las vistas del flujo comparten ahora una vista base (idioma, límite por IP, lectura del cuerpo y
  «no encontrado»), que usarán también la consulta del estado y la compleción.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-008 | Contadores de reenvío en el modelo | `6d64b9f` |
| T-009 | Contadores al emitir el código | `0d2d076` |
| T-010 | Reenvío con espera y tope | `64c3c90` |
| T-011 | Ruta de reenvío | `d8e8302` |

Además, `215b14c` quita un `type: ignore` sobrante que dejó T-008 en sus tests.

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, con Docker. Sin proveedor de correo configurado, los códigos se leen
en la salida del worker.

Levanta los servicios:
```bash
docker compose -f docker/docker-compose.yml up -d db redis backend worker beat
```
Aplica las migraciones:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py migrate
```
Deberías ver `accounts.0013_codeprocess_resend... OK`. Publica unos términos de prueba si aún no
hay unos vigentes:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from datetime import timedelta; from django.utils import timezone; from apps.consents.models import Terms; [Terms.objects.get_or_create(kind='terms', version='1', locale=locale, defaults={'content': 'Términos de prueba.', 'published_at': timezone.now() - timedelta(days=1)}) for locale in ('es', 'pt-BR', 'en')]"
```
Empieza un registro:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration -H "Content-Type: application/json" -d '{"name": "Ana García", "birthdate": "1990-05-10", "email": "ana@example.com", "country": "ES", "terms": {"version": "1", "locale": "es", "accepted": true}}'
```
En los pasos siguientes, `<PUBLIC_ID>` es el `public_id` de esa respuesta. Pide un reenvío enseguida:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/resend -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>"}'
```
Deberías ver `{"code": "resend_unavailable", …}`: no han pasado 60 segundos. Espera un minuto y
repite el mismo comando:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/resend -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>"}'
```
Deberías ver `{"result": "resent"}`, y en el worker un correo nuevo con otro código:
```bash
docker compose -f docker/docker-compose.yml logs worker --tail 60
```
Para ver el tope sin esperar cinco minutos, marca el proceso como si ya llevara 5 reenvíos y su
último envío fuera de hace dos minutos:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from datetime import timedelta; from django.utils import timezone; from apps.accounts.models import PendingRegistration; PendingRegistration.objects.update(resend_count=5, last_sent_at=timezone.now() - timedelta(minutes=2))"
```
Repite el reenvío:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/resend -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>"}'
```
Deberías ver otra vez `{"code": "resend_unavailable", …}`.

Los tests de la entrega:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_registration_flow.py apps/accounts/tests/test_registration_flow_api.py apps/accounts/tests/test_pending_registration_model.py
```
Deberías ver todos en verde.

## Marco teórico
### Por qué los contadores viven en el proceso y no en la caché
La espera y el tope tienen que comportarse igual en un registro real que en una plaza (el
identificador de un correo con cuenta), o la diferencia delataría la cuenta. Guardados en la fila
del proceso, nacen, se reinician y desaparecen con él, exactamente en los mismos momentos para los
dos. En la caché, un registro repetido o un vaciado de Redis los afectaría de forma distinta.
