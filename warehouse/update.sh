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
#   Staging only: warehouse/refresh.sh  (active)
#   Staging + prod: chained with && PROD=1 --sync-only  (commented out below;
#     comment out the staging-only line when prod is active)
#
# Usage:
#   ./warehouse/update.sh nightly|ondemand

set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPTS/.." && pwd)"
CONFIG="$SCRIPTS/warehouse_config.json"
ACCOUNT="oliveseed"

MODE="${1:-}"

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

  *)
    echo "Usage: $0 nightly|ondemand" >&2
    exit 1
    ;;
esac

# Rebuild changed graphs and sync to staging only.
"$ROOT/warehouse/refresh.sh" --config "$CONFIG" "$ACCOUNT"

# When prod is active, replace the line above with this to sync both:
# "$ROOT/warehouse/refresh.sh" --config "$CONFIG" "$ACCOUNT" && PROD=1 "$ROOT/warehouse/refresh.sh" --sync-only --config "$CONFIG" "$ACCOUNT"
