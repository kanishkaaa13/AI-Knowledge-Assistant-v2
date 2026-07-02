from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if entry.expires_at <= time.time():
                self._store.pop(key, None)
                return None
            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        with self._lock:
            self._store[key] = CacheEntry(value=value, expires_at=time.time() + ttl_seconds)

    def delete_prefix(self, prefix: str) -> None:
        with self._lock:
            for key in [item for item in self._store.keys() if item.startswith(prefix)]:
                self._store.pop(key, None)


app_cache = TTLCache()
