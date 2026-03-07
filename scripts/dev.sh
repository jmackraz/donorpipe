#!/usr/bin/env bash
# Start API and frontend dev servers.
# Usage: ./scripts/dev.sh

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="realfiles_config.json"

# Kill background jobs on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill 0
}
trap cleanup EXIT

echo "Starting API (port 8000)..."
cd "$ROOT"
# Load .env if present (provides DONORPIPE_JWT_SECRET etc.)
if [ -f "$ROOT/.env" ]; then
    set -a; source "$ROOT/.env"; set +a
fi
#uv run fastapi dev src/donorpipe/api/app.py &
USERS_CONFIG="${DONORPIPE_USERS_CONFIG:-users.json}"
JWT_SECRET="${DONORPIPE_JWT_SECRET:?DONORPIPE_JWT_SECRET must be set}"
env DONORPIPE_CONFIG=$CONFIG DONORPIPE_USERS_CONFIG=$USERS_CONFIG DONORPIPE_JWT_SECRET=$JWT_SECRET \
    uv run fastapi dev src/donorpipe/api/app.py &


echo "Starting frontend (port 5173)..."
cd "$ROOT/frontend"
bun run dev &

echo ""
echo "Open in Chrome: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers."

wait