# HUMAN_TODO — registro-api

Acciones que requieren intervención humana para completar la feature. Marca `[x]` cuando completes
cada una y muévela a *Hecho* con la fecha.

## Pendiente

- [ ] **Recorrer `resumen.md` en Docker.** En la sesión remota no se pudo construir la imagen del
  backend (Docker Hub respondió `429 Too Many Requests` al descargar `python:3.12-slim`). Los pasos
  se comprobaron con el mismo código ejecutado fuera del contenedor (`runserver` y el worker de
  Celery sobre el Postgres y el Redis de Docker) y dieron lo que el resumen dice. Falta repetirlos
  tal cual, con `docker compose`, desde tu máquina. Empieza por construir la imagen:
  ```bash
  docker compose -f docker/docker-compose.yml build backend
  ```
  Después sigue *Cómo probarlo* de `specs/registro-api/resumen.md`.

- [ ] **Límites de frecuencia pendientes.** Ver la entrada «Limitar la frecuencia de pedir y
  reenviar códigos…» de `specs/cambio-contrasena/HUMAN_TODO.md`: el formulario de registro ya tiene
  su límite, pero el reenvío y la verificación del código no.

- [ ] **Decidir si las cuentas creadas por consola o por el panel deben guardar el correo en forma
  canónica.** La API ya convierte las variantes del mismo buzón (`ana@ｅxample.com`,
  `"ana"@example.com`) a `ana@example.com` (D-15 de `registro-api`), pero `createsuperuser`, el
  panel y otros caminos guardan el correo tal cual. Por ahí aún podría existir una segunda cuenta
  para el mismo buzón. Es de la feature `usuario-personalizado`; decide si se especifica allí.

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->
