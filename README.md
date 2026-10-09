# Confiabilidad

Herramienta web y de escritorio para la gestión de activos en instalaciones
industriales, basada en la filosofía de Confiabilidad Operacional.

## Stack
- **backend/** — Django + Django REST Framework, Channels (WebSocket), Celery + Redis.
- **frontend/** — React + TypeScript (Vite). Única app de UI.
- **desktop/** — Tauri (Rust); envuelve `frontend/` sin duplicar React.
- **docker/** — orquestación con Docker Compose para desarrollo.
- **secrets/** — secretos de producción cifrados con SOPS + age.
- **specs/** — artefactos del flujo SDD (ver `AGENTS.md`).

## Requisitos
- Docker + Docker Compose
- Node ≥ 20 y pnpm ≥ 9 (para trabajo local sin Docker)
- Python 3.12 (backend local)
- Rust estable + toolchain de Tauri (para el cliente de escritorio)

## Arranque rápido (Docker)
Desde la raíz del repositorio. Crea las variables de entorno de desarrollo del backend:
```bash
cp backend/.env.example backend/.env
```
Levanta backend + frontend + Redis + Postgres + Celery:
```bash
docker compose -f docker/docker-compose.yml up --build
```
- API:      http://localhost:8000/api/health/
- Frontend: http://localhost:5173

## Trabajo local sin Docker
**Frontend y desktop**, desde la raíz. Instala las dependencias:
```bash
pnpm install
```
Arranca el frontend:
```bash
pnpm --filter frontend dev
```
Arranca el cliente de escritorio:
```bash
pnpm --filter desktop tauri dev
```

**Backend.** Entra en `backend`:
```bash
cd backend
```
Crea el entorno virtual y actívalo (Git Bash):
```bash
python -m venv .venv && . .venv/Scripts/activate
```
En PowerShell, la activación es:
```powershell
.venv\Scripts\Activate.ps1
```
Instala las dependencias, aplica las migraciones y arranca el servidor, un comando cada vez:
```bash
pip install -r requirements-dev.txt
```
```bash
python manage.py migrate
```
```bash
python manage.py runserver
```

## Entorno remoto (VPS por SSH)
Desarrollo con VS Code Remote-SSH sobre el VPS que también aloja Coolify. Cada trabajador
tiene su propio usuario, su clon del repo y su stack con puertos propios, así que varias
personas pueden trabajar a la vez. Todo queda atado a `127.0.0.1` y se accede por túnel SSH.

> **Seguridad (riesgo aceptado por el responsable del proyecto):** pertenecer al grupo `docker`
> equivale a ser root en el VPS. Cualquier trabajador puede leer las variables de entorno de lo
> que despliegue Coolify (`docker inspect`), pararlo, o conectarse por `127.0.0.1` a los stacks
> de sus compañeros. Solo se da acceso a personas de confianza.

Cada stack simultáneo consume RAM y disco propios; vigila `free -h` y `docker system df`.

### Administración del VPS (quien tiene root)
**Alta de un trabajador** (la clave pública te la envía él). En los comandos, `<NOMBRE>` es su
usuario, en minúsculas, y `<CLAVE_PUBLICA>` la clave pública que te envió.
Crea el usuario:
```bash
adduser <NOMBRE>
```
Añádelo al grupo `docker` (añade también `sudo` solo si va a administrar el VPS):
```bash
usermod -aG docker <NOMBRE>
```
Instala su clave pública, un comando cada vez:
```bash
install -d -m 700 -o <NOMBRE> -g <NOMBRE> /home/<NOMBRE>/.ssh
```
```bash
echo "<CLAVE_PUBLICA>" >> /home/<NOMBRE>/.ssh/authorized_keys
```
```bash
chown <NOMBRE>:<NOMBRE> /home/<NOMBRE>/.ssh/authorized_keys
```
```bash
chmod 600 /home/<NOMBRE>/.ssh/authorized_keys
```

**Baja de un trabajador** (`<NOMBRE>` es su usuario). Para su stack y borra su BD:
```bash
docker compose -p confiabilidad-<NOMBRE> down -v
```
Borra el usuario y su carpeta:
```bash
deluser --remove-home <NOMBRE>
```

**Endurecer SSH** (una sola vez, después de comprobar que tu propia clave funciona y con otra
sesión SSH abierta por si algo falla): en `/etc/ssh/sshd_config` pon `PasswordAuthentication no`
y `PermitRootLogin no`, y reinicia el servicio:
```bash
sudo systemctl restart ssh
```

**Swap** (una sola vez). Coolify, los servidores de VS Code y los stacks compiten por la RAM;
sin swap, el kernel mata procesos al compilar o instalar dependencias. Comprueba si ya hay:
```bash
swapon --show
```
Si no muestra nada, créala, un comando cada vez:
```bash
sudo fallocate -l 4G /swapfile
```
```bash
sudo chmod 600 /swapfile
```
```bash
sudo mkswap /swapfile
```
```bash
sudo swapon /swapfile
```
```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
Si `free -h` muestra la swap en uso de forma constante, al VPS le falta RAM: la swap evita
caídas, no sustituye a la memoria.

### Alta de un trabajador (cada persona)
1. En Windows (PowerShell), crea tu clave y envía al administrador la **pública**
   (`$env:USERPROFILE\.ssh\id_ed25519.pub`); la privada no sale de tu PC:
   ```powershell
   ssh-keygen -t ed25519 -C "confiabilidad-vps"
   ```
2. Cuando el administrador te dé de alta, añade el alias en `C:\Users\TU_USUARIO\.ssh\config`
   y comprueba que `ssh confiabilidad-vps` entra sin contraseña:
   ```
   Host confiabilidad-vps
       HostName IP_DEL_VPS
       User TU_USUARIO_EN_EL_VPS
       IdentityFile ~/.ssh/id_ed25519
   ```
3. VS Code: instala la extensión **Remote - SSH** → `F1` → *Connect to Host* → `confiabilidad-vps`.
4. En el VPS (terminal de VS Code), crea una clave propia y añádela en GitHub → Settings →
   SSH and GPG keys:
   ```bash
   ssh-keygen -t ed25519 -C "confiabilidad-vps-github"
   ```
   Muestra la clave pública para copiarla:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
5. Clona y prepara el repo, un comando cada vez (`<TU_NOMBRE>` y `<TU_CORREO>` son los tuyos):
   ```bash
   git clone git@github.com:PaldacaDepartamentoAIT/Confiabilidad.git ~/Confiabilidad
   ```
   ```bash
   cd ~/Confiabilidad
   ```
   ```bash
   git config user.name "<TU_NOMBRE>" && git config user.email "<TU_CORREO>"
   ```
   ```bash
   cp backend/.env.example backend/.env
   ```
6. Añade el bloque siguiente al final de `~/.bashrc`. Es un archivo del VPS, no de Windows:
   `~` es tu carpeta personal (`/home/TU_USUARIO`) y, como empieza por punto, está oculto
   (`ls -a ~` lo muestra). Ábrelo con `code ~/.bashrc` o `nano ~/.bashrc` (en nano: `Ctrl+O`,
   Enter y `Ctrl+X`); si no existe, se crea al guardar.
   ```bash
   # Entorno remoto de Confiabilidad: proyecto y puertos propios, derivados del UID
   export COMPOSE_FILE=docker/docker-compose.yml:docker/docker-compose.remote.yml
   export COMPOSE_PROJECT_NAME="confiabilidad-$USER"
   export FRONTEND_PORT=$(( $(id -u) - 1000 + 5173 ))
   export BACKEND_PORT=$(( $(id -u) - 1000 + 8001 ))
   export DB_PORT=$(( $(id -u) - 1000 + 5432 ))
   export REDIS_PORT=$(( $(id -u) - 1000 + 6379 ))
   ```
   Las terminales abiertas antes de editarlo no lo cargan: abre una nueva o ejecuta:
   ```bash
   source ~/.bashrc
   ```
   Comprueba la configuración:
   ```bash
   echo $COMPOSE_FILE
   ```
   Debe imprimir `docker/docker-compose.yml:docker/docker-compose.remote.yml`.
   ```bash
   echo $FRONTEND_PORT $BACKEND_PORT
   ```
   Debe mostrar tus puertos.
   ```bash
   docker compose config | grep host_ip
   ```
   Todas las líneas deben decir `127.0.0.1`.
7. Primer arranque, migraciones y superusuario para el admin (ver *Uso diario*).
8. Desde tu PC (PowerShell), no desde el VPS, verifica que tus puertos **no** responden desde
   fuera. `<IP_DEL_VPS>` es la IP del VPS y `<TU_BACKEND_PORT>` y `<TU_DB_PORT>` tus puertos:
   ```powershell
   Test-NetConnection <IP_DEL_VPS> -Port <TU_BACKEND_PORT>
   ```
   ```powershell
   Test-NetConnection <IP_DEL_VPS> -Port <TU_DB_PORT>
   ```
   Ambos deben dar `TcpTestSucceeded : False`. Si da `True`, para tu stack y avisa al
   administrador.

### Uso diario
Todo desde `~/Confiabilidad`. Gracias a `COMPOSE_FILE`, `docker compose` usa siempre los dos
archivos; si falta el bloque de `~/.bashrc`, falla con `no configuration file provided` en vez
de exponer nada.

**Arrancar**
```bash
docker compose up -d --build
```
Sigue los logs:
```bash
docker compose logs -f backend frontend
```

**Puertos.** Cada persona tiene los suyos (los muestra `echo $FRONTEND_PORT $BACKEND_PORT`): el primer
usuario (UID 1000) usa 5173 / 8001 / 5432 / 6379, el siguiente 5174 / 8002 / 5433 / 6380, y así
sucesivamente. El backend nunca usa el 8000, que es de Coolify.

| Servicio | En tu PC (por el túnel) |
|---|---|
| Frontend (Vite, recarga en caliente) | `http://localhost:TU_FRONTEND_PORT` |
| Backend (Django) | `http://localhost:TU_BACKEND_PORT/api/health/` · `/admin/` |

Reenvía tus puertos a mano en la pestaña **Ports** de VS Code (`F1` → *Forward a Port*);
puede detectar también los de tus compañeros: ignóralos. Sin VS Code, abre el túnel desde
PowerShell y déjalo abierto mientras trabajas (`<TU_FRONTEND_PORT>` y `<TU_BACKEND_PORT>` son tus
puertos):
```powershell
ssh -N -L <TU_FRONTEND_PORT>:localhost:<TU_FRONTEND_PORT> -L <TU_BACKEND_PORT>:localhost:<TU_BACKEND_PORT> confiabilidad-vps
```
`DB_PORT` y `REDIS_PORT` se pueden reenviar si usas un cliente de BD.

**Parar** conservando tu BD:
```bash
docker compose down
```
Parar y borrar tu BD de desarrollo:
```bash
docker compose down -v
```

**Actualizar**
```bash
git pull
```
Si cambió `requirements*.txt` o `backend/Dockerfile`:
```bash
docker compose up -d --build
```
Si cambió `pnpm-lock.yaml` (reinstala al arrancar):
```bash
docker compose restart frontend
```
Si cambiaron tareas de Celery (no recargan solas):
```bash
docker compose restart worker beat
```
El resto de cambios de código no requiere reconstruir: el código está montado en los contenedores.

**Migraciones y tests.** Aplica las migraciones:
```bash
docker compose exec backend python manage.py migrate
```
Crea un superusuario para entrar en `/admin/`:
```bash
docker compose exec backend python manage.py createsuperuser
```
Genera migraciones nuevas:
```bash
docker compose exec backend python manage.py makemigrations
```
Ejecuta los tests:
```bash
docker compose exec backend pytest
```
Los contenedores escriben como root; devuelve la propiedad de los archivos a tu usuario:
```bash
docker compose exec frontend chown -R "$(id -u):$(id -g)" /workspace
```

### Problemas frecuentes
- `no configuration file provided: not found`: `COMPOSE_FILE` no está cargada en esa terminal.
  Compruébalo:
  ```bash
  echo $COMPOSE_FILE
  ```
  Si sale vacío, cárgala:
  ```bash
  source ~/.bashrc
  ```
  Si sigue vacío, revisa que el bloque se guardó y que lo editaste con tu usuario y no como
  root:
  ```bash
  tail -n 10 ~/.bashrc
  ```
  ```bash
  whoami
  ```
- `stat .../docker-compose.remote.yml: no such file or directory`: tu copia del repo no tiene
  ese archivo. Actualízala:
  ```bash
  git pull
  ```
- `port is already allocated`: otro stack ocupa ese puerto. Comprueba que tus variables están
  cargadas y que no tienes otro proyecto tuyo levantado:
  ```bash
  echo $BACKEND_PORT
  ```
  ```bash
  docker compose ls
  ```

### Comandos prohibidos
El VPS comparte Docker con Coolify y con tus compañeros. No ejecutes:
- `docker compose` con `-f`, o desde dentro de `docker/`: se salta el override y publica los
  puertos en internet.
- `docker compose -p` con el proyecto de otra persona, ni `docker stop` / `docker rm` sobre
  contenedores que no sean de tu proyecto (`confiabilidad-TU_USUARIO`).
- `docker system prune` (cualquier variante), `docker volume prune`, `docker container prune`,
  `docker network prune` ni `docker image prune -a`: pueden borrar datos, contenedores o
  imágenes de Coolify y de tus compañeros.
- `docker stop` / `docker rm` sobre `$(docker ps -q)` o similares: paran todo, Coolify incluido.
- `sudo systemctl restart docker`: reinicia también Coolify y los stacks de todos.

### Conflicto con netsh (Windows)
`podman_localhost_update.ps1` crea reglas `netsh portproxy` que sobreviven a los reinicios y
ocupan en tu PC `127.0.0.1:5173`, `8000`, `5432` y `6379`. Si alguno de tus puertos coincide
(le pasa al primer usuario), VS Code no puede reenviarlo al mismo número: elige otro sin avisar,
y `localhost:5173` te lleva al stack local de Podman o a ninguna parte.

Antes de trabajar en remoto (PowerShell como Administrador), mira las reglas:
```powershell
netsh interface portproxy show v4tov4
```
Borra la del 5173; repite cambiando el puerto por 5432 y 6379 si vas a reenviarlos:
```powershell
netsh interface portproxy delete v4tov4 listenport=5173 listenaddress=127.0.0.1
```
Para volver a trabajar en local, ejecuta de nuevo `podman_localhost_update.ps1`.

## Calidad
**Backend**, desde la raíz:
```bash
cd backend && pytest && mypy . && ruff check . && black --check .
```

**Frontend**, desde la raíz, un comando cada vez:
```bash
pnpm --filter frontend test
```
```bash
pnpm --filter frontend typecheck
```
```bash
pnpm lint
```

Consulta `AGENTS.md` (convenciones) y `specs/constitution.md` (principios) antes de contribuir.
