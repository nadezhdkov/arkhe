"""
arkhe.yaml.registry
--------------------
Thread-safe Path registry for the YAML engine.
"""

import threading
from typing import Any, Dict, List, Optional
from pathlib import Path

class PathRegistry:
    """Internal registry mapping dot-paths to their canonical, absolute source YAML file."""

    __slots__ = ("_index", "_prefixes", "_leaf_index", "_lock")

    def __init__(self) -> None:
        self._index: Dict[str, str] = {}  # exact path → absolute filename
        self._prefixes: Dict[str, str] = {} # prefix → absolute filename
        self._leaf_index: Dict[str, str] = {} # leaf_key → full_path
        self._lock = threading.RLock()

    def load_from_dict(self, data: Dict[str, str]) -> None:
        """Load the registry index directly from a dictionary."""
        with self._lock:
            self._index = data.copy()
            self._rebuild_indices()

    def to_dict(self) -> Dict[str, str]:
        """Export the registry index as a dictionary."""
        with self._lock:
            return self._index.copy()

    def _rebuild_indices(self) -> None:
        self._prefixes.clear()
        self._leaf_index.clear()
        for path, filename in self._index.items():
            parts = path.split('.')
            self._leaf_index[parts[-1]] = path
            
            for i in range(1, len(parts)):
                prefix = ".".join(parts[:i])
                self._prefixes[prefix] = filename

    def index_file(self, filepath: Path, data: Dict[str, Any]) -> None:
        """Walk a parsed YAML dict and register all leaf paths with the resolved filepath."""
        canonical_path = str(filepath.resolve())
        with self._lock:
            self.remove_file(canonical_path)
            self._walk(canonical_path, data, prefix="")

    def _walk(self, filename: str, node: Any, prefix: str) -> None:
        if isinstance(node, dict):
            if prefix:
                self._prefixes[prefix] = filename
                leaf = prefix.split('.')[-1]
                self._leaf_index[leaf] = prefix
            for k, v in node.items():
                full = f"{prefix}.{k}" if prefix else k
                self._walk(filename, v, full)
        else:
            self._index[prefix] = filename
            leaf = prefix.split('.')[-1] if prefix else ""
            if leaf:
                self._leaf_index[leaf] = prefix

    def remove_file(self, absolute_path: str) -> None:
        """Remove all keys associated with an absolute path."""
        with self._lock:
            keys_to_delete = [k for k, v in self._index.items() if v == absolute_path]
            if not keys_to_delete:
                return
            for k in keys_to_delete:
                del self._index[k]
            self._rebuild_indices()

    def find(self, path: str) -> Optional[str]:
        """Find which absolute file owns a given dot-path (O(1) resolution)."""
        with self._lock:
            res = self._index.get(path)
            if res is not None:
                return res
            return self._prefixes.get(path)

    def resolve_leaf(self, key: str) -> Optional[str]:
        """Resolve a leaf key to its full dot-path (O(1))."""
        with self._lock:
            return self._leaf_index.get(key)

    def all_paths(self) -> List[str]:
        with self._lock:
            return list(self._index.keys())

    def clear(self) -> None:
        with self._lock:
            self._index.clear()
            self._prefixes.clear()
            self._leaf_index.clear()
