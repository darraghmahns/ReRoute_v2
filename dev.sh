#!/bin/bash

# Start the full Reroute development environment:
#   1. GraphHopper  (Docker, port 8989)
#   2. Backend      (uv / uvicorn, port 8000)
#   3. Frontend     (Vite dev server, port 3000)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Guards ────────────────────────────────────────────────────────────────────
if [ ! -f "$PROJECT_ROOT/backend/pyproject.toml" ]; then
    echo "Error: Run this script from the project root directory"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/graphhopper-data/merged-latest.osm.pbf" ]; then
    echo "⚠️  No merged OSM map found."
    echo "   Run ./setup-maps.sh first to download and merge region files."
    echo "   (Default: Ireland + California)"
    echo ""
    read -r -p "Run setup-maps.sh now? [y/N] " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        "$PROJECT_ROOT/setup-maps.sh"
    else
        echo "Skipping. GraphHopper will fail to start without a map file."
    fi
fi

if ! command -v uv &>/dev/null; then
    echo "Error: 'uv' not found. Install it: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

if ! command -v docker &>/dev/null; then
    echo "Error: 'docker' not found."
    exit 1
fi

# ── Cleanup ───────────────────────────────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "Stopping development servers..."
    [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" stop
    echo "Done."
}

trap cleanup EXIT INT TERM

# ── 1. GraphHopper ───────────────────────────────────────────────────────────
echo "Starting GraphHopper (Docker)..."
docker compose -f "$PROJECT_ROOT/docker-compose.yml" up -d
echo "  GraphHopper starting at http://localhost:8989 (may take a few minutes on first run)"

# ── 2. Backend ────────────────────────────────────────────────────────────────
echo "Starting backend (uv)..."
cd "$PROJECT_ROOT/backend"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# ── 3. Frontend ───────────────────────────────────────────────────────────────
echo "Starting frontend (Vite)..."
cd "$PROJECT_ROOT/frontend"
npm run dev -- --host &
FRONTEND_PID=$!

# ── Ready ─────────────────────────────────────────────────────────────────────
echo ""
echo "✅ All services started!"
echo "   Frontend:    http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs:    http://localhost:8000/docs"
echo "   GraphHopper: http://localhost:8989"
echo ""
echo "Press Ctrl+C to stop everything."

wait $BACKEND_PID $FRONTEND_PID
