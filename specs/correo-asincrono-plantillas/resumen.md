# Resumen — correo-asincrono-plantillas
Estado: correcciones tras la validación implementadas, pendiente de validar de nuevo · Última actualización: 2026-10-15

## Qué se hizo
La aplicación envía sus correos desde una **bandeja de salida** en la base de datos, fuera de la
respuesta, con reintentos. Todo se puede disparar y revisar desde consola (`manage.py emails`) y
desde el panel de administración, sin frontend ni API.

- **Siete tipos de correo**, cada uno con su plantilla en español, portugués de Brasil e inglés
  (`EmailTemplate`, migración `0002` con los 21 textos iniciales):
  - con código: `registration_code` (verificar el correo del registro) y `password_reset_code`
    (restablecer la contraseña);
  - avisos: `account_exists` («ya tienes cuenta»), `password_reset_done`, `password_changed`,
    `account_disabled` y `sessions_closed`.

  Los avisos de seguridad no se pueden desactivar ni llevan enlace de baja.
- **Plantillas editables en el panel** (`/admin/`, *Email templates*), solo por superusuarios y por el
  grupo «Soporte técnico» (migración `0003`). Usan `{{ name }}` y, en los correos con código,
  `{{ code }}`, `{{ link }}` y `{{ expires_in }}`, que son obligatorios. Al guardar se
  rechazan las variables que no admite su tipo, cualquier otra sintaxis de plantilla, un asunto con
  saltos de línea y las direcciones hacia un dominio que no es el de la aplicación, juzgadas como
  las abriría el navegador:
  - con esquema (`https://`, `ftp://`, `https:/`), con `www.` o como dominio suelto
    (`evil.com/login`), también con letras no latinas (`пример.рф`) o con el punto `。`;
  - IP sueltas (`1.2.3.4/login`) y el dominio de una dirección de correo (`soporte@evil.com`);
  - cualquier dirección con un usuario delante del dominio (`evil.com@app…`, `evil.com\@app…`,
    `evil.com＠app…`), aunque lleve a la aplicación, porque solo sirve para disfrazar el enlace;
  - una dirección que no se puede analizar (`https://[evil.com`) se rechaza como problema de la
    plantilla, sin error del servidor.

  Un nombre con partes de una sola letra (`S.A.`) no cuenta como dirección; uno con partes de dos
  letras (`EE.UU.`) sí, y hay que reescribirlo. Cada cambio queda en el historial con el texto anterior, el autor y la fecha;
  desde la migración `0004`, también el primer cambio de cada plantilla instalada, porque el texto
  inicial queda registrado al instalarla. Las plantillas no se pueden crear ni borrar.
- **Bloque fijo de reporte** en todos los avisos («Si no fuiste tú, escríbenos a…»), que añade el
  sistema con `EMAIL_SUPPORT_ADDRESS` y que el panel no permite tocar.
- **Idioma**: el de la petición en los correos con código y el guardado en la cuenta en los avisos.
  El reenvío de un código usa el idioma de la petición que lo empezó, guardado en el registro
  pendiente o en la solicitud de cambio de contraseña (migración `0010` de `accounts`).
  Un idioma no admitido cae en español. Cuentas y registros guardan su idioma (migración `0007` de
  `accounts`).
- **Plazo relativo**: «vence en 14 minutos», calculado al entregar y redondeado hacia abajo; por
  debajo de un minuto, «menos de un minuto».
- **Enlace con el identificador público** en los correos con código:
  `<FRONTEND_BASE_URL>/register/continue#<PUBLIC_ID>` y `/password-reset/continue#<PUBLIC_ID>`. El
  identificador va tras `#`, que el navegador no envía al servidor.
- **Bandeja de salida** (`OutboundEmail`): la fila se crea en la misma transacción que la operación
  que la provoca y se encola en Celery al confirmar. Un barrido cada 30 s recoge lo que quedó
  pendiente, por ejemplo con Redis caído.
- **Reintentos**: un error temporal (red, autenticación, 4xx) espera 30 s, 1 min, 2 min… hasta un
  máximo de 15 min entre intentos. Un correo con código se reintenta mientras su código sirva; un
  aviso, durante `EMAIL_NOTICE_RETRY_HOURS` (24 h). Un rechazo 5xx del destinatario, del remitente o
  del contenido es definitivo desde el primer intento. Los fallidos quedan en el panel (*Failed
  emails*) hasta que soporte los borra; los entregados se borran.
