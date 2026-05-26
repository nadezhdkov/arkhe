"""
nestifypy.yaml.registry
--------------------
Thread-safe Path registry for the YAML engine.
"""

import threading
from typing import Any, Dict, List, Optional
from pathlib import Path

class PathRegistry:
    """Internal registry mapping dot-paths to their canonical, absolute source YAML file."""

    __slots__ = ("_index", "_lock", "_find_cache")

    def __init__(self) -> None:
        self._index: Dict[str, str] = {}  # path → absolute filename
        self._find_cache: Dict[str, Optional[str]] = {}
        self._lock = threading.RLock()

    def load_from_dict(self, data: Dict[str, str]) -> None:
        """Load the registry index directly from a dictionary."""
        with self._lock:
            self._index = data.copy()

    def to_dict(self) -> Dict[str, str]:
        """Export the registry index as a dictionary."""
        with self._lock:
            return self._index.copy()

    def index_file(self, filepath: Path, data: Dict[str, Any]) -> None:
        """Walk a parsed YAML dict and register all leaf paths with the resolved filepath."""
        canonical_path = str(filepath.resolve())
        with self._lock:
            # We want to clear out old keys for this file first
            self.remove_file(canonical_path)
            self._find_cache.clear()
            self._walk(canonical_path, data, prefix="")

    def _walk(self, filename: str, node: Any, prefix: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                full = f"{prefix}.{k}" if prefix else k
                self._walk(filename, v, full)
        else:
            self._index[prefix] = filename

    def remove_file(self, absolute_path: str) -> None:
        """Remove all keys associated with an absolute path."""
        with self._lock:
            keys_to_delete = [k for k, v in self._index.items() if v == absolute_path]
            for k in keys_to_delete:
                del self._index[k]
            if keys_to_delete:
                self._find_cache.clear()

    def find(self, path: str) -> Optional[str]:
        """Find which absolute file owns a given dot-path."""
        with self._lock:
            if path in self._find_cache:
                return self._find_cache[path]
            
            if path in self._index:
                self._find_cache[path] = self._index[path]
                return self._index[path]
                
            # try prefix match (non-leaf paths)
            prefix = path + "."
            for key, file in self._index.items():
                if key.startswith(prefix) or key == path:
                    self._find_cache[path] = file
                    return file
            
            self._find_cache[path] = None
            return None

    def all_paths(self) -> List[str]:
        with self._lock:
            return list(self._index.keys())

    def clear(self) -> None:
        with self._lock:
            self._index.clear()
            self._find_cache.clear()
