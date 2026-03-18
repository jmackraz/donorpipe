#!/usr/bin/env bash
# Check for data changes, rebuild graphs, and sync to server.
# Intended to run frequently (e.g. every few minutes via cron or systemd timer).
# Downloads are handled separately by warehouse/download.sh.
#
# Usage:
#   ./warehouse/refresh.sh [--config <config.json>] [account_id ...]
#   PROD=1 ./warehouse/refresh.sh [account_id ...]
#
# If no account_ids given, processes all accounts in the config.
set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPTS/.." && pwd)"

# Load .env if present
if [ -f "$ROOT/.env" ]; then
    set -a; source "$ROOT/.env"; set +a
fi

CONFIG="$SCRIPTS/warehouse_config.json"
ACCOUNTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
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

# ── Change detection ──────────────────────────────────────────────────────────
echo ""
echo "=== Change detection ==="

# Prints account IDs (stdout) that need a rebuild; status messages go to stderr.
REBUILD_LIST=$(python3 - "$ROOT" "$CONFIG" "${ACCOUNTS[@]+"${ACCOUNTS[@]}"}" <<'PYEOF'
import json, os, subprocess, sys

root        = sys.argv[1]
config_path = sys.argv[2]
requested   = sys.argv[3:]

with open(config_path) as f:
    config = json.load(f)

all_accounts = config.get("accounts", {})
if requested:
    missing = set(requested) - set(all_accounts)
    if missing:
        print(f"Error: unknown account(s): {', '.join(sorted(missing))}", file=sys.stderr)
        sys.exit(1)
    targets = {k: v for k, v in all_accounts.items() if k in requested}
else:
    targets = all_accounts

if not targets:
    print("No accounts in config.", file=sys.stderr)
    sys.exit(1)

checker = os.path.join(root, "warehouse", "should_rebuild.py")
for account_id, acct in targets.items():
    data_base = os.path.expanduser(acct["data_base"])
    graph_path = os.path.join(data_base, "graph.json")
    data_dirs = [os.path.join(data_base, d) for d in acct.get("data_dirs", [])]
    print(f"[{account_id}]", file=sys.stderr)
    result = subprocess.run(
        ["uv", "run", checker, "--graph", graph_path] + [arg for d in data_dirs for arg in ("--dir", d)],
        cwd=root,
        stdout=sys.stderr,
    )
    if result.returncode == 0:
        print(f"  → needs rebuild", file=sys.stderr)
        print(account_id)
    else:
        print(f"  → up to date", file=sys.stderr)
PYEOF
)

REBUILD_ACCOUNTS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && REBUILD_ACCOUNTS+=("$line")
done <<< "$REBUILD_LIST"

if [[ ${#REBUILD_ACCOUNTS[@]} -eq 0 ]]; then
  echo "No changes detected. Skipping rebuild and sync."
  exit 0
fi

# ── Build graphs ──────────────────────────────────────────────────────────────
echo ""
echo "=== Build ==="
"$ROOT/scripts/build_graphs.sh" --config "$CONFIG" "${REBUILD_ACCOUNTS[@]}"

# ── Sync to server ────────────────────────────────────────────────────────────
echo ""
echo "=== Sync ==="
"$ROOT/warehouse/sync-graphs.sh" "${REBUILD_ACCOUNTS[@]}"
