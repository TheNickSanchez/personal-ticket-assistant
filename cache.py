import os
import json
from typing import Any, Dict, Optional

class Cache:
    """Simple JSON file-based cache."""
    def __init__(self, filename: Optional[str] = None) -> None:
        self.filename = filename or os.getenv("CACHE_FILE", ".cache.json")
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save(self) -> None:
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self._cache, f)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(key)

    def set(self, key: str, value: Dict[str, Any]) -> None:
        self._cache[key] = value
        self._save()
