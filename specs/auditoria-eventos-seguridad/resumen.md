# Resumen — auditoria-eventos-seguridad
Estado: pendiente de validación · Última actualización: 2026-10-14

## Qué se hizo
Una app nueva, `backend/apps/audit/`, guarda un registro de cada evento sensible de una cuenta en la
tabla `audit_securityevent` (modelo `SecurityEvent`). Cada fila lleva tipo de evento, fecha en UTC,
IP real del cliente, user agent, huella HMAC del correo, huella HMAC de la clave de sesión, resultado
(éxito o fallo) y metadatos (RF-001). No hay clave foránea a la cuenta: la relación con una persona
solo se hace con la huella del correo. La tabla solo admite inserciones desde la aplicación, y la
única forma de borrar es el comando de purga de eventos de más de un año.

- **Once tipos de evento** (RF-002): registro de cuenta, solicitud de registro pendiente, envío de
  código, validación de código, inicio de sesión, bloqueo por límite, cierre de sesión, cambio de
  contraseña, restablecimiento de contraseña, edición de perfil y deshabilitación de cuenta. La fecha
  (`created_at`) está indexada (RF-016).
- **Inicio de sesión exitoso** (RF-003): lo registra la señal `user_logged_in` de Django, con la huella
  de la sesión ya iniciada (la que queda tras la rotación de la clave).
- **Inicio de sesión fallido** (RF-004): lo registra el adaptador de allauth
  (`apps/audit/adapters.py`, ajuste `ACCOUNT_ADAPTER`). El motivo va en `metadata["reason"]` y solo puede
  ser `invalid_credentials` (credenciales incorrectas, también si el correo no existe),
  `too_many_login_attempts` (límite alcanzado) o `inactive_account` (cuenta inactiva, aunque la
  contraseña sea correcta).
- **Bloqueo por límite** (RF-005): el intento que allauth rechaza por el límite deja dos filas, un
  inicio de sesión fallido y un bloqueo. La aplicación no cuenta intentos ni bloquea por su cuenta: eso
  lo decide allauth (RF-006).
- **Cierre de sesión** (RF-009), **registro y solicitud pendiente** (RF-007) y **códigos** (RF-008): los
  servicios de `apps/accounts` emiten señales propias (`apps/accounts/signals.py`) y la auditoría las
  recibe, así que accounts no importa nada de audit. Un código rechazado deja una validación con
  resultado fallo cuando es incorrecto, ha caducado él o su proceso, se alcanzó el límite de intentos o
  ya estaba validado. Si el proceso no existe, o el restablecimiento se rechaza porque la cuenta cambió
  o está inactiva, no se registra nada.
- **Contraseña** (RF-010): se registran el cambio y el restablecimiento completados. Un intento
  rechazado por una contraseña no válida no deja ninguna fila.
- **Sin datos sensibles** (RF-011): nunca se guardan contraseñas, códigos, tokens ni el correo en claro.
  El correo (en minúsculas y sin espacios a los lados) y la clave de sesión se guardan como HMAC-SHA256
  con la clave `AUDIT_HASH_SECRET`, calculada en el punto único `apps/core/fingerprints.py`. Si la clave
  está vacía, `manage.py check` falla con `audit.E001`.
- **Solo inserción** (RF-012): `save()` y `save_base()` sobre una fila existente, `delete()`, `update()`
  y `delete()` del QuerySet, `bulk_create` con `update_conflicts` y el gestor base lanzan
  `InsertOnlyError`. El admin no ofrece añadir, cambiar ni borrar (un POST directo responde 403). El
  permiso interno de borrado solo se usa en el modelo, y un test lo vigila.
- **Consulta** (RF-013): en el panel de administración, en solo lectura, solo para quien tenga el
  permiso `audit.view_securityevent`. Filtros laterales por tipo, resultado y rango de fechas, búsqueda
  parcial por IP y búsqueda exacta por huella del correo.
- **Conservación y purga** (RF-014): `manage.py purge_security_events` borra los eventos de más de un
  año de calendario (desde un 29 de febrero, el corte cae el 28 de febrero del año anterior). Con
  `--dry-run` solo cuenta. El corte se calcula siempre con el reloj del servidor: no hay forma de
  pasarle una fecha.
- **IP real** (RF-015): `RealClientIPMiddleware` (`apps/core/middleware.py`) solo lee `X-Forwarded-For`
  cuando la conexión llega desde una IP exacta de `TRUSTED_PROXY_IPS`, y toma la última entrada. Si la
  lista está vacía, no confía en nadie y registra la IP de la conexión directa.
- **Configuración nueva**: `AUDIT_HASH_SECRET` (obligatoria), `TRUSTED_PROXY_IPS` (vacía por defecto),
  `ACCOUNT_ADAPTER` y el middleware `apps.audit.middleware.CurrentRequestMiddleware`. Las acciones
  humanas pendientes (clave en producción, IP del proxy, `.env` local y migraciones) están en
  `HUMAN_TODO.md`.

