import os
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override dict into base dict."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


class YamlLoader:
    """
    Loads YAML configuration files.
    Supports base ``application.yml`` merged with profile-specific overrides
    (e.g. ``application-dev.yml``).
    """

    def __init__(self, config_dir: str = "."):
        self._config_dir = config_dir
        self._data: Dict[str, Any] = {}

    def load(self, profile: Optional[str] = None) -> Dict[str, Any]:
        if yaml is None:
            raise ImportError(
                "PyYAML is required. Install it with: pip install pyyaml"
            )

        base = self._load_file("application.yml")
        if profile:
            profile_data = self._load_file(f"application-{profile}.yml")
            base = _deep_merge(base, profile_data)

        self._data = base
        return self._data

    def _load_file(self, filename: str) -> dict:
        path = os.path.join(self._config_dir, filename)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Dot-notation key access, e.g. ``'database.host'``."""
        parts = key.split(".")
        value = self._data
        for part in parts:
            if not isinstance(value, dict):
                return default
            value = value.get(part, default)
            if value is default:
                return default
        return value
