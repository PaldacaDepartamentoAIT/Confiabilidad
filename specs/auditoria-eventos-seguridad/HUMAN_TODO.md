# HUMAN_TODO — auditoria-eventos-seguridad

Acciones que **requieren intervención humana** para completar la feature `auditoria-eventos-seguridad`
(credenciales, instalaciones locales, binarios, decisiones de infraestructura). Marca `[x]`
cuando completes cada una y muévela a *Hecho* con la fecha.

## Pendiente

- [ ] **Definir `AUDIT_HASH_SECRET` en producción, cifrado con SOPS, y no rotarlo nunca** (feature
  `auditoria-eventos-seguridad`). Calcula las huellas HMAC del correo y de la clave de sesión de los
  eventos de seguridad. Usa una clave propia, distinta de `CONSENT_EMAIL_HASH_SECRET`, para que una
  filtración de una tabla no permita correlacionar la otra. Si no se define, la aplicación no debe
  arrancar. Genera la clave:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
  Añade el valor que imprime como `AUDIT_HASH_SECRET` en el archivo cifrado:
  ```bash
  sops secrets/prod.enc.yaml
  ```

- [ ] **Configurar `TRUSTED_PROXY_IPS` con la IP del proxy de entrada** (feature
  `auditoria-eventos-seguridad`). Sin esta variable la aplicación no confía en ningún proxy y registra
  la IP del proxy en lugar de la del cliente. Obtén la IP del contenedor de entrada en la red de Docker
  y ponla en el entorno de despliegue (separada por comas si hay varias):
  ```bash
  docker network inspect confiabilidad_default
  ```
  Deberías ver la IP del contenedor del proxy en la sección `Containers`, en el campo `IPv4Address`. Si la red tiene otro nombre, lista las redes con `docker network ls`.

- [ ] **Añadir `AUDIT_HASH_SECRET` a tu `.env` local** (feature `auditoria-eventos-seguridad`).
  Con `DJANGO_DEBUG` activo (como en Docker Compose), si falta se usa el valor de desarrollo
  `dev-audit-secret-change-me`; sin `DEBUG`, `manage.py runserver` y `manage.py check` fallan con
  `audit.E001`. Para no depender de ese valor por defecto, copia el de `backend/.env.example` (o genera
  uno propio) en tu `backend/.env`:
  ```bash
  grep -n "AUDIT_HASH_SECRET" backend/.env.example
  ```
  Deberías ver la línea `AUDIT_HASH_SECRET=dev-audit-secret-change-me`. Cópiala a tu `backend/.env`.

- [ ] **Aplicar las migraciones de auditoría en tu base de desarrollo** (feature
  `auditoria-eventos-seguridad`). Sin ellas, `manage.py purge_security_events` falla con
  `relation "audit_securityevent" does not exist`. Con `AUDIT_HASH_SECRET` ya en tu `backend/.env`,
  ejecuta desde la raíz del repositorio:
  ```bash
  cd backend && python manage.py migrate
  ```
  Deberías ver `Applying audit.0001_initial... OK` y `Applying audit.0002_securityevent_base_manager... OK`.

- [ ] **Comprobar que el entorno Docker sigue levantando tras `auditoria-eventos-seguridad`.** En la
  sesión remota no se pudo construir la imagen del backend (Docker Hub devolvió
  `429 Too Many Requests` al descargar `python:3.12-slim`). La feature no cambia dependencias,
  `Dockerfile` ni `docker-compose.yml`, pero la regla del proyecto pide verificarlo. En tu máquina:
  ```bash
  docker compose -f docker/docker-compose.yml build backend
  ```
  ```bash
  docker compose -f docker/docker-compose.yml run --rm backend pytest -q
  ```
  Deberías ver la imagen construida y todos los tests en verde.

- [ ] **Fusionar `feat/auditoria-eventos-seguridad` con tu autoría** (decisión del 2026-10-14). Los
  commits de la rama tienen como autor `Claude <noreply@anthropic.com>`, que viene de la configuración
  git del entorno remoto, y P-10 prohíbe acreditar a una IA. Al fusionar el PR, usa «Squash and merge»
  desde tu cuenta para que el commit resultante quede a tu nombre. `main` ya tiene commits anteriores
  con ese autor: corregirlos exige reescribir la rama principal y es una decisión aparte.
  **Estado (2026-10-15):** el PR #14 se fusionó con un commit de fusión (`42cd8d1`), no con
  «Squash and merge», así que los commits de la rama llegaron a `main` con ese autor. Corregirlo ya
  exige reescribir `main`: queda dentro de la decisión aparte del párrafo anterior.

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->
