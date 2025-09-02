import os
import json
from datetime import datetime, timedelta
from typing import Optional


class SessionManager:
    """Manage session state persisted to a JSON file."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.last_scan: Optional[datetime] = None
        self.current_focus: Optional[str] = None
        self.load()

    def load(self) -> None:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                last_scan = data.get("last_scan")
                self.last_scan = (
                    datetime.fromisoformat(last_scan) if last_scan else None
                )
                self.current_focus = data.get("current_focus")
            except Exception:
                self.last_scan = None
                self.current_focus = None
        else:
            self.last_scan = None
            self.current_focus = None

    def save(self) -> None:
        data = {
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "current_focus": self.current_focus,
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def within_24_hours(self) -> bool:
        if not self.last_scan:
            return False
        return datetime.now() - self.last_scan < timedelta(hours=24)
from datetime import datetime
from typing import Optional, Any, Dict

class SessionManager:
    """Persist and restore session state."""
    def __init__(self, filename: str = "session_state.json") -> None:
        self.filename = os.path.join(os.path.dirname(__file__), filename)

    def save_progress(self, current_focus: Optional[Any], notes: Optional[Any] = None, **extra: Dict[str, Any]) -> None:
        """Persist current session state to disk."""
        state = {
            "timestamp": datetime.now().isoformat(),
            "current_focus": getattr(current_focus, "key", None),
            "notes": notes,
        }
        if extra:
            state.update(extra)
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(state, f)
