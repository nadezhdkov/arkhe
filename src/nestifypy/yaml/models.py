"""
nestifypy.yaml.models
------------------
Data structures for the YAML module.
"""

from typing import Any, Dict, Iterator, List

class DotDict:
    """
    A dict wrapper that allows attribute-style access.

    Example:
        cfg = DotDict({"window": {"width": 800}})
        cfg.window.width  # → 800
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_"):
            return super().__getattribute__(key)
        if key not in self._data:
            raise AttributeError(f"Key '{key}' not found in config")
        val = self._data[key]
        if isinstance(val, dict):
            return DotDict(val)
        return val

    def __getitem__(self, key: str) -> Any:
        val = self._data[key]
        if isinstance(val, dict):
            return DotDict(val)
        return val

    def get(self, path: str, default: Any = None) -> Any:
        """
        Retrieve a value using dot-notation path.

        Example:
            cfg.get("window.width", 800)
        """
        parts = path.split(".")
        current: Any = self._data
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        
        # If the result itself is a dict, return a DotDict for consistency
        if isinstance(current, dict):
            return DotDict(current)
        return current

    def set(self, path: str, value: Any) -> None:
        """Set a value using dot-notation path."""
        parts = path.split(".")
        current = self._data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        return self._data

    def keys(self) -> List[str]:
        return list(self._data.keys())

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        return f"DotDict({self._data!r})"

    def __iter__(self) -> Iterator:
        return iter(self._data)
