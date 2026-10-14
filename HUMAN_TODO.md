# HUMAN_TODO

Acciones que **requieren intervención humana** (credenciales, instalaciones locales,
binarios, decisiones de infraestructura). Los agentes no las pueden hacer por ti; las
anotan aquí para que no se pierdan. Marca `[x]` cuando completes cada una.

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
  8. **Guarda las credenciales SMTP cifradas.** Cuando el plan de la feature fije los nombres de
     las variables, añade el usuario y la contraseña del buzón al archivo cifrado:
     ```bash
     sops secrets/prod.enc.yaml
     ```
  9. **Migra a un proveedor transaccional** antes de que el volumen real se acerque al límite por
     hora de MXroute; solo cambiarán las variables de entorno.

- [ ] **Comprobar que el entorno Docker sigue levantando tras `huellas-hmac-unificadas`.** En la
  sesión remota no se pudo construir la imagen del backend (Docker Hub devolvió
  `429 Too Many Requests` y `pip` falló dentro de la construcción). La feature no cambia
  dependencias, `Dockerfile` ni `docker-compose.yml`, pero la regla del proyecto pide verificarlo.
  En tu máquina:
  ```bash
  docker compose -f docker/docker-compose.yml build backend
  ```
  ```bash
  docker compose -f docker/docker-compose.yml run --rm backend pytest -q
  ```
  Deberías ver la imagen construida y todos los tests en verde.

- [ ] **Borrar la rama remota `claude/keen-davinci-jyd1ec`.** Se renombró a
  `refactor/huellas-hmac-unificadas` (feature `huellas-hmac-unificadas`), pero el entorno remoto no
  tiene permiso para borrar ramas en GitHub (HTTP 403). Las dos apuntan al mismo commit, así que no
  se pierde nada. Desde tu máquina:
  ```bash
  git push origin --delete claude/keen-davinci-jyd1ec
  ```

- [ ] **Reconstruir la imagen del backend y migrar tras `usuario-personalizado`.** La feature
  `usuario-personalizado`, ya fusionada en `main`, añade dos dependencias (`pycountry` y `django-simple-history`)
  y las migraciones `0002`, `0003` y `0004` de `accounts`. En tu máquina:
  ```bash
  docker compose -f docker/docker-compose.yml build backend
  ```
  ```bash
  docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
  ```
  Si `0003` falla con "Emails that differ only in case", tienes cuentas locales cuyos correos
  solo difieren en mayúsculas: decide cuál conservar y borra o cambia la otra; la migración no
  fusiona cuentas a propósito (RF-011).
  En el VPS no uses estos comandos (se saltan el override y exponen Postgres y Redis): sigue
  *Actualizar* y *Migraciones* de la sección *Entorno remoto* del README.

- [ ] **Decidir los límites de peticiones (rate limiting) de allauth en `auth-headless`.**
  Hallazgo C-15 del spike `allauth-verificacion-codigo`: `ACCOUNT_RATE_LIMITS = {}` en
  `backend/config/settings.py` **no** desactiva los límites de allauth (solo `False` lo hace).
  Siguen activos, entre otros, 5 logins fallidos cada 5 min por correo y 20 registros por minuto
  e IP. Esto contradice S-09 de `specs/auth-headless/spec.md`, y ejecutar la suite más de 5 veces
  en 5 minutos hace fallar sus tests de login (`too_many_login_attempts`). Elige una opción:
  - **Mantener los límites** (recomendable para producción): corregir S-09 y el resumen de
    `auth-headless` para que digan la verdad, y aislar los tests de login de los contadores.
  - **Desactivarlos** como dice S-09: poner `ACCOUNT_RATE_LIMITS = False`.

  Siguiente paso, en ambos casos: `sdd-cambio` sobre `auth-headless` en una rama `fix/`.

- [ ] **Clave age para SOPS.** Genera tu par de claves y pon la pública en `.sops.yaml`.
  Ejecútalo fuera del repo, para que `age-key.txt` no quede dentro:
  ```bash
  age-keygen -o age-key.txt
  ```
  Copia la línea `age1...` (clave pública) al `age:` de `.sops.yaml` (reemplaza el placeholder).

