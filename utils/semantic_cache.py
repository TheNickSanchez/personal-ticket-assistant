import os
import json
from datetime import datetime
from typing import Optional, Dict, Any


class SemanticCache:
    """Lightweight cache storing LLM analysis."""

    def __init__(self, cache_file: str = "semantic_cache.json"):
        self.cache_file = os.path.join(os.path.dirname(__file__), cache_file)
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache: Dict[str, Dict[str, Any]] = json.load(f)
            except json.JSONDecodeError:
                self.cache = {}
        else:
            self.cache = {}

    def _save(self) -> None:
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f)

    def get(self, ticket_hash: str) -> Optional[Dict[str, Any]]:
        return self.cache.get(ticket_hash)

    def set(self, ticket_hash: str, analysis_text: str) -> None:
        self.cache[ticket_hash] = {
            "analysis_text": analysis_text,
            "ticket_hash": ticket_hash,
            "timestamp": datetime.now().isoformat(),
        }
        self._save()
