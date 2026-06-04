from typing import Any, Dict, Optional, Type


class BeanRegistry:
    """
    Central registry for all beans (components) managed by the IOC container.
    Stores class definitions, instances (singletons), and metadata.
    """

    def __init__(self):
        self._definitions: Dict[Type, dict] = {}
        self._instances: Dict[Type, Any] = {}

    def register(self, cls: Type, scope: str = "singleton", metadata: Optional[dict] = None):
        """Register a class as a bean definition."""
        self._definitions[cls] = {
            "scope": scope,
            "metadata": metadata or {},
        }

    def register_instance(self, cls: Type, instance: Any):
        """Store a singleton instance."""
        self._instances[cls] = instance

    def get_instance(self, cls: Type) -> Optional[Any]:
        return self._instances.get(cls)

    def get_definition(self, cls: Type) -> Optional[dict]:
        return self._definitions.get(cls)

    def has(self, cls: Type) -> bool:
        return cls in self._definitions

    def all_definitions(self) -> Dict[Type, dict]:
        return dict(self._definitions)

    def all_instances(self) -> Dict[Type, Any]:
        return dict(self._instances)

    def clear(self):
        self._definitions.clear()
        self._instances.clear()