- [ ] **Crear el primer secreto de producción cifrado** (cuando tengas valores reales):
  ```bash
  sops secrets/prod.enc.yaml
  ```

- [ ] **Definir `REGISTRATION_CODE_SECRET` en producción, cifrado con SOPS** (features
  `procesos-pendientes` y `cambio-contrasena`). Protege las huellas de los códigos de registro y
  de cambio de contraseña: sin él, cualquiera con la base de datos podría probar el millón de
  códigos posibles (RF-008) y, con un código de cambio de contraseña en curso, tomar la cuenta. Si
  no se define, se usa `DJANGO_SECRET_KEY`, lo que ata su rotación a la de las sesiones. Genera uno
  propio:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
  Añade el valor que imprime como `REGISTRATION_CODE_SECRET` en el archivo cifrado:
  ```bash
  sops secrets/prod.enc.yaml
  ```
  Para rotarlo sin invalidar los códigos en curso (RF-015): pasa el valor actual a
  `REGISTRATION_CODE_SECRET_PREVIOUS`, pon el nuevo en `REGISTRATION_CODE_SECRET` y la hora del
  cambio en `REGISTRATION_CODE_SECRET_ROTATED_AT` (ISO 8601 con zona, p. ej.
  `2026-10-06T10:00:00+00:00`). El anterior vale durante `REGISTRATION_SECRET_TRANSITION_MINUTES`
  (60 por defecto); después puedes borrar las dos variables de rotación.

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

- [ ] **Migrar y comprobar Docker tras `cambio-contrasena`.** La rama `feat/cambio-contrasena`
  añade la migración `0006_passwordresetrequest` de `accounts` (sin dependencias nuevas). En la
  sesión remota (2026-10-09) la imagen se construyó con una copia del `Dockerfile` que solo añade
  el certificado del proxy de la sesión durante `pip install`, porque ese proxy intercepta TLS. Con
  ella, `migrate` aplicó `0006`, backend, worker y beat arrancaron y la suite pasó dentro del
  contenedor (703 tests). Falta construirla con el `Dockerfile` real, sin proxy. En tu máquina:
  ```bash
  docker compose -f docker/docker-compose.yml build backend
  docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
  ```
  Deberías ver `accounts.0006_passwordresetrequest... OK`.

  Si ejecutas la suite dentro del contenedor, para antes el `worker` de Compose: comparte el broker
  Redis con los tests y se lleva la tarea de `apps/core/tests/test_task_worker.py`, que entonces
  falla (la escribe en la base de desarrollo, no en la de tests):
  ```bash
  docker compose -f docker/docker-compose.yml stop worker
  ```
  Después ejecuta la suite:
  ```bash
  docker compose -f docker/docker-compose.yml run --rm backend pytest -q
  ```
  Deberías ver todos los tests en verde.

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

- [ ] **Limitar la frecuencia del reenvío de códigos antes de publicar la API de registro**
  (feature `procesos-pendientes`, S-07). Cada reenvío reinicia los intentos, así que el tope de 5
  intentos es por código, no por proceso: sin límite de reenvíos, un atacante puede probar códigos
  sin parar durante la hora de vida del registro. En consola no hay riesgo; decide el límite (por
  correo y por IP) al especificar la feature de la API.

- [ ] **Limitar la frecuencia de pedir y reenviar códigos antes de publicar la API de cambio de
  contraseña** (feature `cambio-contrasena`, S-05). Aquí el riesgo es mayor que en el registro:
  cualquiera puede pedir el cambio para el correo de otra persona, y pedirlo de nuevo o reenviar
  el código pone los intentos a 0. Sin límite, unas 200.000 rondas de 5 intentos bastan de media
  para acertar un código y **tomar la cuenta ajena**. En consola no hay riesgo; decide el límite
  (por correo y por IP, para pedir y para reenviar) al especificar la API. Es bloqueante.

- [ ] **Neutralizar "sin cuenta elegible" en la API de cambio de contraseña** (feature
  `cambio-contrasena`, S-01, RF-004). El servicio `password_reset.start` responde
  `NoEligibleAccount` cuando el correo no tiene cuenta o la cuenta está inactiva. La API debe
  devolver exactamente el mismo mensaje que con una cuenta válida ("Si existe una cuenta,
  recibirás un código") y con un tiempo de respuesta comparable (con cuenta se escribe en la base
  de datos y se calcula la huella; sin cuenta, no), o revelará qué correos están registrados. Es
  bloqueante.

