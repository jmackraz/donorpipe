#!/usr/bin/env bash
# Stream container logs.
# Optional first arg selects a service (api or nginx).
# Usage: ./scripts/logs.sh [service]
#        PROD=1 ./scripts/logs.sh [service]

set -euo pipefail

DPIPE_DIR="${DPIPE_DIR:-~/donorpipe}"
PROD="${PROD:-0}"

if [ "$PROD" = "1" ]; then
    DPIPE_HOST="${DPIPE_HOST:-ubuntu@donorpipe.trickybit.com}"
    COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
else
    DPIPE_HOST="${DPIPE_HOST:-punkinpi.local}"
    COMPOSE="docker compose"
fi

ssh "$DPIPE_HOST" "cd $DPIPE_DIR && $COMPOSE logs -f ${1:-}"
