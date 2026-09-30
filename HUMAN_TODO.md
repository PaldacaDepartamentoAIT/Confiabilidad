# HUMAN_TODO

Acciones que **requieren intervención humana** (credenciales, instalaciones locales,
binarios, decisiones de infraestructura). Los agentes no las pueden hacer por ti; las
anotan aquí para que no se pierdan. Marca `[x]` cuando completes cada una.

## Pendiente

- [ ] **Entorno remoto en el VPS: tareas de administración.** Cómo hacerlo: `README.md` →
  *Entorno remoto (VPS por SSH)*.
  - [ ] Crear tu propio usuario (con `sudo` y `docker`) e instalar tu clave pública
        (*Administración del VPS*).
  - [ ] Endurecer SSH tras comprobar que tu clave funciona.
  - [ ] Crear la swap si `swapon --show` no muestra nada.
  - [ ] Seguir *Alta de un trabajador* con tu usuario. Mientras `chore/entorno-remoto-ssh` no
        esté fusionada en `main`, haz `git checkout chore/entorno-remoto-ssh` tras clonar.
  - [ ] Comprobar que la RAM y el disco del VPS alcanzan para las personas que trabajarán a la
        vez (`free -h`, `docker system df`).

- [ ] **Dominio con HTTPS para el panel de Coolify.** Hoy escucha en `0.0.0.0:8000` por HTTP y
  las credenciales de administrador viajan en claro. Asígnalo en Settings → Instance Domain.

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

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->

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