- [ ] **Traducir el `IntegrityError` de `complete` antes de publicar la API de registro**
  (feature `procesos-pendientes`, riesgo residual). Si otra vía crea la cuenta justo entre la
  comprobación y el alta, `registration.complete` lanza `IntegrityError`: en la API sería un
  error 500 y el registro pendiente se conservaría en vez de borrarse (RF-012). Debe devolver
  "cuenta existente" y borrar el registro.

- [ ] **Probar una vez el validador de contraseñas filtradas con red real** (feature
  `procesos-pendientes`, riesgo residual). En el entorno remoto no hay salida a
  `api.pwnedpasswords.com` y los tests lo simulan. En tu máquina, en `registration complete`
  prueba una contraseña filtrada conocida de 12+ caracteres (por ejemplo `password1234`): debe
  rechazarse con "appeared in a data breach". Si sale el aviso "Pwned Passwords check skipped",
  no hay salida al servicio.

- [ ] **Añadir `makemigrations --check` a la CI del backend.** Hallazgo M39 de la tercera validación
  de `usuario-personalizado`: si se quita una restricción del modelo sin crear la migración
  correspondiente, hoy ningún paso de la CI lo detecta hasta que alguien ejecuta `makemigrations`.
  Hay que añadir, en el job de backend de `.github/workflows/ci.yml`, tras `mypy`:
  `python manage.py makemigrations --check --dry-run`.
  Decide cuándo hacerlo: es un cambio de CI independiente, en una rama `chore/` propia (por ejemplo,
  `chore/ci-makemigrations-check`) y no dentro de `feat/usuario-personalizado`.

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->

- [x] **Integrar la feature `infra-persistencia-y-colas`** (2026-09-25). Fusionada en `main` con el
  PR #1. Quedan como **opcionales** las tareas T-009 y T-010 en
  `specs/infra-persistencia-y-colas/tasks.md` (mejoras de tests, no bloqueantes).

- [x] **Entorno remoto en el VPS: tareas de administración** (2026-09-30). Usuario propio con
  `sudo` y `docker` y clave pública instalada, SSH endurecido, swap creada, alta de trabajador
  completada y RAM y disco comprobados. Procedimiento en `README.md` → *Entorno remoto (VPS
  por SSH)*.

- [x] **Dominio con HTTPS para el panel de Coolify** (2026-09-30). Asignado en Settings →
  Instance Domain; las credenciales de administrador ya no viajan en claro.

- [x] **Acceso de escritura a GitHub para las sesiones web** (2026-09-28). GitHub reconectado;
  la rama `spike/allauth-verificacion-codigo` se subió correctamente.

- [x] **Lockfiles** (2026-09-23). `pnpm-lock.yaml` generado y commiteado (`0753a35`);
  `pnpm install --frozen-lockfile` pasa igual que en el CI. `requirements-dev.txt`
  presente (el backend instala en CI; no hay lockfile de Python que versionar).

- [x] **Iconos de Tauri** (2026-09-23). Generados con `tauri icon` a partir de un
  **placeholder temporal** (círculo azul con "C"); desbloquea el job Desktop del CI.
  **Pendiente de diseño real:** reemplazar por el logo definitivo y regenerar los iconos;
  `<LOGO_PATH>` es la ruta al archivo del logo:
  ```bash
  pnpm --filter desktop tauri icon <LOGO_PATH>
  ```

- [x] **Branch protection en GitHub** (2026-09-23). Regla sobre `main` con los checks
  `Backend`, `Frontend`, `Desktop`, `Secretos` como obligatorios.

- [x] **`.env` local del backend** (2026-09-23). Creado a partir de `.env.example`;
  gitignoreado (no se versiona).

- [x] **Prerrequisitos locales** (2026-09-24). Verificado todo en local: Podman 6.0.2
  (runtime de contenedores), Node 24, pnpm 9.12, Python 3.12.10 (`py -3.12`), Rust
  (rustup 1.29.1 / rustc 1.98.1) + Build Tools de C++.
