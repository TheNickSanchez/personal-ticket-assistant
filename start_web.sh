#!/bin/bash

# Script to start the FastAPI web app
echo "Starting Personal Ticket Assistant Web API..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Activate the virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Virtual environment activated."
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated."
else
    echo "Warning: Virtual environment not found at .venv/ or venv/"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found!"
    echo "Creating a basic .env file with required configuration."
    cat > .env << EOL
# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Jira Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your_email@example.com
JIRA_API_TOKEN=your_jira_api_token

# Environment Settings
DEBUG=true
CONSISTENT_RESULTS=true
EOL
    echo "Please edit the .env file with your actual API keys and configuration."
fi

# Create static directory if it doesn't exist
if [ ! -d "web/static" ]; then
    mkdir -p web/static
    echo "Created web/static directory"
fi

# Export DEBUG mode for more verbose output
export DEBUG=true

# Install required packages if missing
if ! pip list | grep -q "fastapi"; then
    echo "Installing required packages..."
    pip install fastapi uvicorn[standard] python-dotenv
fi

# Start the web server from the project root directory
# This ensures proper loading of environment variables and module imports
echo "Starting web server at http://localhost:8000"
export PYTHONPATH="$PYTHONPATH:$(pwd)"
uvicorn web.app:app --reload
