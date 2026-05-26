"""
nestifypy.yaml.proxy
-----------------
Magic module-level routing logic (PEP 562 and __class__ replacement).
"""

import sys
import types
from typing import Any

from nestifypy.yaml.engine import YamlEngine
from nestifypy.yaml.exceptions import YamlPathError

class YamlModuleProxy(types.ModuleType):
    """
    A custom module class that intercepts attribute and item access
    to provide fluent dot-notation and dictionary-style YAML config retrieval.
    """

    def __getattr__(self, name: str) -> Any:
        """
        Intercept attribute access for fluent YAML resolution:
        `yaml.database.host` -> routes to YamlEngine.get("database.host")
        """
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass

        val = YamlEngine.get(name)
        if val is not None:
            return val

        raise YamlPathError(f"Configuration path '{name}' was not found in the YAML registry.")

    def __getitem__(self, key: str) -> Any:
        """
        Intercept dictionary-style access:
        `yaml["database.host"]` -> routes to YamlEngine.get("database.host")
        """
        val = YamlEngine.get(key)
        if val is not None:
            return val
        raise YamlPathError(f"Configuration path '{key}' was not found in the YAML registry.")

def setup_module_proxy(module_name: str) -> None:
    """
    Apply the proxy class to the given module.
    """
    sys.modules[module_name].__class__ = YamlModuleProxy
