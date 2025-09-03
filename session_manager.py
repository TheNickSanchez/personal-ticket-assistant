import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class SessionManager:
    """Manage persisted session data: last scan, current focus, notes, history.

    Stores a single JSON file next to the project root by default.
    """

    def __init__(self, path: str = "session_state.json") -> None:
        self.path = path
        self.data: Dict[str, Any] = {
            "last_scan": None,
            "current_focus": None,
            "tickets": [],
            "ticket_progress": {},
            "conversation_history": [],
            "recent_tickets": [],
        }
        self.load()

    # Basic file IO
    def load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self.data.update(loaded)
            except Exception:
                # Corrupt or unreadable; keep defaults
                pass

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    # Convenience helpers
    @property
    def last_scan(self) -> Optional[datetime]:
        raw = self.data.get("last_scan")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None

    def within_24_hours(self) -> bool:
        last = self.last_scan
        return bool(last and datetime.now() - last < timedelta(hours=24))

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

    # Recently focused ticket tracking
    def record_ticket(self, ticket: Any) -> None:
        """Store a lightweight summary of a ticket that was recently discussed."""
        recent: List[Dict[str, str]] = self.data.setdefault("recent_tickets", [])
        summary = {
            "key": getattr(ticket, "key", ""),
            "summary": getattr(ticket, "summary", ""),
        }
        recent.append(summary)
        # Keep only the last 5 entries
        self.data["recent_tickets"] = recent[-5:]
        self.save()

    def get_recent_ticket_summaries(self, exclude: Optional[str] = None, limit: int = 3) -> List[Dict[str, str]]:
        """Return summaries of recently discussed tickets, excluding the provided key."""
        recent: List[Dict[str, str]] = list(self.data.get("recent_tickets", []))
        if exclude:
            recent = [t for t in recent if t.get("key") != exclude]
        return recent[-limit:]

    def reset(self) -> None:
        self.data.update(
            {
                "last_scan": None,
                "current_focus": None,
                "tickets": [],
                "ticket_progress": {},
                "conversation_history": [],
                "recent_tickets": [],
            }
        )
        self.save()

    # Ticket snapshot storage
    def _serialize_ticket(self, ticket: Any) -> Dict[str, Any]:
        data = asdict(ticket) if is_dataclass(ticket) else dict(ticket)
        if isinstance(data.get("created"), datetime):
            data["created"] = data["created"].isoformat()
        if isinstance(data.get("updated"), datetime):
            data["updated"] = data["updated"].isoformat()
        return data

    def update_session(self, tickets: List[Any]) -> None:
        self.data["tickets"] = [self._serialize_ticket(t) for t in tickets]
        self.set_last_scan()
        self.save()

    def needs_rescan(self) -> bool:
        last = self.last_scan
        if not last:
            return True
        return datetime.now() - last > timedelta(hours=24)

    def get_tickets(self) -> List[Dict[str, Any]]:
        return list(self.data.get("tickets", []))

    def get_ticket_summary(self) -> str:
        tickets = self.data.get("tickets", [])
        if not tickets:
            return "No tickets stored."
        first = ", ".join(t.get("key", "") for t in tickets[:3])
        more = "" if len(tickets) <= 3 else f", +{len(tickets) - 3} more"
        return f"Last session had {len(tickets)} tickets: {first}{more}."

    # Optional: save quick progress snapshot
    def save_progress(self, current_focus: Optional[Any], notes: Optional[Any] = None) -> None:
        self.set_current_focus(getattr(current_focus, "key", current_focus))
        if notes:
            self.data["notes"] = notes
        self.save()

