# Plan: auditoria-eventos-seguridad
Estado: aprobado

## Módulos
### M-01 Modelo SecurityEvent
Responsabilidad: tabla de eventos, tipos (11 valores de RF-002), campos de RF-001, índice en
`created_at`, y guardas de solo inserción (`save`, `save_base`, `delete`, `update` y `delete` del QuerySet, `bulk_create` con `update_conflicts` y el gestor base).
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
registrar el fallo por credenciales incorrectas, `pre_authenticate` para el bloqueo por límite y
`pre_login` para la cuenta inactiva con credenciales válidas (D-13). No cuenta intentos ni bloquea:
solo registra lo que allauth ya decidió.
RF: RF-004, RF-005, RF-006

### M-05 Admin de solo lectura
Responsabilidad: `SecurityEventAdmin` sin añadir, cambiar ni borrar. La vista se concede solo con el
permiso `view_securityevent` (`has_view_permission` lo comprueba explícitamente). Filtros laterales por
tipo, resultado y rango de fechas (filtro personalizado, D-11); búsqueda por dirección IP y búsqueda
exacta por huella del correo (D-12).
RF: RF-012, RF-013

### M-06 Comando de purga
Responsabilidad: `manage.py purge_security_events --dry-run` llama a `purge_expired()` (M-01), que borra
solo eventos con más de un año y no recibe fecha de referencia (T-035, T-036). Es la única vía de borrado
(RF-012, RF-014).
RF: RF-012, RF-014

### M-07 IP real del cliente (cambio en `apps/core`)
Responsabilidad: `RealClientIPMiddleware` solo lee `X-Forwarded-For` cuando `REMOTE_ADDR` coincide
exactamente con una IP de la lista de proxies de confianza (ajuste `TRUSTED_PROXY_IPS`, leído del
entorno de despliegue). Con la lista vacía o sin configurar, no confía en ningún proxy y registra la IP
de la conexión directa. La aplicación arranca en ese caso.
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
El 429 de la limitación por IP de la vista de login no se registra (RF-004 aclarado): no evalúa
credenciales, y registrarlo permitiría inflar la tabla con dos filas por petición.

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
`SECRET_KEY` como valor por defecto). En desarrollo (`DJANGO_DEBUG` activo), si `AUDIT_HASH_SECRET` falta
o está vacía, se usa el valor `dev-audit-secret-change-me`, el mismo de `.env.example`. Con `DEBUG`
desactivado, `audit.E001` sigue impidiendo arrancar (T-043, P-02).

### D-06 Permiso de consulta: permiso específico por defecto
Elegida: el permiso por defecto `view_securityevent` que Django crea para `SecurityEvent`, sin
`Meta.permissions` ni migración; `has_view_permission` lo comprueba explícitamente (decisión del
usuario al resolver T-017, y corrección de T-023 tras la validación).
Descartada: un permiso propio `view_security_event` (dos permisos de vista distintos), y `is_staff`,
que ya decidiste no usar (H-07). Motivo de la corrección: el texto anterior mezclaba ambos.

### D-07 Solo inserción: guardas en tres puntos
Elegida: `save()` lanza error si la fila ya existe; `delete()` y el `QuerySet` de update y delete
lanzan error salvo cuando los llama la función interna `purge_expired()` de `models.py`, que toma el corte
de un año con el reloj del servidor y no recibe fecha (T-035, T-036). `save_base()` y `QuerySet.bulk_create`
con `update_conflicts` también lanzan (T-032, T-034), y `base_manager_name = "objects"` hace que el gestor
base aplique las mismas guardas (T-033). El admin no ofrece cambiar ni borrar. Las vías que RF-012 deja
fuera (SQL directo, APIs internas del ORM como `_raw_delete`, métodos base llamados sin pasar por el
modelo, comandos integrados de Django como `flush` y uso deliberado del permiso de purga) no tienen
guarda: son riesgo residual aceptado.
`_purge_allowed` solo se usa en `models.py`, y `purge_expired()` de auditoría solo la importa el comando
de purga; un test lo comprueba con análisis estático del backend (T-040).
Descartada: un rol de base de datos sin UPDATE ni DELETE, que está fuera de alcance (spec).
Motivo: las guardas viven en el código y se prueban con tests.

### D-08 Confianza en el proxy (aprobada, ampliada tras el cambio de RF-015)
Elegida: M-07 con lista `TRUSTED_PROXY_IPS` tomada del entorno, con entradas que son IP exactas y
valor por defecto vacío (no confía en ningún proxy, y la aplicación arranca).
Descartada: seguir leyendo `X-Forwarded-For` sin comprobar la conexión, y entradas en formato CIDR
(H-09 eligió IP exactas). Motivo: hoy cualquier cliente puede falsificar la IP en conexiones directas.

