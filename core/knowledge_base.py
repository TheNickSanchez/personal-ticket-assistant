import json
import os
from typing import Dict, List


class KnowledgeBase:
    """Simple JSON-backed store for resolved ticket summaries and resolutions."""

    def __init__(self, path: str = "knowledge_base.json") -> None:
        self.path = path
        self.data: List[Dict[str, str]] = []
        self.load()

    def load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = []

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def add(self, ticket_key: str, summary: str, resolution: str) -> None:
        """Add or update a ticket resolution."""
        entry = {
            "ticket_key": ticket_key,
            "summary": summary,
            "resolution": resolution,
        }
        for idx, existing in enumerate(self.data):
            if existing.get("ticket_key") == ticket_key:
                self.data[idx] = entry
                break
        else:
            self.data.append(entry)
        self.save()

    def search(self, query: str) -> List[Dict[str, str]]:
        """Return entries whose summary or resolution contain the query."""
        query = query.lower()
        return [
            e
            for e in self.data
            if query in e.get("summary", "").lower() or query in e.get("resolution", "").lower()
        ]
