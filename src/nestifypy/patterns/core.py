"""
nestifypy.patterns.core
-----------------------
Design pattern decorators for Python classes.
"""

from __future__ import annotations

import types
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

C = TypeVar("C", bound=type)
F = TypeVar("F", bound=Callable[..., Any])

_PATTERNS_META_ATTR = "__patterns_meta__"

def _mark(cls: type, feature: str) -> None:
    if not hasattr(cls, _PATTERNS_META_ATTR):
        setattr(cls, _PATTERNS_META_ATTR, set())
    getattr(cls, _PATTERNS_META_ATTR).add(feature)

class _Unset:
    def __repr__(self) -> str:
        return "<unset>"

_UNSET = _Unset()

class _Patterns:
    @staticmethod
    def singleton(cls: C) -> C:
        """Ensure only one instance of the class exists (Singleton pattern)."""
        instances: Dict[type, Any] = {}

        original_new = cls.__new__

        def __new__(klass: type, *args: Any, **kwargs: Any) -> Any:  # type: ignore
            if klass not in instances:
                if original_new is object.__new__:
                    instances[klass] = object.__new__(klass)
                else:
                    instances[klass] = original_new(klass, *args, **kwargs)
            return instances[klass]

        cls.__new__ = __new__  # type: ignore
        cls._instance = property(lambda self: instances.get(cls))  # type: ignore
        _mark(cls, "singleton")
        return cls

    @staticmethod
    def observable(cls: C) -> C:
        """Add ``__setattr__`` interception to notify listeners of changes."""
        original_setattr = cls.__setattr__ if hasattr(cls, "__setattr__") else None

        def __setattr__(self: Any, name: str, value: Any) -> None:
            if not name.startswith("_"):
                old = getattr(self, name, _UNSET)
                if original_setattr and original_setattr is not object.__setattr__:
                    original_setattr(self, name, value)
                else:
                    object.__setattr__(self, name, value)
                if old is not _UNSET and old != value:
                    for cb in getattr(self, "_observers", []):
                        cb(name, old, value)
            else:
                object.__setattr__(self, name, value)

        def on_change(self: Any, callback: Callable) -> None:
            if not hasattr(self, "_observers"):
                object.__setattr__(self, "_observers", [])
            self._observers.append(callback)

        def off_change(self: Any, callback: Callable) -> None:
            if hasattr(self, "_observers"):
                self._observers.remove(callback)

        cls.__setattr__ = __setattr__  # type: ignore
        cls.on_change = on_change      # type: ignore
        cls.off_change = off_change    # type: ignore
        _mark(cls, "observable")
        return cls

    @staticmethod
    def delegate(field: str, methods: Optional[List[str]] = None) -> Callable[[C], C]:
        """Delegate specified methods to a wrapped object stored in ``self.<field>``."""
        def decorator(cls: C) -> C:
            original_init = cls.__init__ if hasattr(cls, "__init__") else None

            @wraps(original_init or (lambda self: None))
            def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
                if original_init:
                    original_init(self, *args, **kwargs)
                delegate_obj = getattr(self, field, None)
                if delegate_obj is None:
                    return
                target_methods = methods or [
                    m for m in dir(delegate_obj)
                    if not m.startswith("_") and callable(getattr(delegate_obj, m))
                ]
                for method_name in target_methods:
                    if not hasattr(cls, method_name):
                        bound = getattr(delegate_obj, method_name)
                        setattr(self, method_name, bound)

            cls.__init__ = __init__  # type: ignore
            _mark(cls, "delegate")
            return cls

        return decorator

    @staticmethod
    def deprecated(
        cls: Optional[C] = None,
        *,
        reason: str = "This class is deprecated.",
        since: str = "",
    ):
        """Mark a class as deprecated."""
        import warnings

        def _apply(klass: C) -> C:
            original_init = klass.__init__ if hasattr(klass, "__init__") else None
            since_str = f" since v{since}" if since else ""
            msg = f"{klass.__name__} is deprecated{since_str}. {reason}"

            @wraps(original_init or (lambda self: None))
            def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
                warnings.warn(msg, DeprecationWarning, stacklevel=2)
                if original_init:
                    original_init(self, *args, **kwargs)

            klass.__init__ = __init__  # type: ignore
            klass.__deprecated__ = msg  # type: ignore
            _mark(klass, "deprecated")
            return klass

        if cls is not None:
            return _apply(cls)
        return _apply

    @staticmethod
    def sealed(cls: C) -> C:
        """Prevent any subclassing of the decorated class."""
        original_init_subclass = cls.__init_subclass__

        @classmethod  # type: ignore
        def __init_subclass__(klass: type, **kwargs: Any) -> None:
            raise TypeError(
                f"{cls.__name__} is sealed and cannot be subclassed."
            )

        cls.__init_subclass__ = __init_subclass__  # type: ignore
        _mark(cls, "sealed")
        return cls

    @staticmethod
    def mixin(*mixins: type) -> Callable[[C], C]:
        """Dynamically inject mixin classes into a class's MRO at definition time."""
        def decorator(cls: C) -> C:
            new_bases = tuple(
                m for m in mixins if m not in cls.__mro__
            ) + cls.__bases__
            new_cls = types.new_class(
                cls.__name__,
                new_bases,
                {},
                lambda ns: ns.update(cls.__dict__),
            )
            new_cls.__qualname__ = cls.__qualname__
            new_cls.__module__ = cls.__module__
            _mark(new_cls, "mixin")
            return new_cls  # type: ignore

        return decorator

patterns = _Patterns()

__all__ = ["patterns"]