### D-09 Purga manual con comando
Elegida: `manage.py purge_security_events` con `--dry-run`, que la persona operadora ejecuta.
Descartada: tarea de Celery beat. Motivo: S-03 dice que no es automática; añadirla exigiría
infraestructura nueva.

### D-11 Filtro de rango de fechas en el admin
Elegida: un filtro lateral personalizado (`SimpleListFilter` con plantilla propia) con dos campos
`desde` y `hasta` en formato `AAAA-MM-DD`, que filtra por `created_at__date` (UTC). Requiere una
plantilla nueva, `apps/audit/templates/admin/audit/filter_date_range.html`.
Descartada: el filtro de fecha de Django (solo ofrece periodos predefinidos, como hoy o los últimos
7 días, no un rango libre) y `date_hierarchy` (navega por año, mes y día, sin rango libre). Motivo: el
RF-013 aprobado pide un rango de fechas.

### D-12 Búsqueda exacta por huella del correo
Elegida: en `search_fields`, la huella del correo con prefijo `=` (`=user_email_hash`), que exige
coincidencia exacta, y la IP sin prefijo (coincidencia parcial).
Descartada: la coincidencia parcial que usa hoy `search_fields` para la huella. Motivo: H-11 eligió
coincidencia exacta, y una búsqueda parcial sobre una huella hexadecimal no aporta nada.

### D-13 Detección de cuenta inactiva con credenciales válidas
Elegida: sobrescribir `pre_login` en `AuditAccountAdapter`. Si `user.is_active` es falso, registrar un
fallo de inicio de sesión con motivo `inactive_account` y después llamar a `super().pre_login`, que es
quien responde con la página de cuenta inactiva. `pre_login` se llama en el flujo de login compartido
por el navegador y el headless (`allauth/account/internal/flows/login.py`, línea 94).
Descartada: sobrescribir `authenticate` o `authentication_failed`. Motivo: la validación comprobó que
con credenciales válidas la cuenta inactiva no llega a `authentication_failed` (no hay fila); en
allauth 65.x la decisión la toma `pre_login`. Descartada también una señal, que allauth no emite para
este caso.
*Suposición:* en el flujo de registro `pre_login` no ve cuentas inactivas, porque con la verificación
de correo desactivada las cuentas nuevas se crean activas. Se verifica en la tarea.

### D-14 Motivos de metadatos: lista cerrada de tres códigos
Elegida: el campo `metadata["reason"]` toma solo estos valores, que corresponden a los motivos de la
spec: `invalid_credentials` (credenciales incorrectas), `too_many_login_attempts` (límite de intentos
alcanzado) e `inactive_account` (cuenta inactiva). Los dos primeros ya existen en el código.
Descartada: el texto que devuelva allauth en cada caso, que no es verificable (decisión H-15).
Motivo: la spec pide una lista fija, y los códigos evitan depender de textos traducibles.

### D-15 Cambio o restablecimiento rechazado por contraseña no válida: sin evento de fallo
Elegida: el receptor de cambio y de restablecimiento de contraseña solo registra el evento cuando el
cambio o el restablecimiento se completa. Ningún rechazo, por ningún motivo, deja fila (RF-010,
aclarado).
Descartada: registrar un fallo con un motivo nuevo (por ejemplo `invalid_password`). Motivo: decisión del
usuario al resolver la ambigüedad de RF-010; un motivo nuevo obligaría a ampliar D-14, que fija tres códigos.
Verificación: T-037.

### D-16 Código rechazado: qué genera evento de validación
Elegida: `CODE_VERIFIED` con `success=False` cuando el código es incorrecto (`WRONG_CODE`), ha caducado
(`CODE_EXPIRED`, o el proceso con `EXPIRED`), se alcanzó el límite (`LOCKED`) o ya estaba validado
(`ALREADY_VERIFIED`). Sin evento cuando el proceso no existe (`NOT_FOUND`) o el restablecimiento se rechaza
por la cuenta (`AccountRefusal`). Es lo que ya hacen `registration.verify` y `password_reset.verify`.
Descartada: registrar también `NOT_FOUND` y `AccountRefusal`. Motivo: RF-008 aclarado; con `NOT_FOUND` no
hay correo con el que calcular la huella, y la negativa por la cuenta no llega a evaluar el código.
Verificación: T-038 (caducidad dentro de la gracia) y T-041 (límite, ya validado, proceso inexistente y
negativa por la cuenta). La caducidad del proceso se comprueba antes que la cuenta.

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
- **Admin**: solo lectura, sin borrar ni añadir, y acceso denegado sin el permiso (RF-013). Con
  `change_securityevent` pero sin `view_securityevent`, el listado devuelve 403 (T-023). Filtros de
  tipo, resultado y rango de fechas, y búsqueda exacta por huella y parcial por IP (T-024).
