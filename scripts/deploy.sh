#!/usr/bin/env bash
# Deploy donorpipe to a Raspberry Pi (or any remote Docker host).
#
# Environment variables:
#   DPIPE_HOST     SSH hostname of the target host (default: punkinpi.local)
#   DPIPE_USER     SSH username for the target host (default: ubuntu for prod, local user otherwise)
#   DPIPE_DIR      Working directory on the target host (default: ~/donorpipe)
#   PROD           Set to 1 to deploy with TLS (uses docker-compose.prod.yml override)
#
# First-time setup on the Pi:
#   1. mkdir -p $DPIPE_DIR $DPIPE_DIR/data
#   2. Copy config.json to $DPIPE_DIR/config.json (edit data_base to "/data")
#   3. Create $DPIPE_DIR/.env with: DONORPIPE_JWT_SECRET=<your-secret>
#
# Subsequent deploys: just run this script.
# Production deploy: PROD=1 ./scripts/deploy.sh

set -euo pipefail

PROD="${PROD:-0}"

if [ "$PROD" = "1" ]; then
    DPIPE_HOST="${DPIPE_HOST:-donorpipe.trickybit.com}"
    DPIPE_USER="${DPIPE_USER:-ubuntu}"
else
    DPIPE_HOST="${DPIPE_HOST:-punkinpi.local}"
    DPIPE_USER="${DPIPE_USER:-}"
fi

# Build SSH target (user@host or just host)
if [ -n "$DPIPE_USER" ]; then
    DPIPE_TARGET="${DPIPE_USER}@${DPIPE_HOST}"
else
    DPIPE_TARGET="$DPIPE_HOST"
fi
DPIPE_DIR="${DPIPE_DIR:-~/donorpipe}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

if [ "$PROD" = "1" ]; then
    read -r -p "Deploy to PRODUCTION ($DPIPE_TARGET)? [y/N] " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
fi

echo "==> Building frontend..."
(cd frontend && bun run build)

echo "==> Building Docker images..."
if [ "$PROD" = "1" ]; then
    DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose -f docker-compose.yml -f docker-compose.prod.yml build
else
    docker compose build
fi

echo "==> Transferring images to host (this may take a while)..."
docker save donorpipe-api donorpipe-nginx | ssh "$DPIPE_TARGET" docker load

echo "==> Copying compose file(s) to host..."
ssh "$DPIPE_TARGET" "mkdir -p $DPIPE_DIR"
scp docker-compose.yml "$DPIPE_TARGET:$DPIPE_DIR/"

if [ "$PROD" = "1" ]; then
    scp docker-compose.prod.yml "$DPIPE_TARGET:$DPIPE_DIR/"
    ssh "$DPIPE_TARGET" "mkdir -p $DPIPE_DIR/nginx"
    scp nginx/nginx.prod.conf "$DPIPE_TARGET:$DPIPE_DIR/nginx/nginx.prod.conf"
fi

echo "==> Starting containers on host..."
if [ "$PROD" = "1" ]; then
    ssh "$DPIPE_TARGET" "cd $DPIPE_DIR && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
else
    ssh "$DPIPE_TARGET" "cd $DPIPE_DIR && docker compose up -d"
fi

if [ "$PROD" = "1" ]; then
    echo "==> Done! App available at https://donorpipe.trickybit.com"
else
    echo "==> Done! App available at http://$DPIPE_HOST/"
fi
