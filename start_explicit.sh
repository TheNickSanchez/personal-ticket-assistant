#!/bin/bash
set -e

echo "🚀 Starting Personal Ticket Assistant with explicit environment variables..."

# Kill any existing processes
pkill -f "python -m uvicorn" || true
pkill -f "npm run dev" || true

# Activate virtual environment
source .venv/bin/activate

# Set environment variables explicitly
export JIRA_BASE_URL=https://docusign.atlassian.net
export JIRA_EMAIL=nick.sanchez@docusign.com
export JIRA_API_TOKEN=ATATT3xFfGF0FxJmz_yqNezWmzrUBsfD--yI-keQR6nImukQNmbeM08Aof81wuLcSYreZpUnXnVwQiI4K8ax9AMIoB977WWTZ6ISrfu6cSJt0vFgl1CUqMIotZmfigF9kPULoOXCLZaeNB8n2oR2NY1Rjfiy4sMvs9-O9WqLsFvLStZtOekY_0w=843910F6
export DEBUG=true
export CONSISTENT_RESULTS=true
export LLM_PROVIDER=ollama
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=llama3.2:3b

# Echo environment for debugging
echo "Using LLM Provider: $LLM_PROVIDER"
echo "Using Ollama Host: $OLLAMA_HOST"
echo "Using Ollama Model: $OLLAMA_MODEL"

# Start backend server
python -m uvicorn web.app:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 3
echo "Backend started at http://localhost:8000"

# Start frontend
cd web/frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ Application started successfully!"
echo "Backend: http://localhost:8000"
echo "Frontend: Check URL in terminal output (likely http://localhost:5173)"
echo ""
echo "💡 Press Ctrl+C to stop all servers"

# Trap to kill background processes when script exits
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

# Wait for Ctrl+C
wait
