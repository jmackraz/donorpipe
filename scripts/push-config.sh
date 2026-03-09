#!/usr/bin/env bash
# Copy the right config file to the host and restart the api container.
# Usage: ./scripts/push-config.sh
#        PROD=1 ./scripts/push-config.sh

set -euo pipefail

DPIPE_DIR="${DPIPE_DIR:-~/donorpipe}"
PROD="${PROD:-0}"

if [ "$PROD" = "1" ]; then
    DPIPE_HOST="${DPIPE_HOST:-ubuntu@donorpipe.trickybit.com}"
    COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
    CONFIG_SRC="prod_config.json"
else
    DPIPE_HOST="${DPIPE_HOST:-punkinpi.local}"
    COMPOSE="docker compose"
    CONFIG_SRC="staging_config.json"
fi

scp "$CONFIG_SRC" "$DPIPE_HOST:$DPIPE_DIR/config.json"
ssh "$DPIPE_HOST" "cd $DPIPE_DIR && $COMPOSE restart api"
