#!/usr/bin/env bash
# Hardwired download + rebuild + sync script for the oliveseed account.
#
# Two modes (required):
#   nightly   — full download (all services) + rebuild + sync
#   ondemand  — QBO only download + rebuild + sync (for bookkeeper changes)
#
# In both modes a TODO comment marks where an rclone sync step should be
# added once we are syncing manually-downloaded Benevity reports from
# Google Drive before the rebuild.
#
# Sync targets:
#   After a successful rebuild this script syncs to staging, then to prod
#   if the staging sync succeeded (gated by the exit code from refresh.sh).
#
# Usage:
#   ./warehouse/update.sh [--config <config.json>] nightly|ondemand
#
# On the Pi, pass the Pi config:
#   ./warehouse/update.sh --config warehouse/warehouse_pi_config.json nightly

set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPTS/.." && pwd)"
CONFIG="$SCRIPTS/warehouse_config.json"
ACCOUNT="oliveseed"
MODE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    nightly|ondemand) MODE="$1"; shift ;;
    *) echo "Usage: $0 [--config <config>] nightly|ondemand" >&2; exit 1 ;;
  esac
done

if [[ -z "$MODE" ]]; then
  echo "Usage: $0 [--config <config>] nightly|ondemand" >&2
  exit 1
fi

if [[ "$CONFIG" != /* ]]; then
  CONFIG="$(pwd)/$CONFIG"
fi

case "$MODE" in
  nightly)
    echo "=== Nightly update: all services ==="

    # TODO: rclone sync from Google Drive to pick up new manually-downloaded
    # Benevity reports before rebuilding.
    # rclone sync "gdrive:OSF Exports/$ACCOUNT" "<local data_base>/$ACCOUNT"

    "$SCRIPTS/download.sh" --config "$CONFIG" "$ACCOUNT"
    ;;

  ondemand)
    echo "=== On-demand update: QBO only ==="

    # TODO: rclone sync from Google Drive to pick up new manually-downloaded
    # Benevity reports before rebuilding.
    # rclone sync "gdrive:OSF Exports/$ACCOUNT" "<local data_base>/$ACCOUNT"

    "$SCRIPTS/download.sh" --config "$CONFIG" "$ACCOUNT" --services qbo
    ;;
esac

# Rebuild changed graphs, sync to staging, then sync to prod if staging succeeded.
"$ROOT/warehouse/refresh.sh" --config "$CONFIG" "$ACCOUNT" && \
  PROD=1 "$ROOT/warehouse/refresh.sh" --sync-only --config "$CONFIG" "$ACCOUNT"
