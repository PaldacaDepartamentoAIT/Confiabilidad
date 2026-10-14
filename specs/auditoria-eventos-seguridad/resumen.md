# Resumen — auditoria-eventos-seguridad
Estado: cerrada con riesgo residual aceptado · Última actualización: 2026-10-14

## Qué se hizo
Una app nueva, `backend/apps/audit/`, guarda un registro de cada evento sensible de una cuenta en la
tabla `audit_securityevent` (modelo `SecurityEvent`). Cada fila lleva tipo de evento, fecha en UTC,
IP real del cliente, user agent, huella HMAC del correo, huella HMAC de la clave de sesión, resultado
(éxito o fallo) y metadatos (RF-001). No hay clave foránea a la cuenta: la relación con una persona
solo se hace con la huella del correo. Por las vías de la aplicación (la API pública del ORM, el panel
de administración y los comandos de la aplicación) la tabla solo admite inserciones, y la única forma
de borrar es el comando de purga de eventos de más de un año.

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
  lo decide allauth (RF-006). La limitación de peticiones por IP de la vista de login (30 por minuto)
  responde 429 antes de comprobar la contraseña y no deja fila: esas peticiones no prueban credenciales,
  y registrarlas permitiría inflar la tabla.
- **Cierre de sesión** (RF-009), **registro y solicitud pendiente** (RF-007) y **códigos** (RF-008): los
  servicios de `apps/accounts` emiten señales propias (`apps/accounts/signals.py`) y la auditoría las
  recibe, así que accounts no importa nada de audit. Un código rechazado deja una validación con
  resultado fallo cuando es incorrecto, ha caducado él o su proceso, se alcanzó el límite de intentos o
  ya estaba validado. Si el proceso no existe, o el restablecimiento se rechaza porque la cuenta cambió
  o está inactiva, no se registra nada. Si el proceso ha caducado, se registra el fallo aunque la cuenta
  también haya cambiado. Una creación de cuenta rechazada (cuenta ya existente, proceso caducado o
  contraseña no válida) no deja ningún evento de registro.
- **Contraseña** (RF-010): se registran el cambio y el restablecimiento completados. Un intento
  rechazado, por cualquier motivo, no deja ninguna fila.
- **Sin datos sensibles** (RF-011): nunca se guardan contraseñas, códigos, tokens ni el correo en claro.
  El correo (en minúsculas y sin espacios a los lados) y la clave de sesión se guardan como HMAC-SHA256
  con la clave `AUDIT_HASH_SECRET`, calculada en el punto único `apps/core/fingerprints.py`. Si la clave
  falta o está vacía y `DJANGO_DEBUG` está activo (desarrollo, Docker Compose), se usa el valor de
  desarrollo `dev-audit-secret-change-me`; sin `DEBUG`, `manage.py check` falla con `audit.E001`.
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
  lista está vacía, no confía en nadie y registra la IP de la conexión directa. Los espacios alrededor de
  cada IP de la lista se ignoran.
- **Configuración nueva**: `AUDIT_HASH_SECRET` (obligatoria sin `DEBUG`), `TRUSTED_PROXY_IPS` (vacía por defecto),
  `ACCOUNT_ADAPTER` y el middleware `apps.audit.middleware.CurrentRequestMiddleware`. Las acciones
  humanas pendientes (clave en producción, IP del proxy, `.env` local y migraciones) están en
  `HUMAN_TODO.md`.

### Límites conocidos (riesgos residuales aceptados)
- **Perfil y deshabilitación sin emisor** (RF-010): los receptores y las señales existen, pero hoy
  ningún flujo del código edita perfiles ni deshabilita cuentas, así que no se generan esas filas. Se
  activarán solas cuando la feature que cree esos flujos emita las señales.
- **Vías fuera de la aplicación** (RF-012): las guardas viven en los métodos públicos del ORM. Pueden
  modificar o borrar filas el SQL directo contra la base de datos, las APIs internas del ORM (por
  ejemplo `_raw_delete`), los métodos base llamados sin pasar por el modelo, los comandos integrados de
  Django (`flush`, `migrate audit zero`, `shell`) y el código que use a propósito el permiso interno de
  la purga. La protección a nivel de base de datos está fuera de alcance. El test que vigila el permiso
  de purga no ve accesos con nombres construidos en ejecución.
- **Rechazos dentro de una transacción**: que un restablecimiento o una creación de cuenta rechazados
  por contraseña no válida no dejen fila lo garantiza hoy la transacción de `complete()`, que revierte
  cualquier fila escrita antes del error.
- **Altas fuera del registro** (RF-007): `seed_test_user` y `createsuperuser` crean cuentas sin evento
  de registro.
- **Login fallido en el panel de administración**: no pasa por allauth y no deja fila; el login
  correcto sí se registra.
