from typing import Type
from nestifypy.ignite.decorators.component import _register


def Service(cls: Type = None, *, scope: str = "singleton"):
    """
    Marks a class as a service bean.

    Usage::

        @Service
        class UserService: ...
    """
    if cls is not None:
        return _register(cls, "service", scope)

    def decorator(c: Type) -> Type:
        return _register(c, "service", scope)

    return decorator
