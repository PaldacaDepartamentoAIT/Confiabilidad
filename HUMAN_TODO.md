# HUMAN_TODO

Acciones que **requieren intervención humana** (credenciales, instalaciones locales,
binarios, decisiones de infraestructura). Los agentes no las pueden hacer por ti; las
anotan aquí para que no se pierdan. Marca `[x]` cuando completes cada una.

## Pendiente

- [ ] **Clave age para SOPS.** Genera tu par de claves y pon la pública en `.sops.yaml`.
  ```bash
  age-keygen -o age-key.txt          # guarda age-key.txt FUERA del repo
  ```
  Copia la línea `age1...` (clave pública) al `age:` de `.sops.yaml` (reemplaza el placeholder).

- [ ] **Crear el primer secreto de producción cifrado** (cuando tengas valores reales):
  ```bash
  sops secrets/prod.enc.yaml
  ```

- [ ] **Branch protection en GitHub.** Para que el CI **bloquee** merges con checks en rojo:
  Settings → Branches → Add rule sobre `main` → "Require status checks to pass"
  y marca los jobs `Backend`, `Frontend`, `Desktop`, `Secretos`.

- [ ] **`.env` local del backend.** Copia la plantilla y ajusta valores de dev:
  ```bash
  cp backend/.env.example backend/.env
  ```

- [ ] **Prerrequisitos locales** (si aún no los tienes): Docker + Compose, Node ≥ 20,
  pnpm ≥ 9, Python 3.12, Rust estable + dependencias de sistema de Tauri.

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->

- [x] **Lockfiles** (2026-09-23). `pnpm-lock.yaml` generado y commiteado (`0753a35`);
  `pnpm install --frozen-lockfile` pasa igual que en el CI. `requirements-dev.txt`
  presente (el backend instala en CI; no hay lockfile de Python que versionar).

- [x] **Iconos de Tauri** (2026-09-23). Generados con `tauri icon` a partir de un
  **placeholder temporal** (círculo azul con "C"); desbloquea el job Desktop del CI.
  **Pendiente de diseño real:** reemplazar por el logo definitivo y regenerar con
  `pnpm --filter desktop tauri icon ruta/a/logo.png`.
