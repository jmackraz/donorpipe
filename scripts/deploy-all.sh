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

# don't do this: data is sync'd from the warehouse, not my development machine
#echo "==> Syncing data..."
#"$PROJECT_DIR/warehouse/sync-graphs.sh" --config "$PROJECT_DIR/warehouse/warehouse_config.json" oliveseed test_org

echo "NOTE: Remember to update graphs from data warehouse if needed."

echo "==> Updating warehouse code on Pi..."
"$SCRIPT_DIR/update-warehouse-pi.sh"