- **Reautenticación**: una reautenticación rechazada puede registrarse como inicio de sesión fallido.
- **Arranque sin clave en ASGI**: sin `DEBUG`, `manage.py check` falla sin `AUDIT_HASH_SECRET`, pero un
  servidor ASGI no ejecuta los checks al arrancar; sin la clave, el primer evento falla con
  `ImproperlyConfigured`.
- **`X-Forwarded-For` sin validar como IP**: la última entrada se usa tal cual. Solo importa si el proxy
  de confianza está mal configurado.
- **`TRUSTED_PROXY_IPS` sin validar**: una entrada en formato CIDR nunca coincide. Es un fallo seguro
  (no confía), pero silencioso.
- **Restablecimiento nativo de allauth**: su receptor está conectado, pero hoy la ruta nativa no
  funciona por falta de `HEADLESS_FRONTEND_URLS`. El restablecimiento propio de accounts sí se
  registra.
- **Proxies encadenados** (RF-015): con dos proxies de confianza en cadena se registra la IP del proxy
  interior, no la del cliente. La spec contempla un único proxy.
- **Correo mal formado** (RF-004): un login con un correo no válido responde 400 sin evento.
- **Bloqueo por el límite de IP** (RF-005): el límite por IP de allauth también genera `LOCKOUT` con la
  huella del correo intentado, y los metadatos no lo distinguen del límite por cuenta.
- **Huecos de test aceptados**: el 429 por IP sin fila (RF-004), la presencia de los filtros laterales
  y el «hasta» inclusivo (RF-013), y la huella de sesión del flujo `app` (RF-003, RF-009) no tienen
  test; la validación los confirmó con sondas.
- **Docker** (P-02): la construcción de la imagen no se pudo verificar en la sesión remota (Docker Hub
  devolvió 429); está en `HUMAN_TODO.md`.

## Cómo probarlo
Todo se hace sin frontend, desde la raíz del repositorio. Docker Compose activa `DJANGO_DEBUG`, así que
funciona sin `backend/.env`; para usar tu propia clave de desarrollo, mira `HUMAN_TODO.md`. Los pasos
van en orden: algunos usan valores que obtienes en un paso anterior.

### Tests automáticos

1. Ejecuta los tests de auditoría:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend pytest apps/audit --no-cov
   ```
   Deberías ver todos los tests en verde. El criterio principal de la feature (un inicio de sesión
   exitoso y uno fallido dejan dos filas con la IP real) está en `apps/audit/tests/test_acceptance.py`.

### Preparación

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

### Inicio de sesión e IP real

4. Inicia sesión con la contraseña correcta. `<PASSWORD>` es la que escribiste en el paso 3:
   ```bash
   curl -s -X POST http://localhost:8000/_allauth/app/v1/auth/login -H "Content-Type: application/json" -d '{"email": "auditoria@example.com", "password": "<PASSWORD>"}'
   ```
   Deberías ver `"status": 200` y un `session_token`; apúntalo, es el `<SESSION_TOKEN>` del paso 6.
   Ahora con una contraseña incorrecta y una cabecera de intermediario falsa:
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
   `172.18.0.1`), y no `203.0.113.99`: sin `TRUSTED_PROXY_IPS`, la cabecera se ignora. Apunta esa IP:
   es la `<IP_DIRECTA>` del paso 17. Comprueba también que no se guarda nada en claro:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; e = SecurityEvent.objects.filter(event_type='login', success=True).first(); print(e.user_email_hash, e.session_key)"
   ```
   Deberías ver dos textos de 64 caracteres hexadecimales: las huellas del correo y de la sesión. Ni el
   correo ni la clave de sesión aparecen en claro.

### Contraseña y sesión

