from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.work_assistant import WorkAssistant


app = FastAPI()

# Initialize a single WorkAssistant instance for the application lifecycle
assistant = WorkAssistant()

# Serve the frontend if it has been built
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


@app.post("/api/session/start")
async def start_session():
    """Start a new assistant session and return analysis data."""
    return assistant.start_session_web()

