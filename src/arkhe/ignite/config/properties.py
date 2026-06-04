from typing import Any, Optional

from arkhe.ignite.config.yaml_loader import YamlLoader


class Properties:
    """
    Typed access to configuration values loaded from YAML.
    """

    def __init__(self, loader: YamlLoader):
        self._loader = loader

    def get(self, key: str, default: Any = None) -> Any:
        return self._loader.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        value = self._loader.get(key)
        if value is None:
            return default
        return int(value)

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self._loader.get(key)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "yes")

    def get_str(self, key: str, default: str = "") -> str:
        value = self._loader.get(key)
        if value is None:
            return default
        return str(value)

    def require(self, key: str) -> Any:
        """Return the value or raise if missing."""
        from arkhe.ignite.core.exceptions import ConfigurationException
        value = self._loader.get(key)
        if value is None:
            raise ConfigurationException(
                f"Required configuration key '{key}' is not set."
            )
        return value