- **Lista de proxies vacía**: `TRUSTED_PROXY_IPS` sin configurar no confía en ningún proxy (T-026).
- **Cuenta inactiva con credenciales válidas** (RF-004): `test_login_failed.py` registra una fila
  `LOGIN` con `success=False` y `reason=inactive_account`, tanto por el navegador como por el headless
  (T-029). `test_secrets_by_flow.py` añade el flujo de cuenta inactiva.
- **Comando**: `--dry-run` no borra; la purga elimina solo eventos de más de un año (RF-014).
- **CLI (P-03)**: `pytest backend/apps/audit`; `python manage.py purge_security_events --dry-run`;
  una petición de login por HTTP con `curl` contra el servidor de desarrollo.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-02 | Unitario, integración |
| RF-002 | M-01 | Unitario |
| RF-003 | M-02, M-03 | Integración |
| RF-004 | M-02, M-04 (D-13, D-14) | Integración |
| RF-005 | M-04 | Integración |
| RF-006 | M-04 | Integración (contador de allauth no cambia) |
| RF-007 | M-03, M-08 | Integración |
| RF-008 | M-03, M-08 (D-16) | Integración |
| RF-009 | M-03 | Integración |
| RF-010 | M-03, M-08 | Integración (parcial, ver abajo) |
| RF-011 | M-01, M-02, M-09 | Unitario |
| RF-012 | M-01, M-05, M-06 | Unitario, admin |
| RF-013 | M-05 (D-11, D-12) | Admin |
| RF-014 | M-06 | Comando |
| RF-015 | M-07 (D-08) | Integración en `apps/core` |
| RF-016 | M-01 | Unitario |

## RF sin cobertura
- **RF-010 (residual, aceptado por decisión del usuario):** el contrato de señales y los receptores
  cubren la edición de perfil y la deshabilitación de cuenta; el cambio y el restablecimiento de
  contraseña tienen emisor completo. **Nada emite hoy** la edición de perfil ni la deshabilitación,
  porque no existen esos flujos en el código. Quedan pendientes hasta que su feature los cree.
- **RF-012 (residual, aceptado por decisión del usuario el 2026-10-14):** no tienen guarda el SQL directo,
  las APIs internas del ORM, los métodos base llamados sin pasar por el modelo, los comandos integrados de
  Django (`flush`, `migrate`, `shell`) ni el uso deliberado del permiso de purga (D-07). La spec aclarada
  los excluye de las vías de la aplicación.

La regla de `sdd-plan` impide aprobar con RF sin cobertura. Este residual se acepta solo si lo confirmas
de forma explícita.

## Historial
- 2026-10-13 — Borrador inicial del plan — RF: RF-001 a RF-016 — Estado: borrador
- 2026-10-13 — Aprobación del plan con el residual de RF-010 aceptado por el usuario — RF: RF-001 a RF-016 — Estado: aprobado
- 2026-10-13 — Actualización tras el cambio de RF-013 y RF-015 (M-05, M-07, D-06, D-08; nuevas D-11 y D-12) — RF: RF-013, RF-015 — Estado: aprobado
- 2026-10-13 — Actualización tras RF-004 (M-04; nuevas D-13 y D-14) — RF: RF-004 — Estado: aprobado
- 2026-10-14 — Actualización tras la validación de RF-014 (D-07, M-01, M-06) y aclaración de RF-010 (nueva D-15) — RF: RF-010, RF-012, RF-014 — Estado: aprobado
- 2026-10-14 — Actualización tras la aclaración de RF-008 (nueva D-16) y de RF-012 (D-07 y residual de SQL directo) — RF: RF-008, RF-012 — Estado: aprobado
- 2026-10-14 — Actualización tras la tercera validación: D-05 (valor de desarrollo con `DEBUG`, P-02), D-07 y residual con el nuevo alcance de RF-012, D-16 (verificación con T-041 y precedencia de la caducidad) — RF: RF-008, RF-011, RF-012 — Estado: aprobado
- 2026-10-14 — Actualización tras la cuarta validación: D-03 (el 429 por IP no se registra) y D-15 (ningún rechazo de contraseña deja fila) — RF: RF-004, RF-010 — Estado: aprobado
