# Plan: auditoria-eventos-seguridad
Estado: borrador

## Módulos
### M-01 Modelo SecurityEvent
Responsabilidad: tabla de eventos, tipos (11 valores de RF-002), campos de RF-001, índice en
`created_at`, y guardas de solo inserción (save, delete y QuerySet).
RF: RF-001, RF-002, RF-011, RF-012, RF-016

### M-02 Registrador
Responsabilidad: función `record_event(event_type, *, success, request, email, session_key, metadata)`
que construye la fila: IP desde `REMOTE_ADDR` (ya corregida por M-07), user agent, huella del correo,
huella de la clave de sesión y metadatos. Es el único punto que escribe filas.
RF: RF-001, RF-003, RF-004, RF-011

### M-03 Receptores de señales
Responsabilidad: conecta las señales de Django y de allauth (`user_logged_in`, `user_logged_out`,
`user_signed_up`, `password_changed`, `password_reset`, `password_set`) y las señales propias de
accounts (M-08) con M-02.
RF: RF-003, RF-007, RF-008, RF-009, RF-010 (parcial, ver «RF sin cobertura»)

### M-04 Adaptador de allauth
Responsabilidad: subclase de `DefaultAccountAdapter` que sobrescribe `authentication_failed` para
registrar el fallo y el bloqueo por límite. No cuenta intentos ni bloquea: solo registra lo que
allauth ya decidió.
RF: RF-004, RF-005, RF-006

### M-05 Admin de solo lectura
Responsabilidad: `SecurityEventAdmin` sin añadir, cambiar ni borrar; permiso `view_securityevent`
para ver; filtros por fecha, tipo, IP y huella del correo.
RF: RF-012, RF-013

### M-06 Comando de purga
Responsabilidad: `manage.py purge_security_events --dry-run` borra solo eventos con más de un año.
Es la única vía de borrado (RF-012, RF-014).
RF: RF-012, RF-014

### M-07 IP real del cliente (cambio en `apps/core`)
Responsabilidad: `RealClientIPMiddleware` solo lee `X-Forwarded-For` cuando `REMOTE_ADDR` pertenece a
la lista de proxies de confianza (ajuste nuevo `TRUSTED_PROXY_IPS`). En cualquier otro caso deja la
IP de la conexión directa.
RF: RF-015
*Cambio aprobado: toca `apps/core`, fuera de la feature, con permiso explícito del usuario.*

### M-08 Señales propias de accounts
Responsabilidad: define señales en `apps/accounts/signals.py` y las emiten los servicios de
registro y de cambio de contraseña (`registration.py`, `password_reset.py`). Define también las
señales de edición de perfil y de deshabilitación de cuenta, que hoy no tienen emisor: el contrato
queda listo para el flujo que las emita. Así accounts no importa nada de audit.
RF: RF-007, RF-008, RF-010 (parcial)

### M-09 Huellas centralizadas (dependencia externa)
Responsabilidad: `apps/core/fingerprints.py` del trabajo `huellas-hmac-unificadas`, que aún no está
en `main`. Esta feature añade dos funciones: `audit_email_fingerprint` y `audit_session_fingerprint`.
Dependencia: S-02. Ninguna tarea de implementación empieza antes de que M-09 esté mergeada.

## Modelo de datos
Tabla `audit_securityevent` (app `audit`, nueva):
- `id`: BigAutoField (Django).
- `event_type`: CharField con choices de 11 valores, indexado.
- `created_at`: DateTimeField(UTC, `default=timezone.now`, `db_index=True`).
- `session_key`: CharField(64), null/blank. HMAC de la clave de sesión (D-04).
- `ip`: GenericIPAddressField, null.
- `user_agent`: TextField, blank.
- `user_email_hash`: CharField(64), blank. HMAC del correo en minúsculas, sin espacios (D-04).
- `success`: BooleanField.
- `metadata`: JSONField, default dict. Lista abierta de datos no sensibles (decidido en clarificación).

Sin clave foránea a `User` (decidido en clarificación).

## Decisiones
### D-01 Ubicación: app nueva `audit`
Elegida: `apps/audit/` con modelo, registrador, receptores, adaptador, admin y comando.
Descartada: meterlo en `apps/accounts/`. Motivo: accounts ya concentra registro, contraseñas y
usuario; la auditoría es transversal y tiene su propia tabla y comando.

### D-02 Emisión desde los flujos propios: señales de accounts
Elegida: M-08 define señales y los servicios las emiten; M-03 las recibe.
Descartada: que los servicios llamen directamente a `record_event`. Motivo: accounts quedaría
acoplado a audit y los tests de accounts dependerían de auditoría. Con señales, accounts no conoce
audit.

### D-03 Fallos de inicio de sesión: adaptador, no señal
Elegida: `AuditAccountAdapter.authentication_failed` (M-04), activado con `ACCOUNT_ADAPTER`.
Descartada: un middleware que lea respuestas 400, o una señal inexistente. Motivo: allauth 65.x no
emite señal para fallos de login (`allauth/account/adapter.py`, línea 824); el adaptador es su
punto de extensión oficial y no añade lógica de bloqueo.
*Suposición:* el flujo de headless llama a ese mismo método. Se verifica en la primera tarea de M-04.

