# Entrega E-06 · Consentimiento de marketing en el registro

Rama: `feat/registro-flujo-marketing` · PR: pendiente ·
Líneas de código y tests: 305 (límite: 400).

## Qué se hizo
Implementa los cambios de marketing aprobados en `procesos-pendientes` y `registro-api` el
2026-10-30, que pidió esta feature (RF-018, S-06).
- **Registro pendiente**: guarda el documento de marketing aceptado (`marketing_version` y
  `marketing_locale`, migración `0014_pendingregistration_marketing`), vacío si no se marcó.
- **Al empezar el registro**: un documento de marketing vigente se guarda en la plaza; uno que no
  existe, no es de la versión vigente o está en otro idioma se descarta sin error. Un registro nuevo
  lo copia; uno repetido conserva la elección del primero, **también si no marcó el marketing**. Con
  un correo que ya tiene cuenta no se guarda nada.
- **Al completar**: la concesión se registra en la misma operación que crea la cuenta, con la fecha
  de compleción. Si el documento ya no es vigente, se borró o no es de marketing, la cuenta se crea
  sin concesión y **sin rastro** (riesgo aceptado, C-01 de `procesos-pendientes`).
- **API del formulario**: campo opcional `marketing` `{"version", "locale"}`. El idioma admite sus
  variantes (`pt-br`, `pt_BR`). Lo mal formado (no es un objeto, tipos erróneos, demasiado largo,
  caracteres nulos o sustitutos, anidado) se trata como ausente: la respuesta es la misma `202` que
  sin marketing, nunca un error de campo ni un `500` (RF-015 de `registro-api`).
- **Resúmenes** de `procesos-pendientes` y `registro-api` actualizados, con un paso de prueba con
  `curl`.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-020 | Marketing en el modelo | `41c51bd` |
| T-021 | Marketing al empezar y al repetir | `b6d4d88` |
| T-022 | Concesión de marketing al completar | `a3c8691` |
| T-023 | Marketing en la API del formulario | `d8ffb02` |
| T-024 | Resúmenes de `procesos-pendientes` y `registro-api`: marketing | `9c5d6d7`, `4220870` |

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
Deberías ver `accounts.0014_pendingregistration_marketing... OK`. Publica unos términos y un
documento de marketing de prueba:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from datetime import timedelta; from django.utils import timezone; from apps.consents.models import Terms; [Terms.objects.get_or_create(kind=kind, version=version, locale=locale, defaults={'content': 'Texto de prueba.', 'published_at': timezone.now() - timedelta(days=1)}) for kind, version in (('terms', '1'), ('marketing', 'm1')) for locale in ('es', 'pt-BR', 'en')]"
```
Empieza un registro con el marketing marcado:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration -H "Content-Type: application/json" -d '{"name": "Clara Pérez", "birthdate": "1991-07-08", "email": "clara@example.com", "country": "ES", "terms": {"version": "1", "locale": "es", "accepted": true}, "marketing": {"version": "m1", "locale": "es"}}'
```
En los pasos siguientes, `<PUBLIC_ID>` es el `public_id` de esa respuesta. Lee el código en el
worker:
```bash
docker compose -f docker/docker-compose.yml logs worker --tail 60
```
En los pasos siguientes, `<CODE>` es el código de 6 dígitos del correo. Valida el código:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/verify -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>", "code": "<CODE>"}'
```
Completa el registro:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/complete -H "Content-Type: application/json" -d '{"public_id": "<PUBLIC_ID>", "code": "<CODE>", "password": "Kq7#mZ2!vR9p"}'
```
Deberías ver `{"result": "created"}`. Comprueba el consentimiento:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from apps.consents.models import MarketingConsent; print(MarketingConsent.objects.filter(user__email='clara@example.com', granted=True).values_list('terms__version', flat=True).first())"
```
Deberías ver `m1`. Con un documento inexistente o un campo mal formado, por ejemplo
`"marketing": "sí"`, la respuesta del formulario es la misma y la cuenta queda sin consentimiento.

Los tests de la entrega:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_registration_service.py apps/accounts/tests/test_registration_api.py apps/accounts/tests/test_pending_registration_model.py
```
Deberías ver todos en verde.

## Marco teórico
### Por qué el marketing se ignora sin error y los términos no
Los términos son obligatorios: sin unos válidos no hay registro, así que un fallo tiene que verse.
El marketing es opcional y no debe impedir registrarse, así que un documento que ya no vale o un
campo roto se descartan en silencio. El precio es que un fallo del cliente en el marketing no se ve
en la API: la garantía de que solo se concede cuando la persona marca la casilla queda en los tests
de la pantalla (E-12).
