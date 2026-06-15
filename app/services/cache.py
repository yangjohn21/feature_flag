from threading import Lock
import time
from typing import Any, Optional


class TTLCache:
    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        expire = time.time() + ttl
        with self._lock:
            self._store[key] = (expire, value)

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            expire, value = entry
            if time.time() > expire:
                del self._store[key]
                return None
            return value

    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._store:
                del self._store[key]

    def delete_prefix(self, prefix: str) -> None:
        with self._lock:
            keys = [k for k in list(self._store.keys()) if k.startswith(prefix)]
            for k in keys:
                del self._store[k]

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# Module-level shared in-process cache (one per process). Use this for
# cross-request caching within the same service instance.
cache = TTLCache()
