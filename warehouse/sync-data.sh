#!/usr/bin/env bash
set -euo pipefail
WAREHOUSE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$WAREHOUSE/warehouse_config.json"

TARGET=$([[ "${PROD:-0}" == "1" ]] && echo "prod" || echo "staging")

HOST=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['hosts']['$TARGET']['host'])")
REMOTE_DIR=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['hosts']['$TARGET']['dir'])")

python3 -c "
import json, os
c = json.load(open('$CONFIG'))
for account, src in c['accounts'].items():
    print(account + '|' + os.path.expanduser(src))
" | while IFS='|' read -r ACCOUNT SRC; do
  echo "[$TARGET] $SRC → $HOST:$REMOTE_DIR/data/$ACCOUNT/"
  rsync -avz --delete "$SRC/" "$HOST:$REMOTE_DIR/data/$ACCOUNT/"
done
