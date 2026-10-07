# HUMAN_TODO

Acciones que **requieren intervención humana** (credenciales, instalaciones locales,
binarios, decisiones de infraestructura). Los agentes no las pueden hacer por ti; las
anotan aquí para que no se pierdan. Marca `[x]` cuando completes cada una.

## Pendiente

- [ ] **Reconstruir la imagen del backend y migrar tras `usuario-personalizado`.** La rama
  `feat/usuario-personalizado` añade dos dependencias (`pycountry` y `django-simple-history`)
  y las migraciones `0002`, `0003` y `0004` de `accounts`. En tu máquina:
  ```bash
  docker compose -f docker/docker-compose.yml build backend
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

- [ ] **Integrar la feature `infra-persistencia-y-colas`.** Implementada y validada (CUMPLIDA)
  en la rama `feat/infra-persistencia-y-colas`. Súbela y abre el PR a `main` (la branch
  protection exige PR; el CI correrá Backend/Frontend/Desktop/Secretos):
  ```bash
  git push -u origin feat/infra-persistencia-y-colas
  gh pr create --base main --fill    # requiere `gh auth login` hecho; si no, abre el PR desde la web
  ```
  Quedan como **opcionales** las tareas T-009 y T-010 en
  `specs/infra-persistencia-y-colas/tasks.md` (mejoras de tests, no bloqueantes).

- [ ] **Clave age para SOPS.** Genera tu par de claves y pon la pública en `.sops.yaml`.
  ```bash
  age-keygen -o age-key.txt          # guarda age-key.txt FUERA del repo
  ```
  Copia la línea `age1...` (clave pública) al `age:` de `.sops.yaml` (reemplaza el placeholder).

- [ ] **Crear el primer secreto de producción cifrado** (cuando tengas valores reales):
  ```bash
  sops secrets/prod.enc.yaml
  ```

- [ ] **Definir `REGISTRATION_CODE_SECRET` en producción, cifrado con SOPS** (feature
  `procesos-pendientes`). Protege las huellas de los códigos de registro: sin él, cualquiera con
  la base de datos podría probar el millón de códigos posibles (RF-008). Si no se define, se usa
  `DJANGO_SECRET_KEY`, lo que ata su rotación a la de las sesiones. Genera uno propio y
  añádelo con `sops secrets/prod.enc.yaml`:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
  Para rotarlo sin invalidar los códigos en curso (RF-015): pasa el valor actual a
  `REGISTRATION_CODE_SECRET_PREVIOUS`, pon el nuevo en `REGISTRATION_CODE_SECRET` y la hora del
  cambio en `REGISTRATION_CODE_SECRET_ROTATED_AT` (ISO 8601 con zona, p. ej.
  `2026-10-06T10:00:00+00:00`). El anterior vale durante `REGISTRATION_SECRET_TRANSITION_MINUTES`
  (60 por defecto); después puedes borrar las dos variables de rotación.

- [ ] **Limitar la frecuencia del reenvío de códigos antes de publicar la API de registro**
  (feature `procesos-pendientes`, S-07). Cada reenvío reinicia los intentos, así que el tope de 5
  intentos es por código, no por proceso: sin límite de reenvíos, un atacante puede probar códigos
  sin parar durante la hora de vida del registro. En consola no hay riesgo; decide el límite (por
  correo y por IP) al especificar la feature de la API.

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
  **Pendiente de diseño real:** reemplazar por el logo definitivo y regenerar con
  `pnpm --filter desktop tauri icon ruta/a/logo.png`.

- [x] **Branch protection en GitHub** (2026-09-23). Regla sobre `main` con los checks
  `Backend`, `Frontend`, `Desktop`, `Secretos` como obligatorios.

- [x] **`.env` local del backend** (2026-09-23). Creado a partir de `.env.example`;
  gitignoreado (no se versiona).

- [x] **Prerrequisitos locales** (2026-09-24). Verificado todo en local: Podman 6.0.2
  (runtime de contenedores), Node 24, pnpm 9.12, Python 3.12.10 (`py -3.12`), Rust
  (rustup 1.29.1 / rustc 1.98.1) + Build Tools de C++.