- **El código nunca se guarda en claro**: en la bandeja va oculto con una máscara HMAC
  (`EMAIL_CODE_SECRET`) y se recupera solo al entregar. Si el código ya no sirve (se validó, se
  reemplazó o caducó), el correo se descarta sin enviarse. Un fallido no conserva ni la máscara, y
  si el error del proveedor cita el código, se guarda sustituido por `[code]`.
- **Tope del aviso «ya tienes cuenta»**: como mucho uno por cuenta cada
  `EMAIL_ACCOUNT_EXISTS_WINDOW_MINUTES` (60 min).
- **Proveedor por configuración**: sin `EMAIL_BACKEND`, los correos completos salen por la consola
  del worker; en producción, el SMTP de MXroute. Cambiar de proveedor solo cambia variables.
- **Sin enumeración por tiempo**: el registro y el cambio de contraseña dejan en la respuesta el
  mismo trabajo tenga o no cuenta el correo, y el correo se decide y se envía después (cambios del
  2026-10-14 en `procesos-pendientes` y `cambio-contrasena`).

## Configuración del envío
Esta sección recoge todo lo necesario para rehacer la configuración o cambiar de proveedor. Los
pasos con su comprobación están también en `HUMAN_TODO.md` (*Preparar el envío de correo con
MXroute y Cloudflare*). `<TU_DOMINIO>` es tu dominio en Cloudflare, y `<SERVIDOR_MXROUTE>` y
`<SERVIDOR_MXROUTE_RELAY>` son los dos servidores MX (prioridad 10 y 20) del correo de bienvenida de
MXroute.

### Subdominio y buzón (MXroute)
- Dominio de envío: `notificaciones.<TU_DOMINIO>`, separado del correo de trabajo para no mezclar
  reputación ni cupo.
- Buzón remitente: `no-responder@notificaciones.<TU_DOMINIO>`, con una contraseña larga y única.
- Clave DKIM: en el panel de MXroute, sección DNS o DKIM del subdominio (registro
  `x._domainkey`, valor `v=DKIM1; k=rsa; p=…`).
- Límite de envío: según su documentación, 400 correos por hora y dirección; hay que confirmarlo
  con su soporte, junto con el permiso para correo transaccional automático.

### Registros DNS (Cloudflare)
En *DNS → Records*, con el *Name* sin `<TU_DOMINIO>`, porque Cloudflare lo añade:

| Tipo | Name | Contenido | Prioridad |
|---|---|---|---|
| MX | `notificaciones` | `<SERVIDOR_MXROUTE>` | 10 |
| MX | `notificaciones` | `<SERVIDOR_MXROUTE_RELAY>` | 20 |
| TXT | `notificaciones` | `v=spf1 include:mxroute.com -all` | — |
| TXT | `x._domainkey.notificaciones` | la clave DKIM de MXroute | — |
| TXT | `_dmarc.notificaciones` | `v=DMARC1; p=none; rua=mailto:<CORREO_INFORMES>` | — |

`<CORREO_INFORMES>` es el buzón que recibe los informes DMARC. Un solo registro SPF por nombre; un
CNAME del correo, si lo hay, en *DNS only* (nube gris). Tras 2–4 semanas sin fallos en los
informes, DMARC pasa a `p=quarantine` y después a `p=reject`.

### Variables de entorno
En desarrollo van comentadas en `backend/.env.example` (sin ellas, consola). En producción van en
el archivo cifrado con SOPS; `EMAIL_HOST_PASSWORD` y `EMAIL_CODE_SECRET` solo deben vivir ahí:

| Variable | Producción | Por defecto |
|---|---|---|
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | consola |
| `EMAIL_HOST` | `<SERVIDOR_MXROUTE>` | `localhost` |
| `EMAIL_PORT` | `465` (o `587` con STARTTLS) | `465` |
| `EMAIL_USE_SSL` / `EMAIL_USE_TLS` | `true` / `false` (al revés con `587`) | `true` / `false` |
| `EMAIL_HOST_USER` | `no-responder@notificaciones.<TU_DOMINIO>` | vacío |
| `EMAIL_HOST_PASSWORD` | la contraseña del buzón (secreto) | vacío |
| `EMAIL_TIMEOUT` | `10` | `10` |
| `DEFAULT_FROM_EMAIL` | `no-responder@notificaciones.<TU_DOMINIO>` | `no-responder@localhost` |
| `EMAIL_SUPPORT_ADDRESS` | el buzón de soporte | `soporte@localhost` |
| `FRONTEND_BASE_URL` | la dirección pública de la web | `http://localhost:5173` |
| `EMAIL_NOTICE_RETRY_HOURS` | `24` | `24` |
| `EMAIL_ACCOUNT_EXISTS_WINDOW_MINUTES` | `60` | `60` |
| `EMAIL_CODE_SECRET` | uno propio (secreto), distinto de `REGISTRATION_CODE_SECRET` | `email-code:` + `DJANGO_SECRET_KEY` |

