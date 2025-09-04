from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.work_assistant import WorkAssistant

# Load environment variables
load_dotenv()


app = FastAPI()

# Add CORS middleware to allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177"],  # Frontend dev server ports
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize a single WorkAssistant instance for the application lifecycle.
# If required credentials (e.g. Jira) are missing, continue serving the
# frontend but disable API functionality.
try:
    assistant = WorkAssistant()
except Exception as exc:  # ValueError when credentials missing
    assistant = None
    import logging
    logging.warning("WorkAssistant disabled: %s", exc)


@app.post("/api/session/start")
async def start_session():
    """Start a new assistant session and return analysis data."""
    if assistant is None:
        raise HTTPException(status_code=503, detail="Assistant unavailable")
    return assistant.start_session_web()


@app.get("/api/ticket/{ticket_key}/url")
async def get_ticket_url(ticket_key: str):
    """Get the URL to view a ticket in the Jira web interface."""
    if assistant is None:
        raise HTTPException(status_code=503, detail="Assistant unavailable")
    return assistant.get_ticket_url(ticket_key)


# Serve the frontend if it has been built
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
