from typing import Type

_COMPONENT_REGISTRY: list[Type] = []


def _register(cls: Type, stereotype: str, scope: str = "singleton") -> Type:
    cls.__nestifypy_scope__ = scope
    cls.__nestifypy_metadata__ = {"stereotype": stereotype}
    if cls not in _COMPONENT_REGISTRY:
        _COMPONENT_REGISTRY.append(cls)
    return cls


def Component(cls: Type = None, *, scope: str = "singleton"):
    """
    Generic stereotype decorator. Marks a class as a managed bean.

    Usage::

        @Component
        class MyComponent: ...

        @Component(scope="prototype")
        class MyProto: ...
    """
    if cls is not None:
        # called as @Component (no args)
        return _register(cls, "component", scope)

    # called as @Component(scope=...)
    def decorator(c: Type) -> Type:
        return _register(c, "component", scope)

    return decorator
