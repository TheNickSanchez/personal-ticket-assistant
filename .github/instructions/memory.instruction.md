---
applyTo: '**'
---

# User Memory

## User Preferences
- Programming languages: Python, JavaScript, React
- Code style preferences: Modern React hooks, clean code
- Development environment: VS Code, macOS, FastAPI + React
- Communication style: Direct, efficient debugging

## Project Context
- Current project type: Personal Ticket Assistant - AI-powered Jira webapp
- Tech stack: FastAPI backend, React frontend, Ollama LLM, Jira API
- Architecture patterns: REST API, component-based React
- Key requirements: Real-time Jira integration, AI analysis, production-ready

## Coding Patterns
- React: Functional components with hooks, proper state management
- FastAPI: Clean endpoint structure with proper error handling
- Debugging: Console logging for UI issues, comprehensive error handling
- Testing: Incremental testing after each change

## Current Session Progress
- ✅ Fixed age/stale data calculation from API dates
- ✅ Search functionality working but has input glitch (1 letter at a time)
- 🔄 AI Priority Analysis tab goes blank - needs logging
- 🔄 Live mode not default - needs to set isDemoMode=false
- 🔄 Navigation between views causes blank pages

## Bug Status
- Search Input Bug: Input field only allows one character at a time
- AI Analysis View: Goes blank when clicked - missing view rendering
- Demo Mode: Still defaulting to demo instead of live data
- Navigation: View switching between tickets/analysis/work not working properly

## Environment
- Backend: Running on port 8001 with proper PYTHONPATH
- Frontend: Running on port 5173 with React dev server
- New .env file available but not activated yet
