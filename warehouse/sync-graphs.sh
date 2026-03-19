#!/usr/bin/env bash
# Sync pre-built graph.json files to staging or production.
#
# Usage:
#   ./warehouse/sync-graphs.sh [--config <config.json>] <account> [account ...]
#   PROD=1 ./warehouse/sync-graphs.sh [--config <config.json>] <account> [account ...]
set -euo pipefail

WAREHOUSE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$WAREHOUSE/warehouse_config.json"
ACCOUNTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    *) ACCOUNTS+=("$1"); shift ;;
  esac
done

if [[ ${#ACCOUNTS[@]} -eq 0 ]]; then
  echo "Usage: sync-graphs.sh [--config <config>] <account> [account ...]"
  exit 1
fi

if [[ "$CONFIG" != /* ]]; then
  CONFIG="$(pwd)/$CONFIG"
fi

TARGET=$([[ "${PROD:-0}" == "1" ]] && echo "prod" || echo "staging")

HOST=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['hosts']['$TARGET']['host'])")
REMOTE_DIR=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['hosts']['$TARGET']['dir'])")

while IFS='|' read -r ACCOUNT SRC; do
  GRAPH_FILE="$SRC/graph.json"
  if [[ ! -f "$GRAPH_FILE" ]]; then
    echo "Warning: $GRAPH_FILE not found — skipping $ACCOUNT" >&2
    continue
  fi
  echo "[$TARGET] $GRAPH_FILE → $HOST:$REMOTE_DIR/data/$ACCOUNT/graph.json"
  ssh -n "$HOST" "mkdir -p $REMOTE_DIR/data/$ACCOUNT"
  rsync -avz "$GRAPH_FILE" "$HOST:$REMOTE_DIR/data/$ACCOUNT/graph.json"
done < <(python3 -c "
import json, os, sys
c = json.load(open('$CONFIG'))
requested = sys.argv[1:]
for account, acct in c['accounts'].items():
    if account in requested:
        print(account + '|' + os.path.expanduser(acct['data_base']))
" -- "${ACCOUNTS[@]}")
