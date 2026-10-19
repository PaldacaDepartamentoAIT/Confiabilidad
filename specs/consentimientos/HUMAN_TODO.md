# HUMAN_TODO — consentimientos

Acciones que **requieren intervención humana** para completar la feature `consentimientos`
(credenciales, instalaciones locales, binarios, decisiones de infraestructura). Marca `[x]`
cuando completes cada una y muévela a *Hecho* con la fecha.

## Pendiente

- [ ] **Migrar y comprobar Docker tras `consentimientos`.** La feature `consentimientos`, ya fusionada en
  `main`, añade la
  app `consents` y sus migraciones `0001`, `0002` y `0003` (sin dependencias nuevas). En la sesión remota no
  se pudo construir la imagen: Docker Hub respondió `429 Too Many Requests` al descargar
  `python:3.12-slim`. En tu máquina:
  Si aplicaste antes una versión intermedia de la rama anterior a `0003`, ejecuta primero:
  ```bash
  docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate consents zero
  ```
  Reconstruye la imagen:
  ```bash
  docker compose -f docker/docker-compose.yml build backend
  ```
  Aplica las migraciones:
  ```bash
  docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
  ```
  Deberías ver `consents.0001_initial... OK`, `consents.0002_support_group... OK` y
  `consents.0003_history_without_user... OK`.

- [ ] **Definir `CONSENT_EMAIL_HASH_SECRET` en producción, cifrado con SOPS, y no rotarlo nunca**
  (feature `consentimientos`). Protege la huella del correo de las aceptaciones de términos y los
  consentimientos de marketing: sin él, cualquiera con la base de datos podría averiguar el correo
  probando listas de correos (RF-012). Si no se define, se usa `DJANGO_SECRET_KEY`, y el día que
  esa clave rote todas las huellas antiguas dejarán de coincidir con el correo: se pierde la prueba
  de consentimiento de las cuentas borradas (S-09, D-06). Genera uno propio:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
  Añádelo al archivo cifrado **antes del primer consentimiento en producción**, guárdalo aparte y
  no lo cambies después:
  ```bash
  sops secrets/prod.enc.yaml
  ```

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->