### Límites conocidos (riesgos residuales aceptados)
- **Perfil y deshabilitación sin emisor** (RF-010): los receptores y las señales existen, pero hoy
  ningún flujo del código edita perfiles ni deshabilita cuentas, así que no se generan esas filas. Se
  activarán solas cuando la feature que cree esos flujos emita las señales.
- **SQL directo** (RF-012): las guardas viven en el ORM. Una consulta SQL directa contra la base de
  datos puede modificar o borrar filas. La protección con un rol de base de datos está fuera de
  alcance. El test que vigila el permiso de purga tampoco ve accesos con nombres construidos en
  ejecución.
- **Restablecimiento rechazado**: que un restablecimiento con contraseña no válida no deje fila lo
  garantiza hoy la transacción de `complete()`, que revierte cualquier fila escrita antes del error.
- **Arranque sin clave en ASGI**: `manage.py check` falla sin `AUDIT_HASH_SECRET`, pero un servidor
  ASGI no ejecuta los checks al arrancar; sin la clave, el primer evento falla con
  `ImproperlyConfigured`.
- **`TRUSTED_PROXY_IPS` sin validar**: una entrada en formato CIDR nunca coincide. Es un fallo seguro
  (no confía), pero silencioso.
- **Restablecimiento nativo de allauth**: su receptor está conectado, pero hoy la ruta nativa no
  funciona por falta de `HEADLESS_FRONTEND_URLS`. El restablecimiento propio de accounts sí se
  registra.

## Cómo probarlo
Todo se hace sin frontend, desde la raíz del repositorio. Antes, añade `AUDIT_HASH_SECRET` a tu
`backend/.env` (ver `HUMAN_TODO.md`).

1. Ejecuta los tests de auditoría:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend pytest apps/audit --no-cov
   ```
   Deberías ver todos los tests en verde. El criterio principal de la feature (un inicio de sesión
   exitoso y uno fallido dejan dos filas con la IP real) está en `apps/audit/tests/test_acceptance.py`.

2. Levanta la base de datos, Redis y el backend, y aplica las migraciones:
   ```bash
   docker compose -f docker/docker-compose.yml up -d db redis backend
   ```
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
   ```
   Deberías ver `Applying audit.0001_initial... OK` y `Applying audit.0002_securityevent_base_manager... OK`,
   o `No migrations to apply.` si ya estaban aplicadas.

3. Crea una cuenta con el comando de registro:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration start --email auditoria@example.com --name "Ana Auditoria" --birthdate 1990-01-01 --country es
   ```
   Deberías ver `public_id: …` y `code: …`. En los dos comandos siguientes, `<PUBLIC_ID>` y `<CODE>`
   son esos valores:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> <CODE>
   ```
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration complete <PUBLIC_ID>
   ```
   Te pedirá una contraseña; usa una robusta. Deberías ver `account: auditoria@example.com`.

4. Inicia sesión con la contraseña correcta. `<PASSWORD>` es la que escribiste en el paso 3:
   ```bash
   curl -s -X POST http://localhost:8000/_allauth/app/v1/auth/login -H "Content-Type: application/json" -d '{"email": "auditoria@example.com", "password": "<PASSWORD>"}'
   ```
   Deberías ver `"status": 200` y un `session_token`. Ahora con una contraseña incorrecta y una
   cabecera de intermediario falsa:
   ```bash
   curl -s -X POST http://localhost:8000/_allauth/app/v1/auth/login -H "Content-Type: application/json" -H "X-Forwarded-For: 203.0.113.99" -d '{"email": "auditoria@example.com", "password": "incorrecta"}'
   ```
   Deberías ver `"status": 400`.

5. Mira las últimas filas:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; [print(e.event_type, e.success, e.ip, e.metadata) for e in SecurityEvent.objects.all()[:6]]"
   ```
   Deberías ver, de la más reciente a la más antigua, `login False <IP> {'reason': 'invalid_credentials'}`,
   `login True <IP> {}` y los eventos del registro (`account_registration`, `code_verified`,
   `code_sent` y `pending_registration`). Las dos filas de login tienen la misma IP, la de la conexión
   directa al contenedor (en local con Docker, la puerta de enlace de su red, por ejemplo
   `172.18.0.1`), y no `203.0.113.99`: sin `TRUSTED_PROXY_IPS`, la cabecera se ignora.

