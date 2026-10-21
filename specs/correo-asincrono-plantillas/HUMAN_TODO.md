# HUMAN_TODO — correo-asincrono-plantillas

Acciones que **requieren intervención humana** para completar la feature `correo-asincrono-plantillas`
(credenciales, instalaciones locales, binarios, decisiones de infraestructura). Marca `[x]`
cuando completes cada una y muévela a *Hecho* con la fecha.

## Pendiente

- [ ] **Preparar el envío de correo con MXroute y Cloudflare** (feature `correo-asincrono-plantillas`).
  MXroute es el proveedor inicial; más adelante se podrá cambiar por uno transaccional sin tocar
  código. Se envía desde un subdominio propio para que la reputación y el cupo de la aplicación no
  se mezclen con tu correo de trabajo. En todos los pasos, `<TU_DOMINIO>` es tu dominio en
  Cloudflare (por ejemplo, `empresa.com`), y `<SERVIDOR_MXROUTE>` y `<SERVIDOR_MXROUTE_RELAY>` son
  los dos servidores MX (prioridad 10 y 20) que aparecen en el correo de bienvenida de MXroute.
  1. **Subdominio y buzón en MXroute.** En el panel de MXroute, añade el dominio
     `notificaciones.<TU_DOMINIO>` y crea el buzón `no-responder@notificaciones.<TU_DOMINIO>` con
     una contraseña larga y única. Si el panel no admite subdominios, avísame antes de seguir.
  2. **Copia la clave DKIM.** En el panel de MXroute, en la sección DNS o DKIM de
     `notificaciones.<TU_DOMINIO>`, copia el nombre del registro (normalmente `x._domainkey`) y su
     valor (empieza por `v=DKIM1; k=rsa; p=`).
  3. **Registros en Cloudflare.** En Cloudflare, abre la zona de `<TU_DOMINIO>`, ve a *DNS →
     Records → Add record* y crea estos registros. En la columna *Name* se escribe solo la parte
     anterior a `<TU_DOMINIO>`, porque Cloudflare la añade sola:

     | Tipo | Name | Contenido | Prioridad |
     |---|---|---|---|
     | MX | `notificaciones` | `<SERVIDOR_MXROUTE>` | 10 |
     | MX | `notificaciones` | `<SERVIDOR_MXROUTE_RELAY>` | 20 |
     | TXT | `notificaciones` | `v=spf1 include:mxroute.com -all` | — |
     | TXT | `x._domainkey.notificaciones` | el valor DKIM copiado en el paso 2 | — |
     | TXT | `_dmarc.notificaciones` | `v=DMARC1; p=none; rua=mailto:<CORREO_INFORMES>` | — |

     `<CORREO_INFORMES>` es un buzón tuyo donde quieras recibir los informes DMARC. Los MX hacen
     falta para que los rebotes lleguen al buzón remitente. No toques los registros de
     `<TU_DOMINIO>` raíz: el subdominio tiene los suyos. Cada nombre admite **un solo** registro
     SPF. Si creas además un CNAME (por ejemplo, `mail`), déjalo en *DNS only* (nube gris), nunca
     con proxy.
  4. **Comprueba que los registros se ven desde fuera.** Pueden tardar de minutos a 48 horas.
     Funciona en Linux, macOS y Windows:
     ```bash
     nslookup -type=MX notificaciones.<TU_DOMINIO>
     ```
     ```bash
     nslookup -type=TXT notificaciones.<TU_DOMINIO>
     ```
     ```bash
     nslookup -type=TXT x._domainkey.notificaciones.<TU_DOMINIO>
     ```
     ```bash
     nslookup -type=TXT _dmarc.notificaciones.<TU_DOMINIO>
     ```
     Deberías ver los dos servidores MX, el texto `v=spf1 include:mxroute.com -all`, la clave
     `v=DKIM1…` y el texto `v=DMARC1…`.
  5. **Prueba de entrega real.** Desde el webmail de MXroute, envía un correo desde
     `no-responder@notificaciones.<TU_DOMINIO>` a una cuenta de Gmail. En Gmail, abre el correo,
     menú ⋮ → *Mostrar original*. Deberías ver `SPF: PASS`, `DKIM: PASS` y `DMARC: PASS`.
  6. **Endurece DMARC.** Tras 2–4 semanas de informes sin fallos, cambia el contenido del registro
     `_dmarc.notificaciones` a `v=DMARC1; p=quarantine; rua=mailto:<CORREO_INFORMES>`, y más
     adelante a `p=reject`.
  7. **Confirma la política con MXroute.** Pregunta a su soporte si permiten correo transaccional
     automático de una aplicación (códigos y avisos de seguridad) y cuál es hoy el límite de
     envío por hora (su documentación indica 400 por dirección).
  8. **Guarda la configuración SMTP en producción, con las credenciales cifradas.** Abre el
     archivo cifrado:
     ```bash
     sops secrets/prod.enc.yaml
     ```
     Añade estas variables (las dos últimas son secretas y solo deben vivir ahí):
     `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST=<SERVIDOR_MXROUTE>`,
     `EMAIL_PORT=465`, `EMAIL_USE_SSL=true`, `EMAIL_USE_TLS=false`,
     `DEFAULT_FROM_EMAIL=no-responder@notificaciones.<TU_DOMINIO>`,
     `EMAIL_SUPPORT_ADDRESS=<CORREO_DE_SOPORTE>`, `FRONTEND_BASE_URL=<URL_DEL_FRONTEND>`,
     `EMAIL_HOST_USER=no-responder@notificaciones.<TU_DOMINIO>` y
     `EMAIL_HOST_PASSWORD=<CONTRASEÑA_DEL_BUZÓN>`. `<CORREO_DE_SOPORTE>` es el buzón donde quieres
     recibir los reportes de «no fui yo», y `<URL_DEL_FRONTEND>` la dirección pública de la web
     (por ejemplo, `https://app.<TU_DOMINIO>`). Si prefieres STARTTLS, usa `EMAIL_PORT=587`,
     `EMAIL_USE_SSL=false` y `EMAIL_USE_TLS=true`.
  8b. **Envía un correo real de prueba** cuando el backend, el worker y el beat estén desplegados
     con esa configuración. Dentro del contenedor del backend:
     ```bash
     python manage.py emails test --kind password_changed --locale es --to <TU_CORREO>
     ```
     Deberías ver `queued: <ID> → <TU_CORREO>` y, en un minuto como mucho, el correo en tu bandeja
     con `SPF: PASS`, `DKIM: PASS` y `DMARC: PASS` en *Mostrar original*. Si no llega, el panel de
     administración muestra el error en *Failed emails*.
  9. **Migra a un proveedor transaccional** antes de que el volumen real se acerque al límite por
     hora de MXroute; solo cambiarán las variables de entorno.

