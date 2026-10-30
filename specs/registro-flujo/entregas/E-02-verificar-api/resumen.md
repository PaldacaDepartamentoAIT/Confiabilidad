# Entrega E-02 · Verificar el código por la API, con límite por IP

Rama: `feat/registro-flujo-verificar-api` · PR: pendiente ·
Líneas de código y tests: 402 (límite: 400; excepción aprobada por el usuario, hasta 500).

## Qué se hizo
- **Ruta de verificación** para los dos clientes, con el mismo reparto que el formulario de
  `registro-api`:
  - `POST /api/browser/v1/registration/verify` (web, exige el token CSRF);
  - `POST /api/app/v1/registration/verify` (aplicación, sin CSRF).
  Cuerpo JSON `{"public_id", "code"}` y, opcional, `language` (`es`, `pt-BR` o `en`; si falta, la
  cabecera `Accept-Language`).
- **Respuestas**:
  - `200` `{"result": "verified"}` con el código correcto, también si ya estaba validado (E-01);
  - `400` `{"code", "message"}` con `wrong_code`, `locked`, `code_expired` o `expired`, con el
    texto en el idioma de la petición;
  - `404` `{"code": "not_found", "message"}` con un identificador que no existe, tenga la forma que
    tenga (vacío, de 500 caracteres, con un carácter nulo…), sin consultar la base de datos cuando
    no puede existir;
  - `400` `{"errors": …}` si falta un campo o no es texto, y con un cuerpo ilegible; nunca `500`;
  - `429` con `Retry-After` al superar el límite por IP.
- **Límite por IP del flujo** (RF-019): 60 peticiones por hora entre verificar, reenviar y completar
  (hoy solo existe verificar), aparte del límite del formulario. Cuenta toda petición, válida o no,
  antes de evaluarla.
- **Valores configurables** (RF-023) en `backend/.env.example`: espera entre reenvíos (60 s),
  reenvíos por proceso (5), límite por IP del flujo (60/h) y plazo de borrado (24 h). Los tres
  últimos se usarán en E-03 y E-07.
- **Textos** de los rechazos del flujo en español, portugués de Brasil e inglés.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-004 | Valores configurables del flujo | `5258f8f` |
| T-005 | Límite por IP del flujo | `1f33747` |
| T-006 | Textos del flujo en tres idiomas | `758534a` |
| T-007 | Ruta de verificación | `6a03ba9` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, con Docker. Sin proveedor de correo configurado, el código se lee en
la salida del worker.

Levanta los servicios y aplica las migraciones:
```bash
docker compose -f docker/docker-compose.yml up -d db redis backend worker beat
```
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py migrate
```
Publica unos términos de prueba (versión `1`, en los tres idiomas, desde ayer) si aún no hay unos
vigentes:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from datetime import timedelta; from django.utils import timezone; from apps.consents.models import Terms; [Terms.objects.get_or_create(kind='terms', version='1', locale=locale, defaults={'content': 'Términos de prueba.', 'published_at': timezone.now() - timedelta(days=1)}) for locale in ('es', 'pt-BR', 'en')]"
```
Empieza un registro por la API del formulario:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration -H "Content-Type: application/json" -d '{"name": "Ana García", "birthdate": "1990-05-10", "email": "ana@example.com", "country": "ES", "terms": {"version": "1", "locale": "es", "accepted": true}}'
```
Deberías ver `{"public_id": "…", "message": "…"}`; en los pasos siguientes, `<PUBLIC_ID>` es ese
valor. Lee el código en el worker:
```bash
docker compose -f docker/docker-compose.yml logs worker --tail 60
```
En los pasos siguientes, `<CODE>` es el código de 6 dígitos del correo. Prueba un código
incorrecto:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/verify -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>", "code": "000000", "language": "en"}'
```
Deberías ver `{"code": "wrong_code", "message": "The code is not correct. Check it and try again."}`.
Ahora el correcto:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/verify -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>", "code": "<CODE>"}'
```
Deberías ver `{"result": "verified"}`. Con un identificador inventado:
```bash
curl -s -i -X POST http://localhost:8000/api/app/v1/registration/verify -H "Content-Type: application/json" -d '{"public_id": "inventado", "code": "123456"}'
```
Deberías ver `HTTP/1.1 404` y `{"code": "not_found", …}`. Para ver el límite por IP, repite la
petición anterior 61 veces seguidas:
```bash
for i in $(seq 61); do curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/app/v1/registration/verify -H "Content-Type: application/json" -d '{"public_id": "inventado", "code": "123456"}'; done | sort | uniq -c
```
Deberías ver unas 60 respuestas `404` (menos si ya hiciste peticiones en la última hora) y el resto
`429`.

Los tests de la entrega:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_registration_flow_api.py apps/accounts/tests/test_registration_throttling.py apps/accounts/tests/test_registration_conf.py apps/accounts/tests/test_registration_api_messages.py
```
Deberías ver todos en verde.

## Marco teórico
### Por qué un identificador imposible no llega a la base de datos
Postgres no admite el carácter nulo ni un sustituto UTF-16 suelto en un texto: si la consulta los
lleva, la base de datos da un error y la API respondería `500`. Como ningún identificador real puede
contenerlos ni medir más de 64 caracteres, la vista responde «no encontrado» sin consultar. El
resultado visible es el mismo que con cualquier otro identificador que no existe.