Para editar el archivo cifrado:
```bash
sops secrets/prod.enc.yaml
```
Para generar `EMAIL_CODE_SECRET`:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
`EMAIL_CODE_SECRET` no se rota: cambiarlo descarta los correos de código que esperan en la bandeja.

### Cambiar de proveedor
Con un proveedor transaccional (por SMTP) solo cambian `EMAIL_HOST`, `EMAIL_PORT`,
`EMAIL_USE_SSL`/`EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` y los registros SPF y
DKIM de `notificaciones` (cada proveedor da los suyos). El código no cambia.

## Cómo probarlo
Requisitos: Docker y `main` actualizado. En el VPS sigue *Actualizar* y *Migraciones* de la sección
*Entorno remoto* del README. Todos los comandos se ejecutan desde la raíz del repositorio. Sin
`EMAIL_BACKEND`, cada correo entregado aparece completo en la salida del worker.

1. Levanta la base de datos y Redis:
   ```bash
   docker compose -f docker/docker-compose.yml up -d db redis
   ```
   Aplica las migraciones:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
   ```
   Deberías ver, entre otras, `emails.0001_initial... OK`, `emails.0002_initial_templates... OK`,
   `emails.0003_support_permissions... OK` y `emails.0004_initial_template_history... OK`. Levanta el worker y el planificador:
   ```bash
   docker compose -f docker/docker-compose.yml up -d worker beat
   ```
2. Encola un correo de ejemplo de cada tipo que quieras ver. Por ejemplo, el del código de registro
   en portugués:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py emails test --kind registration_code --locale pt-BR --to prueba@example.com
   ```
   Deberías ver `queued: <ID> → prueba@example.com (registration_code, pt-BR)`. Cambia `--kind`
   por `password_reset_code`, `account_exists`, `password_reset_done`, `password_changed`,
   `account_disabled` o `sessions_closed`, y `--locale` por `es` o `en`, para ver los demás. Lee la
   salida del worker:
   ```bash
   docker compose -f docker/docker-compose.yml logs worker --tail 80
   ```
   Deberías ver el correo completo: asunto, cuerpo, el código `123456` de ejemplo, el enlace que
   termina en `#sample` y «O código vence em 15 minutos». Los avisos terminan con el bloque de
   reporte.
3. Provoca los correos reales de los procesos siguiendo el *Cómo probarlo* de
   `specs/procesos-pendientes/resumen.md` (código de registro y «ya tienes cuenta») y de
   `specs/cambio-contrasena/resumen.md` (código de cambio y «contraseña restablecida»).
4. Envía un aviso de seguridad a una cuenta existente, en el idioma guardado de la cuenta.
   `<CORREO_DE_LA_CUENTA>` es el correo de una cuenta que ya exista:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py emails notify --kind password_changed --email <CORREO_DE_LA_CUENTA>
   ```
   Deberías ver `queued: …` y el aviso en la salida del worker.
5. Ve un fallo temporal y su reintento con un proveedor que no responde. Para el worker normal:
   ```bash
   docker compose -f docker/docker-compose.yml stop worker
   ```
   Arranca en primer plano un worker que apunta a un SMTP inexistente (déjalo abierto en esta
   terminal):
   ```bash
   docker compose -f docker/docker-compose.yml run --rm -e EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend -e EMAIL_HOST=127.0.0.1 -e EMAIL_PORT=2 worker
   ```
   En otra terminal, encola un aviso:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py emails test --kind password_changed --locale es --to prueba@example.com
   ```
   Mira su estado en la bandeja:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.emails.models import OutboundEmail; print(list(OutboundEmail.objects.values_list('kind', 'status', 'attempts', 'next_attempt_at', 'last_error')))"
   ```
   Deberías ver el correo en `pending`, con `attempts` en 1 o más, el siguiente intento unos
   segundos más tarde y el error de conexión en `last_error`. Repite el comando al cabo de un
   minuto: `attempts` sube y la espera se dobla. Para el worker roto con `Ctrl+C` y arranca el
   normal:
   ```bash
   docker compose -f docker/docker-compose.yml up -d worker
   ```
   En menos de un minuto, el barrido lo vuelve a encolar y el aviso aparece en la salida del worker.
   El mismo comportamiento lo fijan los tests con el proveedor simulado:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend pytest -q apps/emails/tests/test_delivery.py -k "temporary or permanent or notice"
   ```
   Deberías ver todos esos tests en verde.