- [ ] **Definir `EMAIL_CODE_SECRET` en producción, cifrado con SOPS, y no rotarlo** (features
  `huellas-hmac-unificadas` y `correo-asincrono-plantillas`). Oculta el código de los correos que
  esperan en la bandeja. Sin definir vale `email-code:` + `DJANGO_SECRET_KEY`, así que rotar esa
  clave descartaría los correos de código pendientes. Genera uno propio:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
  Añade el valor que imprime como `EMAIL_CODE_SECRET` en el archivo cifrado; debe ser distinto de
  `REGISTRATION_CODE_SECRET`:
  ```bash
  sops secrets/prod.enc.yaml
  ```

- [ ] **Migrar y comprobar Docker tras `correo-asincrono-plantillas`.** La rama añade la app
  `emails` (migraciones `0001`, `0002`, `0003` y `0004`) y la migración `0007_language` de `accounts`, sin
  dependencias nuevas. En tu máquina:
  ```bash
  docker compose -f docker/docker-compose.yml build backend
  ```
  ```bash
  docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
  ```
  Deberías ver `emails.0001_initial... OK`, `emails.0002_initial_templates... OK`,
  `emails.0003_support_permissions... OK`, `emails.0004_initial_template_history... OK` y
  `accounts.0007_language... OK`. Reinicia después el
  `worker` y el `beat` para que carguen la tarea de entrega y el barrido de cada 30 segundos.

## Hecho
