#!/bin/bash
# Prepara la sesión remota: dependencias del backend y del frontend, y Postgres + Redis en Docker.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"
VENV="$CLAUDE_PROJECT_DIR/.venv"
LOG=/tmp/confiabilidad-dockerd.log

if [ ! -x "$VENV/bin/python" ]; then
  python3.12 -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --disable-pip-version-check -r backend/requirements-dev.txt

pnpm install --silent

if ! docker info >/dev/null 2>&1; then
  pgrep -x dockerd >/dev/null || rm -f /var/run/docker.pid
  pgrep -x containerd >/dev/null || rm -f /var/run/docker/containerd/containerd.pid
  setsid nohup dockerd >"$LOG" 2>&1 < /dev/null &
  for _ in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 1; done
fi
docker compose -f docker/docker-compose.yml up -d db redis
for _ in $(seq 1 30); do
  docker compose -f docker/docker-compose.yml exec -T db pg_isready -U confiabilidad >/dev/null 2>&1 && break
  sleep 1
done
if ! docker compose -f docker/docker-compose.yml exec -T db pg_isready -U confiabilidad >/dev/null 2>&1; then
  echo "Postgres is not accepting connections after 30 s; see: docker compose -f docker/docker-compose.yml logs db" >&2
  exit 1
fi

# Mismos valores de desarrollo que el CI (.github/workflows/ci.yml); no son secretos.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  cat >>"$CLAUDE_ENV_FILE" <<EOF
export PATH="$VENV/bin:\$PATH"
export DJANGO_SECRET_KEY=ci-insecure-key
export DJANGO_DEBUG=0
export DJANGO_SECURE_HARDENING=0
export DATABASE_URL=postgres://confiabilidad:confiabilidad@localhost:5432/confiabilidad
export REDIS_URL=redis://localhost:6379/0
EOF
fi