6. Cambia la contraseña. `<SESSION_TOKEN>` sale del paso 4 y `<PASSWORD>` es la actual. Prueba
   primero con una contraseña débil, que se rechaza:
   ```bash
   curl -s -X POST http://localhost:8000/_allauth/app/v1/account/password/change -H "Content-Type: application/json" -H "X-Session-Token: <SESSION_TOKEN>" -d '{"current_password": "<PASSWORD>", "new_password": "12345678"}'
   ```
   Deberías ver `"status": 400`, y el rechazo no deja ninguna fila. Ahora con una contraseña nueva
   robusta que eliges tú, `<NEW_PASSWORD>`:
   ```bash
   curl -s -X POST http://localhost:8000/_allauth/app/v1/account/password/change -H "Content-Type: application/json" -H "X-Session-Token: <SESSION_TOKEN>" -d '{"current_password": "<PASSWORD>", "new_password": "<NEW_PASSWORD>"}'
   ```
   Deberías ver `"status": 200`. Comprueba las filas de cambio de contraseña:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; print([(e.success, e.metadata) for e in SecurityEvent.objects.filter(event_type='password_change')])"
   ```
   Deberías ver `[(True, {})]`: una sola fila, la del cambio correcto.

7. Cierra sesión. El cambio de contraseña invalida la sesión del paso 4, así que inicia sesión otra vez
   con `<NEW_PASSWORD>`:
   ```bash
   curl -s -X POST http://localhost:8000/_allauth/app/v1/auth/login -H "Content-Type: application/json" -d '{"email": "auditoria@example.com", "password": "<NEW_PASSWORD>"}'
   ```
   Deberías ver `"status": 200` y un `session_token` nuevo. En el comando siguiente,
   `<NEW_SESSION_TOKEN>` es ese valor:
   ```bash
   curl -s -X DELETE http://localhost:8000/_allauth/app/v1/auth/session -H "X-Session-Token: <NEW_SESSION_TOKEN>"
   ```
   Deberías ver `"status": 401`: allauth responde así porque ya no hay sesión. Comprueba la fila:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; print([(e.success, e.metadata) for e in SecurityEvent.objects.filter(event_type='logout')[:1]])"
   ```
   Deberías ver `[(True, {})]`.

### Códigos

8. Envía un código incorrecto en un registro nuevo:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration start --email otra@example.com --name "Otra Persona" --birthdate 1990-01-01 --country es
   ```
   Deberías ver `public_id: …` y `code: …`. `<PUBLIC_ID>` es ese `public_id`; usa `000000` como código
   (si justo te tocó ese código, usa `111111`):
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> 000000
   ```
   Deberías ver `CommandError: Wrong code.`. Comprueba la fila:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; print([(e.success, e.metadata) for e in SecurityEvent.objects.filter(event_type='code_verified')[:1]])"
   ```
   Deberías ver `[(False, {})]`: la validación fallida queda registrada.

### Rechazos del inicio de sesión

9. Desactiva la cuenta e intenta entrar con la contraseña correcta (`<NEW_PASSWORD>` del paso 6):
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.accounts.models import User; User.objects.filter(email='auditoria@example.com').update(is_active=False)"
   ```
   ```bash
   curl -s -X POST http://localhost:8000/_allauth/app/v1/auth/login -H "Content-Type: application/json" -d '{"email": "auditoria@example.com", "password": "<NEW_PASSWORD>"}'
   ```
   Deberías ver `"status": 401`. Comprueba la fila:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; print([(e.success, e.metadata) for e in SecurityEvent.objects.filter(event_type='login')[:1]])"
   ```
   Deberías ver `[(False, {'reason': 'inactive_account'})]`. Vuelve a activar la cuenta:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.accounts.models import User; User.objects.filter(email='auditoria@example.com').update(is_active=True)"
   ```

10. Provoca el bloqueo por límite con varios intentos fallidos seguidos:
    ```bash
    for intento in 1 2 3 4 5 6; do curl -s -X POST http://localhost:8000/_allauth/app/v1/auth/login -H "Content-Type: application/json" -d '{"email": "auditoria@example.com", "password": "incorrecta"}'; echo; done
    ```
    Deberías ver `"status": 400` en todas las respuestas, y en la última (o antes, si en los últimos
    minutos ya hubo intentos fallidos) el código `too_many_login_attempts`. Comprueba las filas:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; print([(e.success, e.metadata) for e in SecurityEvent.objects.filter(event_type='lockout')[:1]])"
    ```
    Deberías ver `[(False, {'reason': 'too_many_login_attempts'})]`. Junto a ese bloqueo, el mismo
    intento deja una fila `login` fallida con el mismo motivo. allauth bloquea ese correo durante unos
    minutos; el paso 11 lo libera.

11. Restablece la contraseña con el comando de restablecimiento:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset start --email auditoria@example.com
    ```
    Deberías ver `public_id: …` y `code: …`. En los dos comandos siguientes, `<PUBLIC_ID>` y `<CODE>`
    son esos valores:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset verify <PUBLIC_ID> <CODE>
    ```
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset complete <PUBLIC_ID>
    ```
    Te pedirá la contraseña nueva. Deberías ver `account: auditoria@example.com`. Comprueba la fila:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; print([(e.success, e.metadata) for e in SecurityEvent.objects.filter(event_type='password_reset')[:1]])"
    ```
    Deberías ver `[(True, {})]`. El restablecimiento también borra los intentos fallidos, así que el
    bloqueo del paso 10 desaparece.

### Solo inserción y purga

12. Intenta modificar y borrar los eventos desde el ORM:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; SecurityEvent.objects.all().update(success=True)"
    ```
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; SecurityEvent.objects.all().delete()"
    ```
    En los dos casos deberías ver un error que termina en
    `InsertOnlyError: Security events are insert-only; they cannot be changed or deleted.`

13. Crea un evento con más de un año de antigüedad (insertar sí está permitido) y prueba la purga:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from datetime import timedelta; from django.utils import timezone; from apps.audit.models import SecurityEvent; SecurityEvent.objects.create(event_type='login', success=True, created_at=timezone.now() - timedelta(days=400))"
    ```
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py purge_security_events --dry-run
    ```
    Deberías ver `1 security events would be deleted.`, y no se borra nada. Ahora la purga real:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py purge_security_events
    ```
    Deberías ver `1 security events deleted.`. Los eventos de los pasos anteriores siguen ahí: la
    purga nunca borra eventos de menos de un año.

