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
```bash
# 1. Variables de entorno de desarrollo del backend
cp backend/.env.example backend/.env

# 2. Levantar backend + frontend + Redis + Postgres + Celery
docker compose -f docker/docker-compose.yml up --build
```
- API:      http://localhost:8000/api/health/
- Frontend: http://localhost:5173

## Trabajo local sin Docker
```bash
# Frontend / desktop (desde la raíz)
pnpm install
pnpm --filter frontend dev
pnpm --filter desktop tauri dev

# Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

## Calidad
```bash
# Backend
cd backend && pytest && mypy backend/ && ruff check . && black --check .

# Frontend
pnpm --filter frontend test
pnpm --filter frontend typecheck
pnpm lint
```

Consulta `AGENTS.md` (convenciones) y `specs/constitution.md` (principios) antes de contribuir.
