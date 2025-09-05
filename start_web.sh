#!/bin/bash

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Warning: No virtual environment found"
fi

# Export PYTHONPATH to include current directory
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Check if we have Node.js installed for the frontend
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed"
    exit 1
fi

# Start the backend server in the background
echo "Starting FastAPI backend server at http://localhost:8000"
uvicorn web.app:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Navigate to frontend directory
cd web/frontend

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start the frontend development server
echo "Starting frontend development server at http://localhost:5173"
npm run dev

# Cleanup: Kill the backend server when frontend is stopped
kill $BACKEND_PID