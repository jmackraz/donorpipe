#!/usr/bin/env bash
# Update warehouse code on the Pi: git pull + uv sync.
#
# Run this after deploying when warehouse scripts or Python dependencies change.
# The Pi's warehouse clone lives at ~/donorpipe_warehouse/donorpipe.
#
# Environment variables:
#   DPIPE_HOST      SSH hostname of the Pi (default: punkinpi.local)
#   WAREHOUSE_DIR   Path to the warehouse git clone on the Pi
#                   (default: ~/donorpipe_warehouse/donorpipe)
#
# Usage:
#   ./scripts/update-warehouse-pi.sh

set -euo pipefail

DPIPE_HOST="${DPIPE_HOST:-punkinpi.local}"
WAREHOUSE_DIR="${WAREHOUSE_DIR:-~/donorpipe_warehouse/donorpipe}"

echo "==> Updating warehouse on $DPIPE_HOST..."
ssh "$DPIPE_HOST" "cd $WAREHOUSE_DIR && git pull && uv sync"
echo "==> Done."
