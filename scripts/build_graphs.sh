#!/usr/bin/env bash
# Build graph.json for one or more accounts from an app config.
#
# Usage:
#   ./scripts/build_graphs.sh [--config <config.json>] [account_id ...]
#
# --config  path to an app config whose data_base values point to local CSV dirs
#           (default: config.json)
#
# If no account_ids are given, builds all accounts in the config.
set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPTS/.." && pwd)"

CONFIG="config.json"
ACCOUNTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG="$2"; shift 2 ;;
    *)
      ACCOUNTS+=("$1"); shift ;;
  esac
done

# Resolve config path relative to cwd if not absolute
if [[ "$CONFIG" != /* ]]; then
  CONFIG="$(pwd)/$CONFIG"
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Error: config file not found: $CONFIG" >&2
  exit 1
fi

# Extract account→{data_base, data_dirs} pairs from config
python3 - "$CONFIG" "${ACCOUNTS[@]}" <<'PYEOF'
import json, os, subprocess, sys

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
    targets = {k: v for k, v in accounts.items() if k in requested}
else:
    targets = accounts

if not targets:
    print("No accounts found in config.", file=sys.stderr)
    sys.exit(1)

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
script = os.path.join(root, "scripts", "generate_graph_json.py")

for account_id, acct in targets.items():
    data_base = os.path.expanduser(acct["data_base"])
    data_dirs = acct["data_dirs"]
    output    = os.path.join(data_base, "graph.json")

    print(f"\n[{account_id}] {data_base} → {output}")

    env = os.environ.copy()
    env["OSF_EXPORTS"] = data_base

    cmd = ["uv", "run", script, "--output", output, "-d"] + data_dirs
    subprocess.run(cmd, env=env, check=True, cwd=root)
PYEOF
