import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class SessionManager:
    """Handle saving and loading of persistent session state."""

    def __init__(self, path: str = "session_state.json"):
        self.path = path
        self.data: Dict[str, Any] = {
            "last_scan": None,
            "current_focus": None,
            "ticket_progress": {},
            "conversation_history": [],
        }
        self.load()

    # ------------------------------------------------------------------
    # Basic file operations
    # ------------------------------------------------------------------
    def load(self) -> None:
        """Load session data from disk if it exists."""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.data.update(loaded)
            except Exception:
                # If the file is corrupted, start fresh
                pass

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    @property
    def last_scan(self) -> Optional[datetime]:
        value = self.data.get("last_scan")
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def within_24_hours(self) -> bool:
        """Return True if the last scan was within the past 24 hours."""
        last = self.last_scan
        if not last:
            return False
        return datetime.now() - last < timedelta(hours=24)

    def set_last_scan(self) -> None:
        self.data["last_scan"] = datetime.now().isoformat()
        self.save()

    def set_current_focus(self, ticket_key: Optional[str]) -> None:
        self.data["current_focus"] = ticket_key
        self.save()

    def get_current_focus(self) -> Optional[str]:
        return self.data.get("current_focus")

    def add_ticket_note(self, ticket_key: str, note: str) -> None:
        notes: Dict[str, str] = self.data.setdefault("ticket_progress", {})
        notes[ticket_key] = note
        self.save()

    def add_message(self, message: str) -> None:
        history: List[str] = self.data.setdefault("conversation_history", [])
        history.append(message)
        self.save()

    def reset(self) -> None:
        """Clear session data (used when starting a fresh scan)."""
        self.data = {
            "last_scan": None,
            "current_focus": None,
            "ticket_progress": {},
            "conversation_history": [],
        }
        self.save()
