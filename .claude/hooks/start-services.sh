#!/bin/bash
# Levanta Postgres + Redis en Docker para los tests; solo hace falta si la tarea toca código.
set -euo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"
LOG=/tmp/confiabilidad-dockerd.log

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
