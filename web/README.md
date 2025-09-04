# Personal Ticket Assistant Web App

This is a web interface for the Personal Ticket Assistant, allowing you to manage and analyze your tickets through a browser-based UI.

## Features

- View your current tickets and their priorities
- Get AI-powered analysis of your workload
- See recommended next steps and priorities
- Simple, responsive user interface

## Getting Started

### Prerequisites

- Python 3.8 or higher
- FastAPI and Uvicorn installed
- Proper environment configuration (see below)

### Running the Web App

To start the web application, simply run the provided script:

```bash
./start_web.sh
```

This script will:
1. Activate your virtual environment if available
2. Create a sample `.env` file if one doesn't exist
3. Install required packages if they're missing
4. Start the Uvicorn server with FastAPI

The web app will be available at http://localhost:8000

### Environment Configuration

The web app requires the following environment variables to be set in a `.env` file:

```
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
```

Make sure to replace the placeholder values with your actual API keys and credentials.

## API Endpoints

The web app exposes the following API endpoints:

- `GET /`: Serves the main HTML interface
- `POST /api/session/start`: Starts a new session and returns ticket analysis data

## Troubleshooting

If you encounter issues with the web app:

1. Check your `.env` file for correct configuration
2. Ensure all required packages are installed
3. Look for error messages in the terminal output
4. Verify your Jira credentials are correct
5. Make sure your LLM provider API key is valid

## Development

To extend the web application:

1. The main web app is defined in `web/app.py`
2. The UI is implemented in `web/index.html`
3. Static assets can be placed in `web/static/`
4. API endpoints use the `WorkAssistant.start_session_web()` method
