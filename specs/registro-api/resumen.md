# Resumen — registro-api

## Qué se hizo
El primer paso del registro, el formulario, ya se puede usar desde la web y desde el escritorio. El
endpoint valida los datos, empieza el registro con el servicio de `procesos-pendientes` y devuelve
el identificador público con el que el cliente lleva a la pantalla de verificación. Las pantallas
llegarán con una feature de frontend (S-01).

- **Dos rutas** (D-01): `POST /api/browser/v1/registration` para la web, que exige el token CSRF
  (RF-014), y `POST /api/app/v1/registration` para el cliente de aplicación, sin CSRF. La segunda
  la puede usar cualquier cliente que no sea un navegador; sus defensas son los límites (S-19).
- **Cuerpo**, solo en JSON (`Content-Type: application/json`; cualquier otro tipo es un cuerpo
  ilegible, D-16): `name`, `birthdate` (`AAAA-MM-DD`), `email`, `country`, `terms`
  (`{"version", "locale", "accepted": true}`) y, opcional, `language` (`es`, `pt-BR` o `en`).
- **Respuesta neutra** (RF-005): `202` con `{"public_id", "message"}`, idéntica tanto si el correo es
  nuevo como si tiene un registro pendiente o una cuenta, activa o inactiva. Lo que depende del
  caso (crear o repetir el registro, enviar el código o el aviso "ya tienes cuenta") pasa fuera de
  la respuesta, en el worker. Con un correo que tiene cuenta, el identificador no tiene registro
  detrás (RF-008).
- **Errores por campo** (RF-002): `400` con `{"errors": {campo: [{"code", "message"}]}}`, todos los
  errores de todos los campos a la vez. Cada error tiene un código estable y un texto en el idioma
  de la solicitud.
- **Reglas**: las de la cuenta para nombre, fecha (18 años y 5 días, S-02) y país; el correo debe
  tener un dominio con punto y no puede ser una IP (RF-003), y se guarda en su forma canónica: las
  variantes del mismo buzón (`ana@ｅxample.com`, `"ana"@example.com`) pasan a `ana@example.com`
  (D-15); los términos exigen la marca
  `accepted: true` y un documento de la versión vigente, en cualquier idioma (RF-004).
- **Términos** (RF-009): el registro pendiente guarda el documento aceptado, y la aceptación se
  registra al completar el registro con la contraseña. Si para entonces el documento ya no es de la
  versión vigente, la cuenta se crea sin aceptación (S-12).
- **Idioma** (RF-013): el campo `language`; si falta, la cabecera `Accept-Language` por idioma base
  (`pt-PT` → `pt-BR`); si no, español. Es también el idioma que guarda la cuenta.
- **Límites de frecuencia** (RF-010, RF-011): por correo e IP, una solicitud válida cada 60 s y 5
  por hora; por IP, 20 solicitudes por hora, válidas o no. Al superarlos, `429` con
  `{"message", "retry_after"}` y la cabecera `Retry-After`, igual en los tres casos. Las
  rechazadas por un límite no cuentan. Se configuran en `backend/.env.example`.

### Límites conocidos
- Solicitudes simultáneas con la misma clave pueden colarse por encima del límite (D-09).
- Un bot con muchas IP puede generar registros hasta el límite de cada una; la respuesta sería un
  CAPTCHA, fuera de alcance (S-19).
- Siguen sin límite el reenvío y la verificación del código, y pedir el cambio de contraseña (S-15,
  `specs/cambio-contrasena/HUMAN_TODO.md`).

## Cómo probarlo
Requisitos: Docker y `main` actualizado. Todos los comandos se ejecutan desde la raíz del
repositorio. Sin proveedor de correo configurado, los correos salen por la consola del worker: ahí
se lee el código.

