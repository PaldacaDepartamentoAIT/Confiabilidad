# Entrega E-02 · Servicio de cambio de contraseña con límite configurable y cierre de otras sesiones

Rama: `feat/perfil-y-cambio-contrasena-api-password` · PR: #155 · Líneas de código y tests: 353 (límite: 400).

## Qué se hizo
- Se ajustó la división de entregas trasladando `T-009` a `E-02b` para mantener esta entrega por debajo del límite de 400 líneas (353 líneas reales).
- En `backend/config/settings.py`, `backend/apps/accounts/conf.py` y `backend/apps/accounts/throttling.py` (`T-005`, `RF-008` y `RF-014`) se añadieron los ajustes configurables `PASSWORD_CHANGE_MAX_FAILED_ATTEMPTS` (`5` por defecto), `PASSWORD_CHANGE_ATTEMPT_WINDOW_MINUTES` (`5` por defecto) y `PASSWORD_CHANGE_LOCKOUT_MINUTES` (`5` por defecto), junto con `check_password_change`, `record_password_change_failure` y `clear_password_change_failures` en caché por cuenta.
- En `backend/apps/accounts/models.py`, `backend/apps/accounts/sessions.py` y `backend/apps/accounts/profile.py` (`T-006`, `RF-006`…`RF-010`) se implementó `profile.change_password`:
  - comprueba primero el bloqueo por intentos fallidos; si falla la contraseña actual, registra el fallo aunque la nueva falte o sea inválida;
  - valida la nueva contraseña con la política del proyecto (`validate_password`), aceptando la contraseña actual si cumple la política;
  - guarda la nueva contraseña con `skip_password_session_revocation` para respetar `RF-010` de `inicio-cierre-sesion` en guardados externos, actualiza la sesión actual (`sessions.refresh_current_session`: rota clave en navegador sincronizando `UserSession`, y actualiza `HASH_SESSION_KEY` en `app` conservando `X-Session-Token`);
  - revoca de inmediato el resto de sesiones (`sessions.revoke_all_other_sessions`), emite auditoría (`password_changed` y `user_logged_out` por cada otra sesión cerrada), encola `password_changed` siempre y `sessions_closed` únicamente cuando `revoked_sessions > 0` en el idioma guardado de la cuenta, y limpia el contador al confirmar la transacción.
- En `backend/apps/accounts/tests/test_profile_service.py` se añadieron pruebas de límites, bloqueos, preservación de sesión actual, cierre de las demás, auditoría, avisos de correo y preservación de `RF-010` en guardados directos del modelo.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-005 | Límite configurable por cuenta ante intentos fallidos de contraseña actual | `70c2bd9` |
| T-006 | Servicio de cambio de contraseña, conservación de sesión actual, cierre de otras sesiones, auditoría y avisos | `a03a8d0` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con Docker, PostgreSQL y Redis levantados, actualiza las ramas remotas y cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/perfil-y-cambio-contrasena-api-password
```
Ejecuta los tests de esta entrega (sin umbral global sobre otros módulos):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_profile_service.py -v --no-cov
```
Deberías ver todos los tests de `test_profile_service.py` en verde.

Ejecuta la suite completa, `mypy .`, `ruff check .` y `black --check .`:
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

Para ejercitar `change_password` desde consola antes de `E-02b` (cambia `<EMAIL>`, `<CURRENT_PASSWORD>` y `<NEW_PASSWORD>` por los de una cuenta de prueba):
```bash
docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.accounts import profile; from apps.accounts.models import User; u = User.objects.get(email='<EMAIL>'); print(profile.change_password(u, current_password='<CURRENT_PASSWORD>', new_password='<NEW_PASSWORD>'))"
```
Deberías ver `PasswordChanged(user=<User: ...>, revoked_sessions=...)`.

## Marco teórico
### Actualización explícita de `HASH_SESSION_KEY` frente a `update_session_auth_hash`
En las vistas headless de este proyecto (`authentication_classes = []`), DRF asigna `AnonymousUser` a `request.user` aunque la sesión de cookie esté autenticada mediante `get_user(django_request)`. El helper estándar de Django `update_session_auth_hash` comprueba `request.user == user` antes de actualizar `_auth_user_hash`, por lo que dejaría la sesión sin actualizar. Por ello, `sessions.refresh_current_session` actualiza explícitamente `HASH_SESSION_KEY` y rota la clave en el navegador (sincronizando `UserSession`), mientras que en sesiones de aplicación (`X-Session-Token`) actualiza `HASH_SESSION_KEY` en el almacén manteniendo la misma clave para no expulsar al cliente de escritorio.
