#!/usr/bin/env bash
# Long-running service that polls the DonorPipe API for refresh requests
# and triggers update.sh ondemand when a request is pending.
#
# Env vars (set in .env on the Pi):
#   DPIPE_SERVICE_USER    Username for the warehouse API service account
#   DPIPE_SERVICE_PASS    Password for the warehouse API service account
#   DPIPE_API_BASE        API base URL (e.g. https://donorpipe.trickybit.com)
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
API_BASE="${DPIPE_API_BASE:?DPIPE_API_BASE is required}"
SERVICE_USER="${DPIPE_SERVICE_USER:?DPIPE_SERVICE_USER is required}"
SERVICE_PASS="${DPIPE_SERVICE_PASS:?DPIPE_SERVICE_PASS is required}"

# Read account list from config (stdlib only — no uv needed)
ACCOUNTS=$(python3 -c "
import json, sys
c = json.load(open('$CONFIG'))
print(' '.join(c['accounts']))
")

# Authenticate and get a JWT token
get_token() {
  curl -sf -X POST "$API_BASE/token" \
    -d "username=$SERVICE_USER&password=$SERVICE_PASS" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])"
}

TOKEN=$(get_token)
TOKEN_OBTAINED=$(date +%s)
TOKEN_LIFETIME=25200  # 7 hours (tokens expire after 8h)

echo "$(date): poll_refresh.sh started (accounts: $ACCOUNTS, interval: ${POLL_INTERVAL}s)"

while true; do
  # Re-authenticate if token is approaching expiry
  NOW=$(date +%s)
  if (( NOW - TOKEN_OBTAINED > TOKEN_LIFETIME )); then
    echo "$(date): Refreshing API token..."
    TOKEN=$(get_token)
    TOKEN_OBTAINED=$(date +%s)
  fi

  for ACCT in $ACCOUNTS; do
    STATUS=$(curl -sf -H "Authorization: Bearer $TOKEN" \
      "$API_BASE/accounts/$ACCT/refresh" || echo '{"pending":false}')

    PENDING=$(echo "$STATUS" | python3 -c "import json,sys; print(json.load(sys.stdin).get('pending', False))")

    if [[ "$PENDING" == "True" ]]; then
      echo "$(date): Refresh requested for $ACCT — running update.sh ondemand"
      "$SCRIPTS/update.sh" --config "$CONFIG" ondemand || \
        echo "$(date): update.sh ondemand exited with error $?"
    fi
  done

  sleep "$POLL_INTERVAL"
done