1. Levanta los servicios y aplica las migraciones:
   ```bash
   docker compose -f docker/docker-compose.yml up -d db redis
   ```
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
   ```
   Deberías ver, entre otras, `accounts.0012_pendingregistration_terms... OK`. Levanta el backend y
   el worker:
   ```bash
   docker compose -f docker/docker-compose.yml up -d backend worker beat
   ```
2. Publica unos términos de prueba (versión `1`, en los tres idiomas, desde ayer):
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from datetime import timedelta; from django.utils import timezone; from apps.consents.models import Terms; [Terms.objects.get_or_create(kind='terms', version='1', locale=locale, defaults={'content': 'Términos de prueba.', 'published_at': timezone.now() - timedelta(days=1)}) for locale in ('es', 'pt-BR', 'en')]"
   ```
   Comprueba que están vigentes:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py consents current --kind terms --locale es
   ```
   Deberías ver `version: 1`.
3. Envía el formulario desde el cliente de aplicación:
   ```bash
   curl -s -i -X POST http://localhost:8000/api/app/v1/registration -H "Content-Type: application/json" -d '{"name": "Ana García", "birthdate": "1990-05-17", "email": "ana@example.com", "country": "ES", "terms": {"version": "1", "locale": "es", "accepted": true}}'
   ```
   Deberías ver `202 Accepted` y un cuerpo con `public_id` y el mensaje «Si puedes registrarte con
   este correo, recibirás un código en unos minutos…». En los pasos siguientes, `<PUBLIC_ID>` es ese
   `public_id`.
4. Lee el código en la salida del worker:
   ```bash
   docker compose -f docker/docker-compose.yml logs worker --tail 60
   ```
   Deberías ver el correo «Confirma tu correo para crear tu cuenta» con un código de 6 dígitos. Si
   aún no aparece, espera unos segundos y repite. Desde aquí, `<CODE>` es ese código.
5. Repite el comando del paso 3 enseguida. Deberías ver `429`, la cabecera `Retry-After` y el
   mensaje «Has hecho demasiadas solicitudes. Espera N segundos…»: el mismo correo desde la misma IP
   solo puede enviarse una vez por minuto. Pasado ese tiempo, la misma solicitud vuelve a dar `202`
   con otro `public_id`, y el registro pendiente conserva los datos del primero; en ese caso, usa en
   los pasos 9 y 10 el último `public_id` y el código de su correo.
6. Envía un formulario con errores, pidiendo los textos en inglés:
   ```bash
   curl -s -X POST http://localhost:8000/api/app/v1/registration -H "Content-Type: application/json" -H "Accept-Language: en-GB" -d '{"name": "", "birthdate": "2020-01-01", "email": "ana@localhost", "country": "XX", "terms": {"version": "1", "locale": "es", "accepted": false}}'
   ```
   Deberías ver `errors` con un error en cada campo: `blank`, `birthdate_under_minimum_age`,
   `email_domain_without_dot`, `country_invalid` y `terms_not_accepted`, con sus textos en inglés.
7. Prueba la ruta web. Sin token CSRF:
   ```bash
   curl -s -i -X POST http://localhost:8000/api/browser/v1/registration -H "Content-Type: application/json" -d '{}'
   ```
   Deberías ver `403 Forbidden` y `CSRF verification failed.`. Ahora obtén la cookie CSRF, como hace
   la web al cargar:
   ```bash
   curl -s -o /dev/null -c cookies.txt http://localhost:8000/_allauth/browser/v1/auth/session
   ```
   ```bash
   grep csrftoken cookies.txt
   ```
   La última columna de esa línea es `<CSRF_TOKEN>`. Envía el formulario con ella:
   ```bash
   curl -s -i -b cookies.txt -X POST http://localhost:8000/api/browser/v1/registration -H "Content-Type: application/json" -H "X-CSRFToken: <CSRF_TOKEN>" -d '{"name": "Bruno Souza", "birthdate": "1988-03-02", "email": "bruno@example.com", "country": "BR", "language": "pt-BR", "terms": {"version": "1", "locale": "pt-BR", "accepted": true}}'
   ```
   Deberías ver `202 Accepted` y el mensaje en portugués. En el worker llega «Confirme seu e-mail
   para criar sua conta».
8. Prueba el caso de un correo con cuenta. Crea la cuenta:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from datetime import date; from apps.accounts.models import User; User.objects.create_user('carla@example.com', 'una-contraseña-larga', name='Carla Ruiz', birthdate=date(1985,1,20), country='ES')"
   ```
   Envía el formulario con ese correo:
   ```bash
   curl -s -i -X POST http://localhost:8000/api/app/v1/registration -H "Content-Type: application/json" -d '{"name": "Otra Persona", "birthdate": "1990-05-17", "email": "carla@example.com", "country": "ES", "terms": {"version": "1", "locale": "es", "accepted": true}}'
   ```
   Deberías ver la misma respuesta que en el paso 3, con otro `public_id`. Repite el comando del
   paso 4: llega el aviso «Ya tienes una cuenta con este correo», sin código.
