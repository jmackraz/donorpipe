#!/usr/bin/env bash
set -euo pipefail
WAREHOUSE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$WAREHOUSE")"
CONFIG="${1:-$WAREHOUSE/warehouse_config.json}"

COUNT=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(len(c['sanitize']))")

for i in $(seq 0 $((COUNT - 1))); do
  SRC=$(python3 -c "import json,os; c=json.load(open('$CONFIG')); print(os.path.expanduser(c['sanitize'][$i]['source']))")
  DST=$(python3 -c "import json,os; c=json.load(open('$CONFIG')); print(os.path.expanduser(c['sanitize'][$i]['dest']))")
  echo "Sanitizing $SRC → $DST"
  uv run --directory "$ROOT" python scripts/sanitize_csv.py "$SRC" "$DST"
done
