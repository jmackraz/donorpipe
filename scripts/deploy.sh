#!/usr/bin/env bash
# Deploy donorpipe to a Raspberry Pi (or any remote Docker host).
#
# Environment variables:
#   PI_HOST        SSH hostname of the target host (default: donorpipe.local)
#   PI_DIR         Working directory on the target host (default: ~/donorpipe)
#
# First-time setup on the Pi:
#   1. mkdir -p $PI_DIR $PI_DIR/data
#   2. Copy config.json to $PI_DIR/config.json (edit data_base to "/data")
#   3. Create $PI_DIR/.env with: DONORPIPE_JWT_SECRET=<your-secret>
#
# Subsequent deploys: just run this script.

set -euo pipefail

PI_HOST="${PI_HOST:-donorpipe.local}"
PI_DIR="${PI_DIR:-~/donorpipe}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "==> Building frontend..."
(cd frontend && bun run build)

echo "==> Building Docker images..."
docker compose build

echo "==> Transferring images to Pi (this may take a while)..."
docker save donorpipe-api donorpipe-nginx | ssh "$PI_HOST" docker load

echo "==> Copying compose file to Pi..."
ssh "$PI_HOST" "mkdir -p $PI_DIR"
scp docker-compose.yml "$PI_HOST:$PI_DIR/"

echo "==> Starting containers on Pi..."
ssh "$PI_HOST" "cd $PI_DIR && docker compose up -d"

echo "==> Done! App available at http://$PI_HOST/"
