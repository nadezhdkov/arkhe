"""
arkhe.komodo.core
-------------------
The `komodo` namespace — all class-level annotation decorators live here.
"""

from typing import TypeVar, Callable, Any
from arkhe.komodo.ast_engine import apply_generator
from arkhe.komodo.ast_generators.constructor import generate_constructor
from arkhe.komodo.ast_generators.repr import generate_to_str
from arkhe.komodo.ast_generators.eq_hash import generate_eq_hash
from arkhe.komodo.ast_generators.record import generate_record
from arkhe.komodo.ast_generators.immutable import generate_immutable
from arkhe.komodo.ast_generators.builder import generate_builder
from arkhe.komodo.ast_generators.accessors import generate_accessors
from arkhe.komodo.ast_generators.validation import generate_non_null, generate_validated
from arkhe.komodo.ast_generators.logger import generate_logger
from arkhe.komodo.ast_generators.copyable import generate_copyable
from arkhe.komodo.ast_generators.serialization import generate_to_dict, generate_from_dict, generate_json

C = TypeVar("C", bound=type)


class _Komodo:

    @staticmethod
    def data(cls: C) -> C:
        """
        Generates:

        - all-args constructor (__init__)
        - __str__()
        - __eq__()
        - __hash__()

        Similar to Lombok @Data.

        Example:
            @komodo.data
            class User:
                name: str
                age: int
        """
        cls = _Komodo.all_args_constructor(cls)
        cls = _Komodo.to_str(cls)
        cls = _Komodo.eq(cls)
        from arkhe.komodo.ast_generators.utils import mark_komodo_meta
        mark_komodo_meta(cls, "data")
        return cls

    @staticmethod
    def value(cls: C) -> C:
        """
        Generates:

        - all-args constructor
        - __str__()
        - __eq__()
        - __hash__()
        - immutable fields

        Similar to Lombok @Value.
        """
        cls = _Komodo.data(cls)
        cls = _Komodo.immutable(cls)
        from arkhe.komodo.ast_generators.utils import mark_komodo_meta
        mark_komodo_meta(cls, "value")
        return cls

    @staticmethod
    def no_args_constructor(cls: C) -> C:
        """
        Generates an empty constructor.

        Example:
            User()
        """
        cls = apply_generator(cls, lambda c, t: generate_constructor(c, t, "no_args"))
        return cls

    @staticmethod
    def required_args_constructor(cls: C) -> C:
        """
        Generates a constructor containing only required fields.

        Fields with default values are ignored.

        Example:
            >>> @komodo.required_args_constructor
            ... class User:
            ...     name: str
            ...     age: int = 20
            ...
            >>> user = User("Mark")
            >>> print(user.name)
            Mark
        """
        cls = apply_generator(cls, lambda c, t: generate_constructor(c, t, "required"))
        return cls

    @staticmethod
    def all_args_constructor(cls: C) -> C:
        """
        Generates a constructor containing all annotated fields.

        Example:
            User(name, age)
        """
        cls = apply_generator(cls, lambda c, t: generate_constructor(c, t, "all"))
        return cls

    @staticmethod
    def to_str(cls: C) -> C:
        """
        Generates a readable __str__() implementation.

        Example:
            User(name='John', age=20)
        """
        cls = apply_generator(cls, generate_to_str)
        return cls

    @staticmethod
    def eq(cls: C) -> C:
        """
        Generates __eq__() and __hash__() methods.
        """
        cls = apply_generator(cls, generate_eq_hash)
        return cls

    @staticmethod
    def immutable(cls: C) -> C:
        """
        Makes all fields read-only after initialization.
        """
        cls = apply_generator(cls, generate_immutable)
        return cls

    @staticmethod
    def builder(cls: C) -> C:
        """
        Generates a fluent Builder API.

        Example:
            User.builder()\
                .with_name("John")\
                .with_age(20)\
                .build()
        """
        cls = apply_generator(cls, generate_builder)
        return cls

    @staticmethod
    def singular(field_name: str) -> Callable[[C], C]:
        """
        Marks a collection field as singular for Builder generation.

        Example:
            @komodo.singular("roles")

        Generates:
            builder.role("ADMIN")
            builder.role("MODERATOR")
        """
        def decorator(cls: C) -> C:
            if not hasattr(cls, "__komodo_singulars__"):
                setattr(cls, "__komodo_singulars__", [])
            getattr(cls, "__komodo_singulars__").append(field_name)
            return cls
        return decorator

    @staticmethod
    def accessors(
        fluent: bool = False,
        getter: bool = True,
        setter: bool = True,
        withers: bool = False
    ) -> Callable[[C], C]:
        """
        Generates accessors.

        Args:
            fluent:
                Generates fluent methods.

            getter:
                Generates get_<field>() methods.

            setter:
                Generates set_<field>() methods.

            withers:
                Generates immutable with_<field>() methods.
        """
        def decorator(cls: C) -> C:
            cls = apply_generator(cls, lambda c, t: generate_accessors(c, t, fluent, getter, setter, withers))
            return cls
        return decorator

    @staticmethod
    def getter(cls: C) -> C:
        """
        Generates get_<field>() methods.

        Example:
            user.get_name()
        """
        cls = apply_generator(cls, lambda c, t: generate_accessors(c, t, False, True, False, False))
        return cls

    @staticmethod
    def setter(cls: C) -> C:
        """
        Generates set_<field>(value) methods.

        Example:
            user.set_name("John")
        """
        cls = apply_generator(cls, lambda c, t: generate_accessors(c, t, False, False, True, False))
        return cls

    @staticmethod
    def withers(cls: C) -> C:
        """
        Generates immutable with_<field>() methods.

        Example:
            new_user = user.with_name("John")
        """
        cls = apply_generator(cls, lambda c, t: generate_accessors(c, t, False, False, False, True))
        return cls

    @staticmethod
    def logger(cls: C) -> C:
        """
        Injects a logger instance into the class.

        Example:
            self.logger.info("message")
        """
        cls = apply_generator(cls, generate_logger)
        return cls

    @staticmethod
    def non_null(cls: C) -> C:
        """
        Validates that annotated fields cannot receive None.
        """
        cls = apply_generator(cls, generate_non_null)
        return cls

    @staticmethod
    def validated(cls: C) -> C:
        """
        Executes field validators during construction and assignment.
        """
        cls = apply_generator(cls, generate_validated)
        return cls

    @staticmethod
    def copyable(cls: C) -> C:
        """
        Generates a copy() method.

        Example:
            user.copy()
            user.copy(name="John")
        """
        cls = apply_generator(cls, generate_copyable)
        return cls

    @staticmethod
    def to_dict(cls: C) -> C:
        """
        Generates:

            obj.to_dict() -> dict
        """
        cls = apply_generator(cls, generate_to_dict)
        return cls

    @staticmethod
    def from_dict(cls: C) -> C:
        """
        Generates:

            Class.from_dict(data)
        """
        cls = apply_generator(cls, generate_from_dict)
        return cls

    @staticmethod
    def json(cls: C) -> C:
        """
        Generates JSON serialization support.

        Methods:
            to_json()
            from_json()
        """
        cls = apply_generator(cls, generate_json)
        return cls

    @staticmethod
    def record(cls: C) -> C:
        """
        Generates a record-style class.

        Includes:
        - constructor
        - equality
        - hash
        - string representation
        - immutability
        """
        cls = apply_generator(cls, generate_record)
        return cls

    @staticmethod
    def equals_and_hashcode(cls: C) -> C:
        """
        Alias for @komodo.eq.
        """
        cls = apply_generator(cls, generate_eq_hash)
        return cls

    @staticmethod
    def to_string(cls: C) -> C:
        """
        Alias for @komodo.to_str.
        """
        cls = apply_generator(cls, generate_to_str)
        return cls


komodo = _Komodo()
__all__ = ["komodo"]
