#!/usr/bin/env bash
# Wait until the named docker-compose services report healthy.
# Usage: scripts/wait-for-healthy.sh service [service ...]
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <service> [service ...]" >&2
  exit 2
fi

timeout=${TIMEOUT:-180}
start=$SECONDS

for svc in "$@"; do
  echo "waiting for ${svc}..."
  while true; do
    if (( SECONDS - start > timeout )); then
      echo "timeout waiting for ${svc}" >&2
      docker compose ps
      exit 1
    fi
    status=$(docker compose ps --format '{{.Service}}:{{.Health}}' | awk -F: -v s="${svc}" '$1==s {print $2}')
    if [[ "${status}" == "healthy" ]]; then
      echo "  ${svc} healthy"
      break
    fi
    if [[ "${status}" == "unhealthy" ]]; then
      echo "${svc} reported unhealthy" >&2
      docker compose logs "${svc}" | tail -30
      exit 1
    fi
    sleep 2
  done
done

echo "all services healthy."
