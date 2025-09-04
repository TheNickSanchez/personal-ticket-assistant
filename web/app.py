from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sys
import os
from dotenv import load_dotenv

# Add parent directory to path so we can import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

from core.work_assistant import WorkAssistant


app = FastAPI(title="Personal Ticket Assistant API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Initialize a single WorkAssistant instance for the application lifecycle
try:
    assistant = WorkAssistant()
except Exception as e:
    print(f"Error initializing WorkAssistant: {e}")
    assistant = None


@app.get("/")
async def root():
    """Serve the main HTML application."""
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))


@app.post("/api/session/start")
async def start_session():
    """Start a new assistant session and return analysis data."""
    if assistant is None:
        return {"error": "WorkAssistant not initialized properly"}
    return assistant.start_session_web()
