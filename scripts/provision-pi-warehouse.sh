#!/usr/bin/env bash
# Install warehouse systemd units on the Pi (one-time setup).
#
# Substitutes the actual Pi username into the service file, then installs
# and enables the systemd timer.
#
# Environment variables:
#   DPIPE_HOST    SSH hostname of the Pi (default: punkinpi.local)
#   PI_USER       Pi username (default: detected via SSH)
#
# Usage:
#   ./scripts/provision-pi-warehouse.sh
#   DPIPE_HOST=mypi.local PI_USER=pi ./scripts/provision-pi-warehouse.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

DPIPE_HOST="${DPIPE_HOST:-punkinpi.local}"
PI_USER="${PI_USER:-$(ssh "$DPIPE_HOST" 'echo $USER')}"

echo "==> Installing systemd units on $DPIPE_HOST (user: $PI_USER)..."

# Substitute <pi-user> placeholder and write to temp files
TMPFILE_NIGHTLY="$(mktemp /tmp/donorpipe-nightly-XXXXXX.service)"
TMPFILE_ONDEMAND="$(mktemp /tmp/donorpipe-ondemand-XXXXXX.service)"
sed "s/<pi-user>/$PI_USER/g" \
    "$PROJECT_DIR/warehouse/systemd/donorpipe-nightly.service" > "$TMPFILE_NIGHTLY"
sed "s/<pi-user>/$PI_USER/g" \
    "$PROJECT_DIR/warehouse/systemd/donorpipe-ondemand.service" > "$TMPFILE_ONDEMAND"

scp "$TMPFILE_NIGHTLY"  "$DPIPE_HOST:/tmp/donorpipe-nightly.service"
scp "$TMPFILE_ONDEMAND" "$DPIPE_HOST:/tmp/donorpipe-ondemand.service"
scp "$PROJECT_DIR/warehouse/systemd/donorpipe-nightly.timer" \
    "$DPIPE_HOST:/tmp/donorpipe-nightly.timer"
rm "$TMPFILE_NIGHTLY" "$TMPFILE_ONDEMAND"

ssh "$DPIPE_HOST" "
  sudo mv /tmp/donorpipe-nightly.service  /etc/systemd/system/
  sudo mv /tmp/donorpipe-nightly.timer    /etc/systemd/system/
  sudo mv /tmp/donorpipe-ondemand.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now donorpipe-nightly.timer
  sudo systemctl enable --now donorpipe-ondemand.service
  systemctl list-timers donorpipe-nightly.timer
"

echo "==> Done. Timer and on-demand poller installed and enabled on $DPIPE_HOST."