### D-04 Huellas de clave de sesión y correo
Elegida: M-09 calcula ambas con HMAC-SHA256 y la clave de auditoría (D-05). El correo se normaliza
igual que en RF-011.
Descartada: guardar `session_key` en claro (contradice RF-011) y reutilizar `consent_email_fingerprint`
sin clave propia. Motivo: la huella de consentimientos es permanente y ligada a otra finalidad.

### D-05 Clave de auditoría: `AUDIT_HASH_SECRET` nueva
Elegida: un ajuste nuevo `AUDIT_HASH_SECRET` en el almacén de secretos, distinto de los demás.
Descartada: reutilizar `CONSENT_EMAIL_HASH_SECRET`. Motivo: con la misma clave, filtrar una tabla
compromete la otra y ambas se pueden correlacionar. Coste: una entrada en `HUMAN_TODO.md` para generar
la clave y cifrarla con SOPS. Sin esa clave configurada, la aplicación debe fallar al arrancar (no usar
`SECRET_KEY` como valor por defecto).

### D-06 Permiso de consulta: permiso específico
Elegida: `Meta.permissions = [("view_security_event", ...)]` y `has_view_permission` lo comprueba.
Descartada: `is_staff`, que ya decidiste no usar (H-07).

### D-07 Solo inserción: guardas en tres puntos
Elegida: `save()` lanza error si la fila ya existe; `delete()` y el `QuerySet` de update y delete
lanzan error salvo cuando los llama el método `purge_older_than` del comando de purga (M-06). El admin
no ofrece cambiar ni borrar.
Descartada: un rol de base de datos sin UPDATE ni DELETE, que está fuera de alcance (spec).
Motivo: las guardas viven en el código y se prueban con tests.

### D-08 Confianza en el proxy (aprobada)
Elegida: M-07 con lista `TRUSTED_PROXY_IPS` tomada del entorno.
Descartada: seguir leyendo `X-Forwarded-For` sin comprobar la conexión. Motivo: hoy cualquier cliente
puede falsificar la IP en conexiones directas.

### D-09 Purga manual con comando
Elegida: `manage.py purge_security_events` con `--dry-run`, que la persona operadora ejecuta.
Descartada: tarea de Celery beat. Motivo: S-03 dice que no es automática; añadirla exigiría
infraestructura nueva.

### D-10 Tipos de evento: un valor por tipo de RF-002
Elegida: `TextChoices` con 11 valores. El rechazo de código es `CODE_VERIFIED` con `success=False`
(H-06).
Descartada: un tipo propio de rechazo (H-06 lo descartó).

## Estrategia de tests
Se sigue TDD (P-04). Cobertura ≥80% en código nuevo (P-05).
- **Unitario (`apps/audit/tests/`)**: guardas de solo inserción (RF-012); normalización y huellas con
  vectores fijos (RF-011); choices de tipos (RF-002); índice en `created_at` (RF-016).
- **Integración (`apps/audit/tests/`)**: login exitoso y fallido con cliente de allauth; comprobar
  que se generan dos filas con la IP real (criterio de finalización); bloqueo por límite genera dos
  filas (RF-005); señales de accounts emiten las filas esperadas (RF-007, RF-008).
- **Integración de IP (`apps/core/tests/`)**: `X-Forwarded-For` falso desde conexión directa no cambia
  la IP (RF-015).
- **Admin**: solo lectura, sin borrar ni añadir, y acceso denegado sin el permiso (RF-013).
- **Comando**: `--dry-run` no borra; la purga elimina solo eventos de más de un año (RF-014).
- **CLI (P-03)**: `pytest backend/apps/audit`; `python manage.py purge_security_events --dry-run`;
  una petición de login por HTTP con `curl` contra el servidor de desarrollo.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-02 | Unitario, integración |
| RF-002 | M-01 | Unitario |
| RF-003 | M-02, M-03 | Integración |
| RF-004 | M-02, M-04 | Integración |
| RF-005 | M-04 | Integración |
| RF-006 | M-04 | Integración (contador de allauth no cambia) |
| RF-007 | M-03, M-08 | Integración |
| RF-008 | M-03, M-08 | Integración |
| RF-009 | M-03 | Integración |
| RF-010 | M-03, M-08 | Integración (parcial, ver abajo) |
| RF-011 | M-01, M-02, M-09 | Unitario |
| RF-012 | M-01, M-05, M-06 | Unitario, admin |
| RF-013 | M-05 | Admin |
| RF-014 | M-06 | Comando |
| RF-015 | M-07 | Integración en `apps/core` |
| RF-016 | M-01 | Unitario |

## RF sin cobertura
- **RF-010 (residual, aceptado por decisión del usuario):** el contrato de señales y los receptores
  cubren la edición de perfil y la deshabilitación de cuenta; el cambio y el restablecimiento de
  contraseña tienen emisor completo. **Nada emite hoy** la edición de perfil ni la deshabilitación,
  porque no existen esos flujos en el código. Quedan pendientes hasta que su feature los cree.

La regla de `sdd-plan` impide aprobar con RF sin cobertura. Este residual se acepta solo si lo confirmas
de forma explícita.

## Historial
- 2026-10-13 — Borrador inicial del plan — RF: RF-001 a RF-016 — Estado: borrador
