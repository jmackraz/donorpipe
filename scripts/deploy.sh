#!/usr/bin/env bash
# Deploy donorpipe to a Raspberry Pi (or any remote Docker host).
#
# Environment variables:
#   PI_HOST        SSH hostname of the target host (default: donorpipe.local)
#   PI_DIR         Working directory on the target host (default: ~/donorpipe)
#   PROD           Set to 1 to deploy with TLS (uses docker-compose.prod.yml override)
#
# First-time setup on the Pi:
#   1. mkdir -p $PI_DIR $PI_DIR/data
#   2. Copy config.json to $PI_DIR/config.json (edit data_base to "/data")
#   3. Create $PI_DIR/.env with: DONORPIPE_JWT_SECRET=<your-secret>
#
# Subsequent deploys: just run this script.
# Production deploy: PROD=1 PI_HOST=ubuntu@44.237.105.98 ./scripts/deploy.sh

set -euo pipefail

PI_HOST="${PI_HOST:-donorpipe.local}"
PI_DIR="${PI_DIR:-~/donorpipe}"
PROD="${PROD:-0}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "==> Building frontend..."
(cd frontend && bun run build)

echo "==> Building Docker images..."
docker compose build

echo "==> Transferring images to Pi (this may take a while)..."
docker save donorpipe-api donorpipe-nginx | ssh "$PI_HOST" docker load

echo "==> Copying compose file(s) to Pi..."
ssh "$PI_HOST" "mkdir -p $PI_DIR"
scp docker-compose.yml "$PI_HOST:$PI_DIR/"

if [ "$PROD" = "1" ]; then
    scp docker-compose.prod.yml "$PI_HOST:$PI_DIR/"
    ssh "$PI_HOST" "mkdir -p $PI_DIR/nginx"
    scp nginx/nginx.prod.conf "$PI_HOST:$PI_DIR/nginx/nginx.prod.conf"
fi

echo "==> Starting containers on Pi..."
if [ "$PROD" = "1" ]; then
    ssh "$PI_HOST" "cd $PI_DIR && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
else
    ssh "$PI_HOST" "cd $PI_DIR && docker compose up -d"
fi

if [ "$PROD" = "1" ]; then
    echo "==> Done! App available at https://donorpipe.trickybit.com"
else
    echo "==> Done! App available at http://$PI_HOST/"
fi
