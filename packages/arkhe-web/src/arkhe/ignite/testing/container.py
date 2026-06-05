from typing import Any, Type

from arkhe.ignite.core.container import Container
from arkhe.ignite.di.scopes import Scope


class TestContainer:
    """
    A lightweight container for unit and integration testing.
    Allows overriding beans with mocks or test doubles.

    Usage::

        container = TestContainer()
        container.override(UserService, mock_user_service)
        container.register(UserController)
        controller = container.get(UserController)
    """

    def __init__(self):
        self._container = Container()
        self._overrides: dict[Type, Any] = {}

    def override(self, cls: Type, instance: Any):
        """Replace a bean type with a specific instance (mock or stub)."""
        self._overrides[cls] = instance
        self._container.register_instance(cls, instance)

    def register(self, cls: Type, scope: Scope = Scope.SINGLETON):
        self._container.register(cls, scope=scope)

    def get(self, cls: Type) -> Any:
        if cls in self._overrides:
            return self._overrides[cls]
        return self._container.get(cls)

    def clear(self):
        self._container.clear()
        self._overrides.clear()
