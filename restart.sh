#!/bin/bash
set -e  # Exit on error

echo "🚀 Starting Personal Ticket Assistant..."

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
  echo "🔄 Activating virtual environment..."
  source .venv/bin/activate
fi

# Kill any existing servers on the same ports
echo "🧹 Cleaning up any existing servers..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
lsof -ti:5174 | xargs kill -9 2>/dev/null || true
lsof -ti:5175 | xargs kill -9 2>/dev/null || true
lsof -ti:5176 | xargs kill -9 2>/dev/null || true

# Double check .env file values
echo "🔍 Checking environment configuration..."
if grep -q "LLM_PROVIDER=ollama" .env; then
  echo "✅ Using Ollama as LLM provider"
else
  echo "⚠️ Warning: LLM_PROVIDER not set to 'ollama' in .env file"
  echo "   Current setting: $(grep LLM_PROVIDER .env)"
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
python -m uvicorn web.app:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a bit for the backend to start
sleep 3

# Start frontend dev server in the background
echo "🎨 Starting frontend dev server..."
cd web/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

# Wait a bit for the frontend to start
sleep 3

echo "✅ App started successfully!"
echo "🌐 Frontend: Check the terminal for the URL (usually http://localhost:5173 or similar)"
echo "🌐 Backend: http://localhost:8000"
echo ""
echo "💡 Press Ctrl+C to stop the servers"

# Trap to kill background processes on script exit
trap "echo '🛑 Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

# Wait for user to press Ctrl+C
wait
