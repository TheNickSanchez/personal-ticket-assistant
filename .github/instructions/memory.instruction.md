---
applyTo: '**'
---

# User Memory

## User Preferences
- Programming languages: Python, JavaScript (React)
- Code style preferences: Clean, modern React with functional components and hooks
- Development environment: VS Code, macOS, zsh
- Communication style: Concise with technical details

## Project Context
- Current project type: Personal Ticket Assistant application
- Tech stack: 
  - Backend: Python, FastAPI, Jira API integration, LLM integration (Ollama/OpenAI)
  - Frontend: React, Tailwind CSS
  - CLI UI: Rich library
- Architecture patterns: 
  - Service-oriented with distinct modules
  - LLM for ticket analysis and prioritization
- Key requirements: 
  - Security (using environment variables for credentials)
  - Performance (caching of analysis)
  - User experience (clear, focused UI)
- New features:
  - AI Workload Analysis Overhaul (completed)
  - Invisible RSS Intelligence Integration (implemented)

## Coding Patterns
- Functional React components with hooks
- Python modules with clear separation of concerns
- Environment variable configuration for security
- Git workflow with feature branches (dev_webapp)
- Background services with threading for periodic tasks

## Context7 Research History
- React component styling with Tailwind CSS
- FastAPI endpoint structuring
- LLM integration best practices

## Conversation History
- Initial exploration of the codebase and understanding app structure
- Fixed security issues with exposed API tokens in scripts
- Implemented AI Workload Analysis Overhaul with new UI design and priority logic
- Updated visual design based on provided HTML mockup
- Implemented Invisible RSS Intelligence Integration that enhances AI analysis by parsing Jira RSS activity feeds

## Notes
- The application integrates with Jira for ticket retrieval and analysis
- Uses AI to prioritize tickets based on contextual importance
- Has both CLI and web interfaces
- Latest work focused on enhancing the web UI for AI ticket analysis
- Design requirements specified a clear visual hierarchy for priority tickets
- Jira RSS feed URL: https://docusign.atlassian.net/activity?maxResults=10&streams=account-id+IS+712020%3A48326022-8380-46d3-9945-56436ac46b3d&issues=activity+IS+comment%3Apost&os_authType=basic&title=Nick%20Activity
- Added RSS intelligence to provide better contextual reasoning without UI complexity
- Implementation enhances AI analysis by incorporating activity data like:
  - Last activity date
  - Recent comment count
  - Days since activity
  - User recent activity status
