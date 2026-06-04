from typing import Type
from arkhe.ignite.decorators.component import _register

_CONTROLLER_REGISTRY: dict[Type, str] = {}  # cls -> base path


def Controller(path: str = "/"):
    """
    Marks a class as an HTTP controller bean.

    Usage::

        @Controller("/users")
        class UserController: ...
    """
    def decorator(cls: Type) -> Type:
        _register(cls, "controller")
        cls.__arkhe_path__ = path
        _CONTROLLER_REGISTRY[cls] = path
        return cls

    return decorator
