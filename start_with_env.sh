#!/bin/bash
set -e  # Exit on error

# Export environment variables
export JIRA_BASE_URL=https://docusign.atlassian.net
export JIRA_EMAIL=nick.sanchez@docusign.com
export JIRA_API_TOKEN=ATATT3xFfGF0FxJmz_yqNezWmzrUBsfD--yI-keQR6nImukQNmbeM08Aof81wuLcSYreZpUnXnVwQiI4K8ax9AMIoB977WWTZ6ISrfu6cSJt0vFgl1CUqMIotZmfigF9kPULoOXCLZaeNB8n2oR2NY1Rjfiy4sMvs9-O9WqLsFvLStZtOekY_0w=843910F6
export DEBUG=true
export CONSISTENT_RESULTS=true
export LLM_PROVIDER=ollama
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=llama3.2:3b

echo "🚀 Starting Personal Ticket Assistant with environment variables..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
  echo "🔄 Activating virtual environment..."
  source .venv/bin/activate
fi

# Check if node_modules exists in frontend, if not install dependencies
if [ ! -d "web/frontend/node_modules" ]; then
  echo "📦 Installing frontend dependencies..."
  cd web/frontend
  npm install
  cd ../..
fi

# Start backend server in the background
echo "🔌 Starting backend server..."
# Add parent directory to Python path to make core module accessible
export PYTHONPATH=$PYTHONPATH:$(pwd)
cd web
uvicorn app:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend dev server in the background
echo "🎨 Starting frontend dev server..."
cd web/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

echo "✅ App started successfully!"
echo "🌐 Frontend: http://localhost:5173"
echo "🌐 Backend: http://localhost:8000"
echo ""
echo "💡 Press Ctrl+C to stop the servers"

# Trap to kill background processes on script exit
trap "echo '🛑 Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

# Wait for user to press Ctrl+C
wait
