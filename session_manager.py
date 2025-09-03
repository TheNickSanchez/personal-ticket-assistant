import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from knowledge_base import KnowledgeBase


class SessionManager:
    """Manage persisted session data: last scan, current focus, notes, history.

    Stores a single JSON file next to the project root by default.
    """

    def __init__(
        self, path: str = "session_state.json", knowledge_base_path: str = "knowledge_base.json"
    ) -> None:
        self.path = path
        self.data: Dict[str, Any] = {
            "last_scan": None,
            "current_focus": None,
            "tickets": [],
            "ticket_progress": {},
            "conversation_history": [],
            "feedback": {},
            "work_patterns": {"commands": {}, "categories": {}},
            "dependencies": {},
        }
        self.kb = KnowledgeBase(knowledge_base_path)
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
        # Ensure work_patterns structure always exists
        self.data.setdefault("work_patterns", {"commands": {}, "categories": {}})

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

    def add_feedback(self, ticket_key: str, context: str, feedback: str) -> None:
        feedback_store: Dict[str, Dict[str, List[str]]] = self.data.setdefault("feedback", {})
        ticket_fb: Dict[str, List[str]] = feedback_store.setdefault(ticket_key, {})
        ctx_key = context.strip()
        entries: List[str] = ticket_fb.setdefault(ctx_key, [])
        entries.append(feedback)
        self.save()

    def get_feedback(self, ticket_key: str, context: str) -> List[str]:
        feedback_store: Dict[str, Dict[str, List[str]]] = self.data.get("feedback", {})
        ticket_fb: Dict[str, List[str]] = feedback_store.get(ticket_key, {})
        return list(ticket_fb.get(context.strip(), []))
    # Work pattern logging
    def log_command(self, command: str) -> None:
        patterns = self.data.setdefault("work_patterns", {})
        commands = patterns.setdefault("commands", {})
        commands[command] = commands.get(command, 0) + 1
        self.save()

    def log_ticket_category(self, category: str) -> None:
        patterns = self.data.setdefault("work_patterns", {})
        categories = patterns.setdefault("categories", {})
        categories[category] = categories.get(category, 0) + 1
        self.save()

    def get_work_patterns(self) -> Dict[str, Dict[str, int]]:
        patterns = self.data.get("work_patterns")
        if not isinstance(patterns, dict):
            patterns = {"commands": {}, "categories": {}}
            self.data["work_patterns"] = patterns
        return patterns
    def set_dependencies(self, deps: Dict[str, List[str]]) -> None:
        self.data["dependencies"] = deps
        self.save()

    def get_dependencies(self) -> Dict[str, List[str]]:
        return dict(self.data.get("dependencies", {}))

    def reset(self) -> None:
        self.data.update(
            {
                "last_scan": None,
                "current_focus": None,
                "tickets": [],
                "ticket_progress": {},
                "conversation_history": [],
                "feedback": {},
                "dependencies": {},
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
        previous = {t.get("key"): t for t in self.data.get("tickets", []) if isinstance(t, dict)}
        for ticket in tickets:
            key = getattr(ticket, "key", None)
            status = getattr(ticket, "status", None)
            prev_status = previous.get(key, {}).get("status") if key else None
            if key and status == "Done" and prev_status != "Done":
                self.record_resolution(ticket)
        self.data["tickets"] = [self._serialize_ticket(t) for t in tickets]
        self.set_last_scan()
        self.save()

    def record_resolution(self, ticket: Any) -> None:
        summary = getattr(ticket, "summary", "")
        resolution = getattr(ticket, "resolution", "") or getattr(ticket, "description", "")
        self.kb.add(getattr(ticket, "key", ""), summary, resolution)

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

