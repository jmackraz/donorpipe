#!/usr/bin/env bash
# Download fresh CSVs from external services into a single account's data directory.
# Services are skipped silently if their API key is not set in .env.
# Only use for real data accounts — sanitized accounts (e.g. test_org) are
# refreshed manually via warehouse/sanitize.sh.
#
# All services download the same data regardless of account; the account arg
# determines which data_base directory receives the files. When multiple live
# accounts are supported in the future, per-account download configuration
# will be needed.
#
# Usage:
#   ./warehouse/download.sh [--config <config.json>] [--year <year>] [--services <svc> ...] <account_id>
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
SERVICES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --year)   YEAR="$2";   shift 2 ;;
    --services)
      shift
      while [[ $# -gt 0 && "$1" != --* ]]; do
        SERVICES+=("$1"); shift
      done ;;
    *)
      if [[ -n "$ACCOUNT" ]]; then
        echo "Error: download.sh takes exactly one account argument" >&2; exit 1
      fi
      ACCOUNT="$1"; shift ;;
  esac
done

if [[ -z "$ACCOUNT" ]]; then
  echo "Usage: ./warehouse/download.sh [--config <config>] [--year <year>] [--services <svc> ...] <account_id>" >&2
  exit 1
fi

if [[ "$CONFIG" != /* ]]; then
  CONFIG="$(pwd)/$CONFIG"
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Error: config not found: $CONFIG" >&2
  exit 1
fi

echo "Account: $ACCOUNT"
echo "=== Download ==="
python3 - "$ROOT" "$CONFIG" "$YEAR" "$ACCOUNT" "${SERVICES[@]+"${SERVICES[@]}"}" <<'PYEOF'
import json, os, subprocess, sys

root        = sys.argv[1]
config_path = sys.argv[2]
year        = sys.argv[3]
account_id  = sys.argv[4]
services    = sys.argv[5:]

with open(config_path) as f:
    config = json.load(f)

all_accounts = config.get("accounts", {})
if account_id not in all_accounts:
    print(f"Error: unknown account: {account_id}", file=sys.stderr)
    sys.exit(1)

data_base = os.path.expanduser(all_accounts[account_id]["data_base"])
print(f"[{account_id}] → {data_base}")

runner = os.path.join(root, "warehouse", "downloads", "runner.py")
cmd = ["uv", "run", runner, "--output-dir", data_base, "--year", year]
if services:
    cmd += ["--services"] + services
tokens_dir = config.get("tokens_dir")
if tokens_dir:
    cmd += ["--tokens-dir", os.path.expanduser(tokens_dir)]
subprocess.run(cmd, env=os.environ.copy(), check=True, cwd=root)
PYEOF
