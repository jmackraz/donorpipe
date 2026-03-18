#!/usr/bin/env bash
# Full deploy: build + push images, push config, and sync data.
# Usage: ./scripts/deploy-all.sh
#        PROD=1 ./scripts/deploy-all.sh

set -euo pipefail

export PROD="${PROD:-0}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Deploying app..."
"$SCRIPT_DIR/deploy.sh"

echo "==> Pushing config..."
"$SCRIPT_DIR/push-config.sh"
echo "==> Pushing help..."
"$SCRIPT_DIR/push-help.sh"

echo "==> Syncing data..."
"$PROJECT_DIR/warehouse/sync-graphs.sh" oliveseed test_org
