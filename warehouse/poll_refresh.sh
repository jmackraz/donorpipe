#!/usr/bin/env bash
# Long-running service that polls the DonorPipe API for refresh requests
# and triggers update.sh ondemand when a request is pending.
#
# Env vars (set in .env on the Pi):
#   DPIPE_SERVICE_USER    Username for the warehouse API service account
#   DPIPE_SERVICE_PASS    Password for the warehouse API service account
#   DPIPE_API_BASE        Space-separated API base URLs to poll
#                         (e.g. "https://staging.example.com https://prod.example.com")
#   DPIPE_POLL_INTERVAL   Seconds between polls (default: 30)
#
# Usage (normally run via systemd):
#   ./warehouse/poll_refresh.sh [--config <config.json>]

set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPTS/.." && pwd)"
CONFIG="$SCRIPTS/warehouse_pi_config.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "Usage: $0 [--config <config.json>]" >&2; exit 1 ;;
  esac
done

if [[ "$CONFIG" != /* ]]; then
  CONFIG="$(pwd)/$CONFIG"
fi

# Load .env if present
if [[ -f "$ROOT/.env" ]]; then
  set -a; source "$ROOT/.env"; set +a
fi

POLL_INTERVAL="${DPIPE_POLL_INTERVAL:-30}"
API_BASES="${DPIPE_API_BASE:?DPIPE_API_BASE is required}"
SERVICE_USER="${DPIPE_SERVICE_USER:?DPIPE_SERVICE_USER is required}"
SERVICE_PASS="${DPIPE_SERVICE_PASS:?DPIPE_SERVICE_PASS is required}"

# Read account list from config (stdlib only — no uv needed)
ACCOUNTS=$(python3 -c "
import json, sys
c = json.load(open('$CONFIG'))
print(' '.join(c['accounts']))
")

# Per-server token state
declare -A TOKENS
declare -A TOKEN_OBTAINED_AT
TOKEN_LIFETIME=25200  # 7 hours (tokens expire after 8h)

# Authenticate and get a JWT token for a given base URL
get_token() {
  local base="$1"
  curl -sf -X POST "$base/token" \
    -d "username=$SERVICE_USER&password=$SERVICE_PASS" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])"
}

for BASE in $API_BASES; do
  TOKENS["$BASE"]=$(get_token "$BASE")
  TOKEN_OBTAINED_AT["$BASE"]=$(date +%s)
done

echo "$(date): poll_refresh.sh started (servers: $API_BASES, accounts: $ACCOUNTS, interval: ${POLL_INTERVAL}s)"

while true; do
  NOW=$(date +%s)
  ANY_PENDING=false

  for BASE in $API_BASES; do
    # Re-authenticate if token is approaching expiry
    if (( NOW - TOKEN_OBTAINED_AT["$BASE"] > TOKEN_LIFETIME )); then
      echo "$(date): Refreshing API token for $BASE..."
      TOKENS["$BASE"]=$(get_token "$BASE")
      TOKEN_OBTAINED_AT["$BASE"]=$(date +%s)
    fi

    for ACCT in $ACCOUNTS; do
      STATUS=$(curl -sf -H "Authorization: Bearer ${TOKENS[$BASE]}" \
        "$BASE/accounts/$ACCT/refresh" || echo '{"pending":false}')

      PENDING=$(echo "$STATUS" | python3 -c "import json,sys; print(json.load(sys.stdin).get('pending', False))")

      if [[ "$PENDING" == "True" ]]; then
        echo "$(date): Refresh requested for $ACCT on $BASE"
        ANY_PENDING=true
      fi
    done
  done

  if [[ "$ANY_PENDING" == "true" ]]; then
    echo "$(date): Running update.sh ondemand"
    "$SCRIPTS/update.sh" --config "$CONFIG" ondemand || \
      echo "$(date): update.sh ondemand exited with error $?"
  fi

  sleep "$POLL_INTERVAL"
done
