#!/bin/bash
# Prepara la sesión remota: dependencias del backend y del frontend. Docker se levanta aparte,
# solo cuando la tarea toca código, con .claude/hooks/start-services.sh.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"
VENV="$CLAUDE_PROJECT_DIR/.venv"

if [ ! -x "$VENV/bin/python" ]; then
  python3.12 -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --disable-pip-version-check -r backend/requirements-dev.txt

pnpm install --silent

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
