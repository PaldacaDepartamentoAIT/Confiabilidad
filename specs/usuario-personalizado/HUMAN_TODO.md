# HUMAN_TODO — usuario-personalizado

Acciones que **requieren intervención humana** para completar la feature `usuario-personalizado`
(credenciales, instalaciones locales, binarios, decisiones de infraestructura). Marca `[x]`
cuando completes cada una y muévela a *Hecho* con la fecha.

## Pendiente

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

- [ ] **Añadir `makemigrations --check` a la CI del backend.** Hallazgo M39 de la tercera validación
  de `usuario-personalizado`: si se quita una restricción del modelo sin crear la migración
  correspondiente, hoy ningún paso de la CI lo detecta hasta que alguien ejecuta `makemigrations`.
  Hay que añadir, en el job de backend de `.github/workflows/ci.yml`, tras `mypy`:
  `python manage.py makemigrations --check --dry-run`.
  Decide cuándo hacerlo: es un cambio de CI independiente, en una rama `chore/` propia (por ejemplo,
  `chore/ci-makemigrations-check`) y no dentro de `feat/usuario-personalizado`.

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->
