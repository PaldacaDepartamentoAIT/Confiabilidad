# HUMAN_TODO — huellas-hmac-unificadas

Acciones que **requieren intervención humana** para completar la feature `huellas-hmac-unificadas`
(credenciales, instalaciones locales, binarios, decisiones de infraestructura). Marca `[x]`
cuando completes cada una y muévela a *Hecho* con la fecha.

## Pendiente

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

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->
