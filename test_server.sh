#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "Warning: .env file not found. Make sure to set required environment variables."
  exit 1
fi

# Print environment variables (redacted for security)
echo "JIRA_BASE_URL: $JIRA_BASE_URL"
echo "JIRA_EMAIL: $JIRA_EMAIL"
echo "JIRA_API_TOKEN: ${JIRA_API_TOKEN:0:5}..."

# Start the server in the background
echo "Starting server on port 8003..."
uvicorn web.app:app --port 8003 &
SERVER_PID=$!

# Give the server time to start
echo "Waiting for server to start..."
sleep 3

# Test the API endpoint
echo "Testing session start endpoint..."
curl -X POST http://localhost:8003/api/session/start

# Test the ticket URL endpoint
echo -e "\nTesting ticket URL endpoint..."
curl -X GET http://localhost:8003/api/ticket/APP-123/url

# Cleanup - kill the server
echo -e "\nStopping server..."
kill $SERVER_PID
