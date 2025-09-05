---
applyTo: '**'
---

# User Memory

## User Preferences
- Programming languages: Python, JavaScript/React
- Development environment: macOS, zsh
- Code style: Modern Python with type hints, FastAPI for backend, React for frontend

## Project Context
- Current project type: Web application with API backend and React frontend
- Tech stack: Python (FastAPI), React, Rich (terminal UI), Ollama/OpenAI for LLM
- Project name: personal-ticket-assistant
- Purpose: An AI-powered assistant that helps with Jira ticket prioritization, analysis, and management
- Architecture: Modular design with core components, clients, integrations, and utils

## Coding Patterns
- Dataclasses for data models
- Client classes for external service integration
- Rich library for terminal UI formatting
- Caching mechanisms for performance optimization
- FastAPI for web API endpoints
- React for web frontend

## Notes
- Repository branch: dev_webapp
- Application can run in CLI mode or web mode
- Uses Ollama for local LLM inference or OpenAI for cloud-based inference
- Integrates with Jira, GitHub, Calendar, Email, and Slack
- Has both CLI and web interfaces
- Currently undergoing refactoring per REFACTORING_PLAN.md
- Enhancement roadmap available in ENHANCEMENT_ROADMAP.md
