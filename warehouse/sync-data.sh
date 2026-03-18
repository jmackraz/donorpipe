#!/usr/bin/env bash
set -euo pipefail
WAREHOUSE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$WAREHOUSE/warehouse_config.json"

if [[ $# -eq 0 ]]; then
  echo "Usage: sync-data.sh <account> [account ...]"
  exit 1
fi

TARGET=$([[ "${PROD:-0}" == "1" ]] && echo "prod" || echo "staging")

HOST=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['hosts']['$TARGET']['host'])")
REMOTE_DIR=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['hosts']['$TARGET']['dir'])")

python3 -c "
import json, os, sys
c = json.load(open('$CONFIG'))
requested = sys.argv[1:]
for account, acct in c['accounts'].items():
    if account in requested:
        print(account + '|' + os.path.expanduser(acct['data_base']))
" -- "$@" | while IFS='|' read -r ACCOUNT SRC; do
  echo "[$TARGET] $SRC → $HOST:$REMOTE_DIR/data/$ACCOUNT/"
  rsync -avz --delete --exclude='/[Oo][Ll][Dd]*/' "$SRC/" "$HOST:$REMOTE_DIR/data/$ACCOUNT/"
done
