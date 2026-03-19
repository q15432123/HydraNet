"""
Short-Term Memory — per-task context that lives during task execution.

Implemented as an in-memory TTL cache. Entries expire after a
configurable duration.
"""

from __future__ import annotations

import time
from typing import Any


class ShortTermMemory:
    """TTL-based in-memory context store."""

    def __init__(self, default_ttl: float = 300.0):
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expires_at)
        self._default_ttl = default_ttl

    def set(self, key: str, value: Any, ttl: float | None = None):
        expires = time.time() + (ttl or self._default_ttl)
        self._store[key] = (value, expires)

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires = entry
        if time.time() > expires:
            del self._store[key]
            return None
        return value

    def delete(self, key: str):
        self._store.pop(key, None)

    def get_context(self, prefix: str) -> dict[str, Any]:
        """Get all non-expired entries matching a prefix."""
        self._cleanup()
        return {
            k: v for k, (v, exp) in self._store.items()
            if k.startswith(prefix) and time.time() <= exp
        }

    def _cleanup(self):
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]

    def clear(self):
        self._store.clear()

    def size(self) -> int:
        self._cleanup()
        return len(self._store)
