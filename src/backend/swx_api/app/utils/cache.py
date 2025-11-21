"""
Simple in-memory TTL cache utilities for demo stability.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional


class TTLCache:
    """Thread-safe namespaced TTL cache."""

    def __init__(self, ttl_seconds: int = 60) -> None:
        self.default_ttl = ttl_seconds
        self._store: Dict[str, tuple[float, Any]] = {}
        self._lock = threading.RLock()

    def _build_key(self, namespace: str, key: str) -> str:
        return f"{namespace}:{key}"

    def get(self, namespace: str, key: str) -> Optional[Any]:
        cache_key = self._build_key(namespace, key)
        with self._lock:
            payload = self._store.get(cache_key)
            if not payload:
                return None
            expires_at, value = payload
            if time.monotonic() >= expires_at:
                self._store.pop(cache_key, None)
                return None
            return value

    def set(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        cache_key = self._build_key(namespace, key)
        expires_at = time.monotonic() + (ttl or self.default_ttl)
        with self._lock:
            self._store[cache_key] = (expires_at, value)

    def invalidate(self, namespace: Optional[str] = None) -> None:
        with self._lock:
            if namespace is None:
                self._store.clear()
                return
            prefix = f"{namespace}:"
            for key in list(self._store.keys()):
                if key.startswith(prefix):
                    self._store.pop(key, None)


global_cache = TTLCache(ttl_seconds=60)

