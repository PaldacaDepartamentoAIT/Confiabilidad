# Entrega E-01 · Configuración, límite por IP y cómputo de intentos en cuenta inactiva

Rama: `feat/inicio-cierre-sesion-limites` · PR: pendiente · Líneas de código y tests: 287 (límite: 400).

## Qué se hizo
- Se añadieron los cinco ajustes configurables por entorno de `RF-020` (valores configurables) en
  `backend/config/settings.py`, `backend/.env.example` y `backend/apps/accounts/conf.py`, rechazando
  cualquier valor menor que 1 con `ImproperlyConfigured`:
  - `LOGIN_MAX_FAILED_ATTEMPTS` (5 por defecto) y `LOGIN_LOCKOUT_MINUTES` (5 minutos por defecto),
    conectados a `ACCOUNT_RATE_LIMITS["login_failed"]`;
  - `LOGIN_RATE_IP_PER_MINUTE` (30 solicitudes por minuto por defecto);
  - `SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS` (60 segundos por defecto);
  - `SESSION_LIFETIME_DAYS` (14 días por defecto), conectado a `SESSION_COOKIE_AGE`.
- Se implementó `throttling.check_login_ip` (`RF-005`, límite de frecuencia por IP en el inicio de
  sesión) con ventana deslizante de 60 segundos y clave propia en caché (`login-rate:ip:<IP>`),
  independiente de los límites del registro.
- En `AuditAccountAdapter.pre_login` (`RF-002`, rechazo neutro de credenciales inválidas o cuenta
  inactiva, y `RF-004`, bloqueo temporal por intentos fallidos), un intento sobre una cuenta
  inactiva con contraseña correcta consume un intento en el limitador `login_failed` de allauth
  mediante `super().authentication_failed(request, email=user.email)` además de registrar el evento
  `LOGIN` con motivo `inactive_account`, de modo que al sexto intento consecutivo se bloquea con
  `too_many_login_attempts` y genera la fila `LOCKOUT` en `SecurityEvent`, igual que con contraseña
  errónea.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Valores configurables de inicio de sesión y sesiones | `2617e8b` |
| T-002 | Límite por IP del inicio de sesión | `8f103c8` |
| T-003 | Bloqueo por intentos fallidos en cuenta inactiva | `d05b45d` |

## Cómo ejecutarlo y probarlo
En tu máquina virtual o VPS con el entorno y los servicios levantados, actualiza las ramas remotas y
cambia a la rama de la entrega:
```bash
git fetch origin
```
```bash
git checkout feat/inicio-cierre-sesion-limites
```
Ejecuta los tests nuevos y modificados de esta entrega:
```bash
docker compose -f docker/docker-compose.yml exec backend pytest apps/accounts/tests/test_auth_conf.py apps/accounts/tests/test_auth_throttling.py apps/accounts/tests/test_inactive_login.py -v
```
Deberías ver todos los tests de los tres archivos en verde.

Ejecuta la suite completa del backend y los análisis estáticos (tipos, lint y formato):
```bash
docker compose -f docker/docker-compose.yml exec backend pytest -q
```
Deberías ver toda la suite en verde y la cobertura por encima del 80 %.
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

## Marco teórico
### Evitar un oráculo de enumeración en el sexto intento
Si una cuenta inactiva respondiera con el mismo mensaje de error que una contraseña equivocada en los
primeros cinco intentos, pero no sumara al contador de bloqueo cuando la contraseña es la correcta,
quien probara seis veces seguidas notaría que al sexto intento no salta el bloqueo y sabría que
acertó la contraseña de una cuenta deshabilitada. Consumir el intento en `pre_login` dentro del
limitador oficial de allauth mantiene a allauth como única fuente de bloqueo (`RF-006` de
`auditoria-eventos-seguridad`, fuente única de intentos fallidos) e iguala el umbral de bloqueo
entre cuentas activas, inactivas e inexistentes.
