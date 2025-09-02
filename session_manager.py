import os
import json
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