6. Intenta borrar los eventos desde el ORM:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; SecurityEvent.objects.all().delete()"
   ```
   Deberías ver un error que termina en
   `InsertOnlyError: Security events are insert-only; they cannot be changed or deleted.`

7. Prueba el comando de purga, primero sin borrar:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py purge_security_events --dry-run
   ```
   Deberías ver `0 security events would be deleted.`, porque todos los eventos tienen menos de un año.
   La purga real borra solo los de más de un año:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py purge_security_events
   ```
   Deberías ver `0 security events deleted.` y las filas del paso 5 siguen ahí.

8. Consulta los eventos en el panel de administración. Crea un superusuario (te pedirá los datos):
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py createsuperuser
   ```
   Abre `http://localhost:8000/admin/audit/securityevent/` e inicia sesión. Deberías ver los eventos,
   los filtros laterales por tipo, resultado y fechas, y ningún botón para añadir, editar ni borrar.
   Para buscar los eventos de un correo, calcula su huella:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.core.fingerprints import audit_email_fingerprint; print(audit_email_fingerprint('auditoria@example.com'))"
   ```
   Deberías ver 64 caracteres hexadecimales. Pégalos en la búsqueda del panel: deberías ver solo los
   eventos de ese correo.

9. Ejecuta la suite completa:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend pytest
   ```
   Deberías ver todos los tests en verde y la cobertura por encima del 80 %.

## Marco teórico
### Huella HMAC del correo y de la sesión
Un registro de auditoría tiene que permitir responder «¿qué hizo esta cuenta?» sin convertirse en una
lista de correos y sesiones que alguien pueda robar. Una huella HMAC mezcla el dato con una clave
secreta y produce un resumen del que no se puede recuperar el original. Con la clave sí se puede
calcular la huella de un correo concreto y buscarla, que es lo que hace el paso 8. Por eso la
búsqueda por huella es exacta: una búsqueda parcial sobre un resumen no significa nada. La clave de
auditoría es propia (`AUDIT_HASH_SECRET`), distinta de la de consentimientos, para que filtrar una
tabla no permita cruzarla con la otra. No se rota nunca: si cambia, las huellas nuevas dejan de
coincidir con las antiguas.

### IP real y proxy de confianza
Cuando una petición pasa por un proxy, la aplicación ve la IP del proxy, y el proxy añade la del
cliente en la cabecera `X-Forwarded-For`. Pero esa cabecera la puede escribir cualquiera: si la
aplicación se fiara siempre de ella, un atacante podría poner la IP que quisiera en el registro. Por
eso solo se lee cuando la conexión viene de una IP de la lista `TRUSTED_PROXY_IPS`, y se toma la
última entrada, que es la que añadió nuestro proxy. Con la lista vacía, la aplicación no confía en
nadie: registra la IP de la conexión directa, que es correcta mientras no haya proxy delante.

### Solo inserción: en la aplicación, no en la base de datos
Las guardas impiden modificar o borrar filas por cualquier camino del ORM y del panel. Pero viven en
el código Python: una consulta SQL directa contra la base de datos no pasa por ellas. Cerrar ese
hueco exigiría un rol de base de datos sin permisos de `UPDATE` ni `DELETE`, que quedó fuera de
alcance. Por eso la spec define las «vías de la aplicación» como ORM, panel y comandos, y el SQL
directo queda como riesgo aceptado.

### Por qué la purga no acepta una fecha
Una función de purga que recibe «la fecha de hoy» como parámetro permite pasarle una fecha futura, y
entonces el corte de un año también se mueve al futuro y borra eventos recientes. Tomar el reloj
dentro de la función elimina esa posibilidad: nadie puede adelantar la purga desde el código.

### Un año de calendario y el 29 de febrero
«Un año» no son 365 días: entre el 1 de marzo de 2027 y el de 2028 hay 366. La purga resta un año de
calendario a la fecha actual. El único día sin equivalente es el 29 de febrero: desde esa fecha, el
corte cae el 28 de febrero del año anterior, que conserva los eventos un día más en lugar de uno
menos.

### allauth decide y la auditoría registra
allauth no emite una señal cuando falla un inicio de sesión. Su punto de extensión es el adaptador:
`authentication_failed` (credenciales incorrectas), `pre_authenticate` (límite de intentos) y
`pre_login` (cuenta inactiva con contraseña correcta). El adaptador de auditoría sobrescribe esos tres
métodos solo para registrar, y siempre deja que allauth tome la decisión. Así no hay un segundo
contador de intentos que pueda contradecir al de allauth.

### Transacciones y un mutante que no se puede matar
Un mutante es un error introducido a propósito para comprobar que un test lo detecta. En el
restablecimiento de contraseña, un mutante que registraba un fallo antes de rechazar la contraseña no
lo detectó el test, y no por un defecto del test: `complete()` corre dentro de una transacción, y al
lanzarse el error la base de datos deshace todo lo escrito dentro, también esa fila. El mutante es
«equivalente»: no cambia nada observable. El test sí detectaría que alguien sacara el registro fuera
de la transacción.
