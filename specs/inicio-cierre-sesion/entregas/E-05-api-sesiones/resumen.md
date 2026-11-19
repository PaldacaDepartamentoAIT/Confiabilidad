# Entrega E-05 · API de aceptación de términos vigentes y guarda del área privada

Rama: `feat/inicio-cierre-sesion-api-sesiones` · PR: pendiente · Líneas de código y tests: 292 (límite: 400).

## Qué se hizo
- Se añadió `TermsAcceptSerializer` en `apps/accounts/api/auth_serializers.py`, reutilizando las reglas y códigos de validación de términos obligatorios de `RegistrationSerializer.validate_terms` (`RF-012`, `RF-019`).
- Se implementó `POST /api/browser/v1/auth/terms/accept` y `POST /api/app/v1/auth/terms/accept` (`BrowserTermsAcceptView` / `AppTermsAcceptView`) en `apps/accounts/api/auth_views.py` y `apps/accounts/api/urls.py` (`T-012`, `RF-012`, `RF-018`).
- Se añadió `_require_auth(..., require_terms=True)` en `apps/accounts/api/auth_views.py` para exigir sesión activa y comprobar en cada petición privada si la cuenta tiene aceptados los términos vigentes (`403 {"code": "terms_required", "terms_status": ..., "message": ...}` cuando faltan o no hay versión vigente; `D-06`, `C-06`, `RF-011`).
- Se dividió `T-013` en `E-05b` (`feat/inicio-cierre-sesion-gestion-sesiones`) para mantener cada PR por debajo de 400 líneas.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-012 | Ruta de aceptación de términos vigentes y guarda del área privada | `599f2da` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con el entorno y los servicios levantados, actualiza las ramas remotas y cambia a la rama de la entrega:

```bash
git fetch origin
```

```bash
git checkout feat/inicio-cierre-sesion-api-sesiones
```
Deberías ver tu copia de trabajo posicionada en `feat/inicio-cierre-sesion-api-sesiones`.

Ejecuta los tests de esta entrega:

```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_auth_terms_gate.py --no-cov -v
```
Deberías ver todos los tests de aceptación de términos y guarda privada en verde.

Ejecuta los análisis estáticos y la suite completa del backend:

```bash
docker compose -f docker/docker-compose.yml exec backend mypy .
```
Deberías ver `Success: no issues found`.

```bash
docker compose -f docker/docker-compose.yml exec backend ruff check .
```
Deberías ver la salida limpia sin advertencias.

```bash
docker compose -f docker/docker-compose.yml exec backend black --check .
```
Deberías ver todos los archivos con el formato correcto.

```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver toda la suite en verde con cobertura ≥ 80 %.

### Prueba en vivo con `curl` (cliente `app`)
Si no tienes una versión de términos publicada o un usuario de prueba en desarrollo, crea ambos en el contenedor del backend:

```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py shell -c "from datetime import timedelta; from django.contrib.auth import get_user_model; from django.utils import timezone; from apps.consents.models import Terms; User = get_user_model(); user, created = User.objects.get_or_create(email='demo@example.com', defaults={'is_active': True}); user.is_active = True; user.set_password('DemoPass123!'); user.save(); Terms.objects.get_or_create(kind='terms', version='1.0', locale='es', defaults={'content': 'Terminos vigentes.', 'published_at': timezone.now() - timedelta(days=1), 'requires_reacceptance': True})"
```
Deberías ver el comando terminar sin errores.

Inicia sesión con el cliente `app` (guarda el campo `session_token` de la respuesta):

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/login -H "Content-Type: application/json" -d '{"email":"demo@example.com","password":"DemoPass123!","language":"es"}'
```
Deberías ver HTTP 200 con `"terms_status": "not_accepted"`, el documento en `"terms"` y `"session_token"`.

Usa el valor de `session_token` del paso anterior como `<SESSION_TOKEN>` para aceptar los términos vigentes:

```bash
curl -s -X POST http://localhost:8000/api/app/v1/auth/terms/accept -H "Content-Type: application/json" -H "X-Session-Token: <SESSION_TOKEN>" -d '{"version":"1.0","locale":"es","accepted":true,"language":"es"}'
```
Deberías ver `{"terms_status":"accepted"}`.

Consulta la sesión con el mismo `<SESSION_TOKEN>` para confirmar el cambio:

```bash
curl -s http://localhost:8000/api/app/v1/auth/session -H "X-Session-Token: <SESSION_TOKEN>"
```
Deberías ver `"terms_status":"accepted"` y `"terms":null`.

## Marco teórico
- **Por qué la aceptación de términos se valida igual que en registro y en caliente por petición (`C-06`)**: aceptar una versión anterior o de un documento equivocado (como marketing) o hacerlo mientras otra persona administradora publica una versión obligatoria nueva rompería el consentimiento informado. Por eso `TermsAcceptSerializer` reutiliza `validate_terms` de `RegistrationSerializer`, y `_require_auth(..., require_terms=True)` vuelve a consultar `consent_status(user).terms` en cada petición privada sin cachearlo dentro de la sesión.
