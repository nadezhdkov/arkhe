import inspect
from typing import Any, Type, get_type_hints

from arkhe.ignite.di.registry import BeanRegistry
from arkhe.ignite.di.scopes import Scope
from arkhe.ignite.core.exceptions import (
    BeanNotFoundException,
    CircularDependencyException,
    BeanInitializationException,
)


class BeanProvider:
    """
    Resolves and provides bean instances from the registry.
    Handles singleton caching, prototype creation, and dependency injection.
    """

    def __init__(self, registry: BeanRegistry):
        self._registry = registry
        self._resolving: list = []  # for circular dependency detection

    def get(self, cls: Type) -> Any:
        """Retrieve or create a bean instance."""
        if not self._registry.has(cls):
            raise BeanNotFoundException(
                cls.__name__ if hasattr(cls, "__name__") else str(cls)
            )

        definition = self._registry.get_definition(cls)
        scope = definition.get("scope", Scope.SINGLETON)

        if scope == Scope.SINGLETON:
            instance = self._registry.get_instance(cls)
            if instance is None:
                instance = self._create(cls)
                self._registry.register_instance(cls, instance)
            return instance

        # PROTOTYPE: always create new
        return self._create(cls)

    def _create(self, cls: Type) -> Any:
        """Instantiate a class resolving its constructor dependencies."""
        if cls in self._resolving:
            chain = self._resolving + [cls]
            raise CircularDependencyException([c.__name__ for c in chain])

        self._resolving.append(cls)
        try:
            try:
                hints = get_type_hints(cls.__init__)
            except Exception:
                hints = {}

            params = inspect.signature(cls.__init__).parameters
            kwargs = {}
            for name, param in params.items():
                if name == "self":
                    continue
                annotation = hints.get(name, param.annotation)
                if annotation is inspect.Parameter.empty:
                    continue
                if isinstance(annotation, str):
                    continue  # unresolvable forward ref
                if not isinstance(annotation, type):
                    continue
                if self._registry.has(annotation):
                    kwargs[name] = self.get(annotation)

            try:
                return cls(**kwargs)
            except Exception as e:
                raise BeanInitializationException(cls.__name__, e)
        finally:
            self._resolving.remove(cls)
