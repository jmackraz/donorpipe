#!/usr/bin/env bash
# Copy docs/help.md to the host. No container restart needed.
# Usage: ./scripts/push-help.sh
#        PROD=1 ./scripts/push-help.sh

set -euo pipefail

DPIPE_DIR="${DPIPE_DIR:-~/donorpipe}"
PROD="${PROD:-0}"

if [ "$PROD" = "1" ]; then
    DPIPE_HOST="${DPIPE_HOST:-ubuntu@donorpipe.trickybit.com}"
else
    DPIPE_HOST="${DPIPE_HOST:-punkinpi.local}"
fi

ssh "$DPIPE_HOST" "mkdir -p $DPIPE_DIR/docs"
scp docs/help.md "$DPIPE_HOST:$DPIPE_DIR/docs/help.md"
echo "Help docs deployed to $DPIPE_HOST."
