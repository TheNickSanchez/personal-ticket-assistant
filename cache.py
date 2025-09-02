import os
import json
from typing import Any, Dict, Optional
import hashlib

class SemanticCache:
    """Lightweight semantic-ish cache layered on top of file cache.

    This provides a stable key derivation by hashing arbitrary inputs so callers
    can store/retrieve by content rather than manual keys. It falls back to the
    same on-disk JSON file used by Cache, but exposes helper methods.
    """
    def __init__(self, filename: Optional[str] = None) -> None:
        self._file = Cache(filename)

    def _hash_key(self, *parts: Any) -> str:
        h = hashlib.sha256()
        for p in parts:
            h.update(repr(p).encode("utf-8"))
            h.update(b"\x00")
        return h.hexdigest()

    def get_by_content(self, *parts: Any) -> Optional[Dict[str, Any]]:
        return self._file.get(self._hash_key(*parts))

    def set_by_content(self, value: Dict[str, Any], *parts: Any) -> None:
        self._file.set(self._hash_key(*parts), value)

    def clear(self) -> None:
        self._file.clear()

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

    def clear(self) -> None:
        """Remove all items from the cache."""
        self._cache = {}
        self._save()
