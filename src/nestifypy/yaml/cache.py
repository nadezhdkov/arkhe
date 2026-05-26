"""
nestifypy.yaml.cache
-----------------
Memory cache for loaded YAML configurations.
"""

from typing import Dict, Optional
import threading
from nestifypy.yaml.models import DotDict

class ConfigCache:
    """Stores resolved YAML configurations (thread-safe memory only)."""

    def __init__(self) -> None:
        self._cache: Dict[str, DotDict] = {}  # absolute path -> DotDict
        self._lock = threading.RLock()

    def get(self, absolute_path: str) -> Optional[DotDict]:
        """Retrieve a cached DotDict by its absolute path."""
        with self._lock:
            return self._cache.get(absolute_path)

    def set(self, absolute_path: str, config: DotDict) -> None:
        """Store a DotDict in the cache."""
        with self._lock:
            self._cache[absolute_path] = config

    def remove(self, absolute_path: str) -> None:
        """Remove a configuration from the cache."""
        with self._lock:
            self._cache.pop(absolute_path, None)

    def clear(self) -> None:
        """Clear all cached configurations."""
        with self._lock:
            self._cache.clear()
