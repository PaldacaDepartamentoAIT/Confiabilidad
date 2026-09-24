# HUMAN_TODO

Acciones que **requieren intervención humana** (credenciales, instalaciones locales,
binarios, decisiones de infraestructura). Los agentes no las pueden hacer por ti; las
anotan aquí para que no se pierdan. Marca `[x]` cuando completes cada una.

## Pendiente

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
