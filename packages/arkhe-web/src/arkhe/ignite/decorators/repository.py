from typing import Type
from arkhe.ignite.decorators.component import _register


def Repository(cls: Type = None, *, scope: str = "singleton"):
    """
    Marks a class as a repository (data-access) bean.

    Usage::

        @Repository
        class UserRepository: ...
    """
    if cls is not None:
        return _register(cls, "repository", scope)

    def decorator(c: Type) -> Type:
        return _register(c, "repository", scope)

    return decorator