### Consulta en el panel de administración

14. Crea un superusuario (te pedirá los datos):
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py createsuperuser
    ```
    Abre `http://localhost:8000/admin/audit/securityevent/` e inicia sesión. Deberías ver los eventos,
    los filtros laterales por tipo, resultado y fechas (`desde` y `hasta`), y ningún botón para añadir,
    editar ni borrar. Si abres un evento, todos sus campos son de solo lectura.

15. Busca los eventos de un correo. Calcula su huella:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.core.fingerprints import audit_email_fingerprint; print(audit_email_fingerprint('auditoria@example.com'))"
    ```
    Deberías ver 64 caracteres hexadecimales. Pégalos en la búsqueda del panel: deberías ver solo los
    eventos de ese correo. La búsqueda por IP admite una parte de la dirección (por ejemplo, `172.18`).

16. Comprueba que el acceso exige el permiso específico. Crea un usuario de staff con solo el permiso
    de ver eventos:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from datetime import date; from django.contrib.auth.models import Permission; from apps.accounts.models import User; u = User.objects.create_user('lector@example.com', 'Lector-Seguro-2026!', name='Lector', birthdate=date(1990, 1, 1), country='ES', is_staff=True); u.user_permissions.add(Permission.objects.get(codename='view_securityevent'))"
    ```
    Cierra la sesión del panel, entra como `lector@example.com` con la contraseña `Lector-Seguro-2026!`
    y abre la misma dirección del paso 14: deberías ver los eventos en solo lectura. Quítale el permiso:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.accounts.models import User; User.objects.get(email='lector@example.com').user_permissions.clear()"
    ```
    Recarga la página: deberías ver `403 Forbidden`.

### Configuración

17. Prueba el proxy de confianza. Para el backend y vuelve a arrancarlo confiando en la IP que apuntaste
    en el paso 5 (`<IP_DIRECTA>`):
    ```bash
    docker compose -f docker/docker-compose.yml stop backend
    ```
    ```bash
    docker compose -f docker/docker-compose.yml run --rm --service-ports -e TRUSTED_PROXY_IPS=<IP_DIRECTA> backend
    ```
    Deja ese terminal abierto y, en otro, repite el login fallido con la cabecera:
    ```bash
    curl -s -X POST http://localhost:8000/_allauth/app/v1/auth/login -H "Content-Type: application/json" -H "X-Forwarded-For: 203.0.113.99" -d '{"email": "auditoria@example.com", "password": "incorrecta"}'
    ```
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.audit.models import SecurityEvent; print(SecurityEvent.objects.filter(event_type='login').first().ip)"
    ```
    Deberías ver `203.0.113.99`: ahora la conexión llega desde un proxy de confianza y se usa la IP del
    cliente original. Detén el backend del primer terminal con Ctrl+C y vuelve a levantarlo como antes:
    ```bash
    docker compose -f docker/docker-compose.yml up -d backend
    ```

18. Comprueba la clave de auditoría. Con `DEBUG` y sin clave, el backend arranca con el valor de
    desarrollo:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm -e DJANGO_DEBUG=1 -e AUDIT_HASH_SECRET= backend python manage.py check
    ```
    Deberías ver `System check identified no issues (0 silenced).`. Sin `DEBUG` y sin clave, como en
    producción, no arranca:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm -e DJANGO_DEBUG=0 -e AUDIT_HASH_SECRET= backend python manage.py check
    ```
    Deberías ver `(audit.E001) AUDIT_HASH_SECRET must not be empty.`.

### Suite completa

19. Ejecuta la suite completa:
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

### Clave obligatoria en producción, valor fijo en desarrollo
En producción, arrancar sin la clave de auditoría sería peligroso: los eventos fallarían o, peor, se
firmarían con una clave conocida. Por eso, sin `DEBUG`, el check `audit.E001` impide arrancar. En
desarrollo, en cambio, un clon limpio tiene que levantarse con un solo `docker compose up` (P-02), así
que con `DEBUG` activo se usa un valor fijo y público. Ese valor no protege nada, y no tiene que
hacerlo: en desarrollo no hay datos reales.

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
