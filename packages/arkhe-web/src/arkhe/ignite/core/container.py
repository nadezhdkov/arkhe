from typing import Any, Type

from arkhe.ignite.di.registry import BeanRegistry
from arkhe.ignite.di.provider import BeanProvider
from arkhe.ignite.di.injector import Injector
from arkhe.ignite.di.scopes import Scope


class Container:
    """
    The IOC Container. Central hub for bean registration and resolution.
    Wraps the BeanRegistry, BeanProvider, and Injector.
    """

    def __init__(self):
        self._registry = BeanRegistry()
        self._provider = BeanProvider(self._registry)
        self._injector = Injector(self._provider)

    def register(self, cls: Type, scope: Scope = Scope.SINGLETON, metadata: dict = None):
        self._registry.register(cls, scope=scope, metadata=metadata)

    def register_instance(self, cls: Type, instance: Any):
        self._registry.register(cls, scope=Scope.SINGLETON)
        self._registry.register_instance(cls, instance)

    def get(self, cls: Type) -> Any:
        return self._provider.get(cls)

    def has(self, cls: Type) -> bool:
        return self._registry.has(cls)

    def clear(self):
        self._registry.clear()

    @property
    def registry(self) -> BeanRegistry:
        return self._registry
