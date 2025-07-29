#!/bin/bash

# Show logs for the development environment
echo "Showing Reroute development logs..."

# Check if we're in the right directory
if [ ! -f "backend/pyproject.toml" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Function to show logs in parallel
show_logs() {
    echo "=== Backend Logs ==="
    cd backend
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug &
    BACKEND_PID=$!
    cd ..
    
    echo "=== Frontend Logs ==="
    cd frontend
    npm run dev -- --host &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for both processes
    wait $BACKEND_PID $FRONTEND_PID
}

# Cleanup function
cleanup() {
    echo "Stopping development servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup EXIT INT TERM

show_logs