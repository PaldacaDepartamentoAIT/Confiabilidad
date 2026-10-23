# HUMAN_TODO — cambio-contrasena

Acciones que **requieren intervención humana** para completar la feature `cambio-contrasena`
(credenciales, instalaciones locales, binarios, decisiones de infraestructura). Marca `[x]`
cuando completes cada una y muévela a *Hecho* con la fecha.

`REGISTRATION_CODE_SECRET`, el secreto que protege las huellas de los códigos de cambio de
contraseña, se comparte con `procesos-pendientes` y su entrada está en
`specs/procesos-pendientes/HUMAN_TODO.md`.

## Pendiente

- [ ] **Migrar y comprobar Docker tras `cambio-contrasena`.** La rama `feat/cambio-contrasena`
  añade la migración `0006_passwordresetrequest` de `accounts` (sin dependencias nuevas). En la
  sesión remota (2026-10-09) la imagen se construyó con una copia del `Dockerfile` que solo añade
  el certificado del proxy de la sesión durante `pip install`, porque ese proxy intercepta TLS. Con
  ella, `migrate` aplicó `0006`, backend, worker y beat arrancaron y la suite pasó dentro del
  contenedor (703 tests). Falta construirla con el `Dockerfile` real, sin proxy. En tu máquina:
  ```bash
  docker compose -f docker/docker-compose.yml build backend
  ```
  ```bash
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

- [ ] **Limitar la frecuencia de pedir y reenviar códigos antes de publicar la API de cambio de
  contraseña** (feature `cambio-contrasena`, S-05). Aquí el riesgo es mayor que en el registro:
  cualquiera puede pedir el cambio para el correo de otra persona, y pedirlo de nuevo o reenviar
  el código pone los intentos a 0. Sin límite, unas 200.000 rondas de 5 intentos bastan de media
  para acertar un código y **tomar la cuenta ajena**. En consola no hay riesgo; decide el límite
  (por correo y por IP, para pedir y para reenviar) al especificar la API. Es bloqueante.
  El formulario de registro ya tiene el suyo (`registro-api`, RF-010 y RF-011: por correo e IP y
  por IP, en `apps/accounts/throttling.py`), que puede servir de modelo. Siguen sin límite el
  reenvío y la verificación del código, en el registro y en el cambio de contraseña, y pedir el
  cambio de contraseña.

- [ ] **Mensaje neutro en la API de cambio de contraseña** (feature `cambio-contrasena`, S-01,
  RF-004). El servicio ya responde lo mismo, con el mismo trabajo, tenga o no cuenta el correo
  (cambio del 2026-10-14). A la API solo le queda devolver siempre el mismo mensaje ("Si existe una
  cuenta, recibirás un código") y no añadir trabajo que dependa de la cuenta en la respuesta.

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->