9. Verifica el código del paso 4:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> <CODE>
   ```
   Deberías ver `Code verified.`
10. Completa el registro. Te pedirá la contraseña sin mostrarla; usa 12 caracteres o más:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration complete <PUBLIC_ID>
    ```
    Verás `account: ana@example.com`. Comprueba que se registró la aceptación de los términos:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py consents status ana@example.com
    ```
    Deberías ver `terms: accepted`.
11. Prueba el límite por IP con un segundo servidor que solo admite una solicitud por hora y por IP,
    con su propia caché para que no cuenten las solicitudes de los pasos anteriores:
    ```bash
    docker compose -f docker/docker-compose.yml run -d --rm --name registro-limite-ip -e REGISTRATION_RATE_IP_PER_HOUR=1 -e CACHE_URL=redis://redis:6379/5 -p 8001:8000 backend
    ```
    Envía un cuerpo vacío y repite el mismo comando una segunda vez:
    ```bash
    curl -s -i -X POST http://localhost:8001/api/app/v1/registration -H "Content-Type: application/json" -d '{}'
    ```
    La primera vez deberías ver `400` con un error `required` en cada campo; la segunda, `429` con
    `Retry-After` cerca de 3600 (los segundos que faltan para que pase una hora) y sin errores de
    validación: superado el límite por IP, la solicitud ya no se
    valida. Para el servidor de prueba:
    ```bash
    docker stop registro-limite-ip
    ```
12. Ejecuta la suite completa (cobertura mínima 80 % sobre todo el proyecto):
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend pytest -q
    ```
    Deberías ver todos los tests en verde.

## Marco teórico
### Enumeración de cuentas
Un formulario que responde «ese correo ya está registrado» permite a cualquiera averiguar quién tiene
cuenta, y con eso preparar un phishing creíble o probar contraseñas filtradas. Por eso la respuesta
es la misma en los tres casos y el aviso «ya tienes cuenta» va al buzón del titular, que es el único
que puede leerlo.

### Límite por correo e IP, y no solo por correo
Si el límite contara solo por correo, un tercero podría enviar cinco formularios por hora con el
correo de otra persona y dejarla sin poder registrarse. Contando la pareja correo e IP, quien abusa
solo se bloquea a sí mismo. El límite por IP, aparte, frena a una sola máquina que intenta mandar
códigos a miles de correos ajenos.

### CSRF y por qué la app está exenta
CSRF (*cross-site request forgery*) es que otra web haga que tu navegador envíe una petición a este
sitio aprovechando tus cookies. La ruta web exige un token que solo puede leer una página de este
mismo sitio. El cliente de aplicación no usa cookies, así que no hay nada que aprovechar, pero
tampoco hay forma de distinguirlo de un script: por eso su única defensa son los límites.

### `202 Accepted`
`202` significa «recibido; se procesará después», a diferencia de `201 Created` («ya existe»). Encaja
con lo que pasa de verdad: en la respuesta solo se reserva el identificador, y el registro, si
procede, se crea en el worker.

### `Accept-Language`
Es la cabecera con la que el navegador anuncia los idiomas de su usuario, por orden de preferencia
(`fr, en;q=0.8`). Aquí solo es el respaldo: manda el idioma que la persona eligió en la interfaz,
porque se guarda en la cuenta y decide el idioma de sus avisos de seguridad.

### Peticiones simples y comprobación previa (preflight)
Un navegador deja que cualquier web envíe a otro sitio, sin preguntar, las peticiones «simples»: las
de un formulario HTML (`application/x-www-form-urlencoded`, `multipart/form-data` o `text/plain`).
Para enviar JSON a otro origen, antes tiene que preguntar al servidor con una petición `OPTIONS`, y
CORS solo responde que sí a los orígenes configurados (el escritorio Tauri). Por eso las dos rutas
solo admiten JSON (D-16): así otra web no puede usar el navegador de su visitante para empezar
registros.

### Forma canónica de un correo
Un mismo buzón se puede escribir de varias formas: `ana@ｅxample.com` (letras de ancho completo),
`"ana"@example.com` (comillas que no cambian nada) o con el dominio en punycode
(`ana@xn--espaa-rta.es` es `ana@españa.es`). Si el sistema las tratara como correos distintos, una
variante saltaría el límite y hasta permitiría una segunda cuenta para el mismo buzón. La API las
convierte todas a una sola forma antes de usarlas (D-15).

