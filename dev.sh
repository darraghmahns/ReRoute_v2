#!/bin/bash

set -e

# Start Docker Compose in the background
if [ -f docker-compose.yml ]; then
  echo "Starting Docker containers..."
  docker compose up -d
fi

# Trap Ctrl+C (SIGINT) and stop Docker Compose on exit
trap 'echo "Stopping Docker containers..."; docker compose down' EXIT

# Start backend (in background)
(cd backend && poetry install && poetry run uvicorn app.main:app --reload --port 8002) &

# Start frontend (in foreground)
(cd frontend && npm install && npm run dev)

# When you exit the frontend, the trap will run and stop Docker 