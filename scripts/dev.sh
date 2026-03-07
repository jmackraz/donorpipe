#!/usr/bin/env bash
# Start API and frontend dev servers.
# Usage: ./scripts/dev.sh

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Kill background jobs on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill 0
}
trap cleanup EXIT

echo "Starting API (port 8000)..."
cd "$ROOT"
uv run fastapi dev src/donorpipe/api/app.py &

echo "Starting frontend (port 5173)..."
cd "$ROOT/frontend"
bun run dev &

echo ""
echo "Open in Chrome: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers."

wait