#!/usr/bin/env bash
# Download fresh CSVs from external services, rebuild graphs, and sync to server.
#
# Usage:
#   ./warehouse/refresh.sh [--config <config.json>] [--year <year>] [account_id ...]
#   PROD=1 ./warehouse/refresh.sh [account_id ...]
#
# If no account_ids are given, all accounts in the config are processed.
# Services are skipped silently if their API key is not set in .env.
set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPTS/.." && pwd)"

# Load .env (provides STRIPE_API_KEY etc.)
if [ -f "$ROOT/.env" ]; then
    set -a; source "$ROOT/.env"; set +a
fi

CONFIG="config.json"
YEAR=$(date +%Y)
ACCOUNTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --year)   YEAR="$2";   shift 2 ;;
    *)        ACCOUNTS+=("$1"); shift ;;
  esac
done

if [[ "$CONFIG" != /* ]]; then
  CONFIG="$(pwd)/$CONFIG"
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Error: config not found: $CONFIG" >&2
  exit 1
fi

# Resolve account list (all accounts if none specified).
RESOLVED=$(python3 - "$CONFIG" "${ACCOUNTS[@]}" <<'PYEOF'
import json, sys
config_path = sys.argv[1]
requested   = set(sys.argv[2:])
with open(config_path) as f:
    config = json.load(f)
accounts = config.get("accounts", {})
if requested:
    missing = requested - set(accounts)
    if missing:
        print(f"Error: unknown account(s): {', '.join(sorted(missing))}", file=sys.stderr)
        sys.exit(1)
    targets = [k for k in accounts if k in requested]
else:
    targets = list(accounts.keys())
if not targets:
    print("No accounts found in config.", file=sys.stderr)
    sys.exit(1)
print(" ".join(targets))
PYEOF
)
read -ra RESOLVED_ACCOUNTS <<< "$RESOLVED"
echo "Accounts: ${RESOLVED_ACCOUNTS[*]}"

# ── Step 1: Download ──────────────────────────────────────────────────────────
echo ""
echo "=== Download ==="
python3 - "$CONFIG" "$YEAR" "${RESOLVED_ACCOUNTS[@]}" <<'PYEOF'
import json, os, subprocess, sys
config_path = sys.argv[1]
year        = sys.argv[2]
accounts    = sys.argv[3:]
with open(config_path) as f:
    config = json.load(f)
root   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
python3 - "$CONFIG" "${RESOLVED_ACCOUNTS[@]}" <<'PYEOF'
import json, os, subprocess, sys
config_path = sys.argv[1]
accounts    = sys.argv[2:]
with open(config_path) as f:
    config = json.load(f)
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
"$ROOT/scripts/build_graphs.sh" --config "$CONFIG" "${RESOLVED_ACCOUNTS[@]}"

# ── Step 3: Sync to server ────────────────────────────────────────────────────
echo ""
echo "=== Sync ==="
"$ROOT/warehouse/sync-graphs.sh" "${RESOLVED_ACCOUNTS[@]}"
