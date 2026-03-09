#!/usr/bin/env bash
# Rsync sanitized/fake data to the host.
# Usage: ./scripts/sync-test-data.sh
#        PROD=1 ./scripts/sync-test-data.sh

set -euo pipefail

DPIPE_DIR="${DPIPE_DIR:-~/donorpipe}"
PROD="${PROD:-0}"

if [ "$PROD" = "1" ]; then
    DPIPE_HOST="${DPIPE_HOST:-ubuntu@donorpipe.trickybit.com}"
    rsync -av --delete ~/p/data_sanitization_test_box/sanitized_data/ "$DPIPE_HOST:$DPIPE_DIR/data/test_org/"
else
    DPIPE_HOST="${DPIPE_HOST:-punkinpi.local}"
    rsync -av --delete ./data/ "$DPIPE_HOST:$DPIPE_DIR/data/"
fi
