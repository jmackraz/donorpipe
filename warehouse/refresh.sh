#!/usr/bin/env bash
# Download fresh CSVs from external services, rebuild graphs, and sync to server.
# Only downloads into real data accounts — sanitized accounts (e.g. test_org) are
# refreshed manually via warehouse/sanitize.sh + warehouse/sync-graphs.sh.
#
# Usage:
#   ./warehouse/refresh.sh [--config <config.json>] [--year <year>] <account_id>
#   PROD=1 ./warehouse/refresh.sh <account_id>
#
# Services are skipped silently if their API key is not set in .env.
set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPTS/.." && pwd)"

# Load .env (provides STRIPE_API_KEY etc.)
if [ -f "$ROOT/.env" ]; then
    set -a; source "$ROOT/.env"; set +a
fi

CONFIG="$SCRIPTS/warehouse_config.json"
YEAR=$(date +%Y)
ACCOUNT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --year)   YEAR="$2";   shift 2 ;;
    *)
      if [[ -n "$ACCOUNT" ]]; then
        echo "Error: refresh.sh takes exactly one account argument" >&2; exit 1
      fi
      ACCOUNT="$1"; shift ;;
  esac
done

if [[ -z "$ACCOUNT" ]]; then
  echo "Usage: ./warehouse/refresh.sh [--config <config>] [--year <year>] <account_id>" >&2
  exit 1
fi

if [[ "$CONFIG" != /* ]]; then
  CONFIG="$(pwd)/$CONFIG"
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Error: config not found: $CONFIG" >&2
  exit 1
fi

# Validate account exists in config.
python3 - "$CONFIG" "$ACCOUNT" <<'PYEOF'
import json, sys
config_path, account_id = sys.argv[1], sys.argv[2]
with open(config_path) as f:
    config = json.load(f)
if account_id not in config.get("accounts", {}):
    print(f"Error: unknown account: {account_id}", file=sys.stderr)
    sys.exit(1)
PYEOF
echo "Account: $ACCOUNT"

# ── Step 1: Download ──────────────────────────────────────────────────────────
echo ""
echo "=== Download ==="
python3 - "$ROOT" "$CONFIG" "$YEAR" "$ACCOUNT" <<'PYEOF'
import json, os, subprocess, sys
root        = sys.argv[1]
config_path = sys.argv[2]
year        = sys.argv[3]
accounts    = sys.argv[4:]
with open(config_path) as f:
    config = json.load(f)
runner = os.path.join(root, "warehouse", "downloads", "runner.py")
for account_id in accounts:
    data_base = os.path.expanduser(config["accounts"][account_id]["data_base"])
    subprocess.run(
        ["uv", "run", runner, "--output-dir", data_base, "--year", year],
        env=os.environ.copy(), check=True, cwd=root,
    )
PYEOF

# ── Step 1.5: Check whether any account needs a rebuild ───────────────────────
echo ""
echo "=== Change detection ==="
NEEDS_REBUILD=0
python3 - "$ROOT" "$CONFIG" "$ACCOUNT" <<'PYEOF'
import json, os, subprocess, sys
root        = sys.argv[1]
config_path = sys.argv[2]
accounts    = sys.argv[3:]
with open(config_path) as f:
    config = json.load(f)
checker = os.path.join(root, "warehouse", "should_rebuild.py")
needs_rebuild = False
for account_id in accounts:
    acct = config["accounts"][account_id]
    data_base = os.path.expanduser(acct["data_base"])
    graph_path = os.path.join(data_base, "graph.json")
    result = subprocess.run(
        ["uv", "run", checker, "--graph", graph_path, "--dir", data_base],
        cwd=root,
    )
    if result.returncode == 0:
        needs_rebuild = True
sys.exit(0 if needs_rebuild else 1)
PYEOF
NEEDS_REBUILD=$?

if [[ $NEEDS_REBUILD -ne 0 ]]; then
    echo "No changes detected across all accounts. Skipping rebuild and sync."
    exit 0
fi

# ── Step 2: Build graphs ──────────────────────────────────────────────────────
echo ""
echo "=== Build ==="
"$ROOT/scripts/build_graphs.sh" --config "$CONFIG" "$ACCOUNT"

# ── Step 3: Sync to server ────────────────────────────────────────────────────
echo ""
echo "=== Sync ==="
"$ROOT/warehouse/sync-graphs.sh" "$ACCOUNT"
