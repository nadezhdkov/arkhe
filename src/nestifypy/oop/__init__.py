"""
nestifypy.oop
=============

Java-inspired Object-Oriented Programming utilities for Python.

Provides explicit interfaces, abstract classes, fail-fast contract validation,
and inheritance utilities that are not available in native Python.

Unlike Python's built-in `abc` module, nestifypy.oop validates contracts as
early as possible — during module loading — rather than at instantiation time.

Public API
----------

    interface       — Declare a behavior contract (methods + attributes).
    implements      — Declare that a class satisfies one or more interfaces.
    abstract_class  — Declare a class with partial implementation.
    abstract_method — Mark a method that subclasses must override.
    override        — Assert that a method intentionally overrides a parent.
    final           — Prevent a class from being subclassed.

Exceptions
----------

    InterfaceImplementationError  — Missing interface method or attribute.
    AbstractMethodError           — Missing abstract method implementation.
    InstantiationError            — Direct instantiation of an abstract class.
    OverrideError                 — @override method has no parent counterpart.
    FinalClassError               — Attempt to subclass a @final class.

Example
-------

    from nestifypy.oop import (
        interface,
        implements,
        abstract_class,
        abstract_method,
        override,
        final,
    )

    @interface
    class ILogger:
        def log(self, message: str) -> None:
            pass

    @abstract_class
    class BaseService:
        def startup(self):
            print("Service started")

        @abstract_method
        def execute(self):
            pass

    @implements(ILogger)
    class ConsoleLogger:
        def log(self, message: str) -> None:
            print(message)

    class UserService(BaseService):
        @override
        def execute(self):
            print("Executing business logic")

    @final
    class Config:
        pass
"""

from nestifypy.oop.interface import (
    interface,
    implements,
    InterfaceImplementationError,
)

from nestifypy.oop.abstract import (
    abstract_class,
    abstract_method,
    override,
    final,
    AbstractMethodError,
    InstantiationError,
    OverrideError,
    FinalClassError,
)

__all__ = [
    # Decorators
    "interface",
    "implements",
    "abstract_class",
    "abstract_method",
    "override",
    "final",
    # Exceptions
    "InterfaceImplementationError",
    "AbstractMethodError",
    "InstantiationError",
    "OverrideError",
    "FinalClassError",
]
