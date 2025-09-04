from fastapi import FastAPI

from core.work_assistant import WorkAssistant


app = FastAPI()

# Initialize a single WorkAssistant instance for the application lifecycle
assistant = WorkAssistant()


@app.post("/api/session/start")
async def start_session():
    """Start a new assistant session and return analysis data."""
    return assistant.start_session_web()

