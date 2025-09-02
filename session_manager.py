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