6. Edita una plantilla en el panel. Crea un superusuario si no tienes uno:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py createsuperuser
   ```
   Levanta el backend:
   ```bash
   docker compose -f docker/docker-compose.yml up -d backend
   ```
   Abre `http://localhost:8000/admin/`, entra en *Email templates* y edita una. Si escribes
   `{{ telefono }}` o un dominio ajeno como `evil.com/login`, el panel rechaza el cambio y nombra
   cada problema. Un cambio válido queda en *History* junto al texto inicial, y el siguiente
   `emails test` de ese tipo e idioma ya sale con el texto nuevo.
7. Ejecuta la suite completa con el worker parado (comparte el broker con los tests):
   ```bash
   docker compose -f docker/docker-compose.yml stop worker
   ```
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend pytest -q
   ```
   Deberías ver todos los tests en verde y `Required test coverage of 80% reached`.

### Límites conocidos
- **La detección de enlaces cubre los disfraces conocidos, no todos**: se probaron los que
  encontraron dos validaciones independientes (barra invertida, `＠`, dominios no latinos, `。`, IP
  sueltas, direcciones mal formadas). Un cliente de correo con reglas propias de autoenlace podría
  convertir en enlace un texto que la validación no reconoce.
- **Sin envío real probado**: en la sesión remota no hay salida SMTP; la entrega real con MXroute
  y el `PASS` de SPF, DKIM y DMARC se comprueban con los pasos 5 y 8b de `HUMAN_TODO.md`.
- **Los pasos con Docker de esta sección no se ejecutaron en la sesión remota** (Docker Hub
  respondió `429 Too Many Requests`); la suite sí pasó fuera de Docker.
- **Entrega al menos una vez**: si el worker se cae justo después de que el proveedor acepte el
  correo y antes de anotarlo, ese correo puede salir dos veces.
- **Límite por hora de MXroute**: no hay control de ritmo en la aplicación; un pico por encima del
  cupo se convierte en errores temporales y reintentos.
- `makemessages` no se ha ejecutado: los textos del panel y del comando están marcados para
  traducción, sin catálogos.

## Marco teórico
### SPF
Un registro TXT del dominio de envío que enumera qué servidores pueden enviar en su nombre
(`include:mxroute.com`). El servidor que recibe el correo comprueba que quien se lo entrega está en
la lista; `-all` pide rechazar al resto. Sin SPF, cualquiera puede enviar haciéndose pasar por el
dominio y los proveedores desconfían.

### DKIM
MXroute firma cada correo con una clave privada; la clave pública está en el DNS
(`x._domainkey.notificaciones`). Quien recibe verifica la firma: así sabe que el correo salió de un
servidor autorizado y que nadie cambió el contenido por el camino.

### DMARC
Une los dos anteriores: pide que SPF o DKIM pasen **y** coincidan con el dominio del remitente, y
dice qué hacer si no (`p=none` solo informar, `p=quarantine` a spam, `p=reject` rechazar). Los
informes que llegan a `rua` muestran quién envía en nombre del dominio; se endurece la política
cuando los informes salen limpios.

### Bandeja de salida (outbox)
Guardar el correo en la base de datos en la misma transacción que la operación garantiza que no
existe uno sin el otro: si la operación falla, no hay correo; si el correo no se puede enviar ahora,
sigue en la tabla y se reintenta. Celery solo recibe el número de la fila, y el barrido rescata lo
que la cola perdió.

### Máscara del código
El correo pendiente necesita el código en claro para enviarlo, pero guardarlo así lo dejaría a la
vista de quien lea la base de datos. La máscara le suma un valor derivado de un secreto
(`EMAIL_CODE_SECRET`) y de un número aleatorio propio de cada correo. Sin el secreto no se puede
deshacer; con él, el worker lo recupera justo antes de enviar.

### Entrega al menos una vez
Entre «el proveedor aceptó el correo» y «la bandeja lo anotó como entregado» siempre hay un
instante en que un fallo deja la duda. Ante la duda, el sistema reintenta: es preferible un correo
duplicado a uno perdido. Por eso un código reenviado o validado invalida los correos anteriores al
entregarlos.

### Enumeración por tiempo
Aunque dos respuestas digan lo mismo, si una tarda más porque escribe un correo y la otra no, el
tiempo delata qué correos tienen cuenta. Por eso todo lo que depende de la cuenta, incluido el
correo, se hace fuera de la respuesta.
