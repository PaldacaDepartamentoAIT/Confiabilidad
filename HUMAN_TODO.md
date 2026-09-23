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

- [ ] **Iconos de Tauri.** Faltan los binarios en `desktop/src-tauri/icons/`. Genéralos una vez:
  ```bash
  pnpm --filter desktop tauri icon ruta/a/tu-icono.png
  ```

- [ ] **Lockfiles.** Instala dependencias una vez para fijar versiones reproducibles:
  ```bash
  pnpm install                                   # crea pnpm-lock.yaml
  cd backend && pip install -r requirements-dev.txt
  ```

- [ ] **`.env` local del backend.** Copia la plantilla y ajusta valores de dev:
  ```bash
  cp backend/.env.example backend/.env
  ```

- [ ] **Prerrequisitos locales** (si aún no los tienes): Docker + Compose, Node ≥ 20,
  pnpm ≥ 9, Python 3.12, Rust estable + dependencias de sistema de Tauri.

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->
