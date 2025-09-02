import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import asdict, is_dataclass

from cache import Cache


class SessionManager:
    """Manage persisted session data including last scan timestamp."""

    def __init__(self, cache: Optional[Cache] = None) -> None:
        # Use separate file to avoid clashing with other cache data
        self.cache = cache or Cache(filename=os.getenv("SESSION_FILE", "session_cache.json"))
        data = self.cache.get("session") or {}
        self.last_scan: Optional[datetime] = None
        if data.get("last_scan"):
            try:
                self.last_scan = datetime.fromisoformat(data["last_scan"])
            except ValueError:
                self.last_scan = None
        self._tickets: List[Dict[str, Any]] = data.get("tickets", [])

    def _serialize_ticket(self, ticket: Any) -> Dict[str, Any]:
        data = asdict(ticket) if is_dataclass(ticket) else dict(ticket)
        if isinstance(data.get("created"), datetime):
            data["created"] = data["created"].isoformat()
        if isinstance(data.get("updated"), datetime):
            data["updated"] = data["updated"].isoformat()
        return data

    def update_session(self, tickets: List[Any]) -> None:
        """Store tickets and update the last_scan timestamp."""
        self.last_scan = datetime.now()
        self._tickets = [self._serialize_ticket(t) for t in tickets]
        self.cache.set(
            "session",
            {
                "last_scan": self.last_scan.isoformat(),
                "tickets": self._tickets,
            },
        )

    def needs_rescan(self) -> bool:
        if not self.last_scan:
            return True
        return datetime.now() - self.last_scan > timedelta(hours=24)

    def get_tickets(self) -> List[Dict[str, Any]]:
        return self._tickets

    def get_ticket_summary(self) -> str:
        if not self._tickets:
            return "No tickets stored."
        first = ", ".join(t["key"] for t in self._tickets[:3])
        more = "" if len(self._tickets) <= 3 else f", +{len(self._tickets) - 3} more"
        return f"Last session had {len(self._tickets)} tickets: {first}{more}."
=======
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
