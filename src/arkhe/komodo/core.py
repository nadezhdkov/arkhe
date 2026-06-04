"""
arkhe.komodo.core
-------------------
The `komodo` namespace — all class-level annotation decorators live here.
"""

from typing import TypeVar, Callable, Any, overload, Optional, List
import logging
from arkhe.komodo.access_level import AccessLevel
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

    @overload
    @staticmethod
    def data(cls: C) -> C: ...

    @overload
    @staticmethod
    def data(*, static_constructor: Optional[str] = None) -> Callable[[C], C]: ...

    @staticmethod
    def data(cls: Optional[C] = None, *, static_constructor: Optional[str] = None) -> Any:
        """
        Generates data class features.
        """
        def wrapper(c: C) -> C:
            c = _Komodo.all_args_constructor(c, static_name=static_constructor)
            c = _Komodo.to_str(c)
            c = _Komodo.eq(c)
            from arkhe.komodo.ast_generators.utils import mark_komodo_meta
            mark_komodo_meta(c, "data")
            return c
        return wrapper(cls) if cls is not None else wrapper

    @overload
    @staticmethod
    def value(cls: C) -> C: ...

    @overload
    @staticmethod
    def value(*, static_constructor: Optional[str] = None) -> Callable[[C], C]: ...

    @staticmethod
    def value(cls: Optional[C] = None, *, static_constructor: Optional[str] = None) -> Any:
        """
        Generates value class features.
        """
        def wrapper(c: C) -> C:
            c = _Komodo.data(c, static_constructor=static_constructor)
            c = _Komodo.immutable(c)
            from arkhe.komodo.ast_generators.utils import mark_komodo_meta
            mark_komodo_meta(c, "value")
            return c
        return wrapper(cls) if cls is not None else wrapper

    @overload
    @staticmethod
    def no_args_constructor(cls: C) -> C: ...

    @overload
    @staticmethod
    def no_args_constructor(*, access: AccessLevel = AccessLevel.PUBLIC, static_name: Optional[str] = None) -> Callable[[C], C]: ...

    @staticmethod
    def no_args_constructor(cls: Optional[C] = None, *, access: AccessLevel = AccessLevel.PUBLIC, static_name: Optional[str] = None) -> Any:
        """
        Generates no_args_constructor.
        """
        def wrapper(c: C) -> C:
            c = apply_generator(c, lambda ast_cls, t: generate_constructor(ast_cls, t, "no_args", access, static_name))
            return c
        return wrapper(cls) if cls is not None else wrapper

    @overload
    @staticmethod
    def required_args_constructor(cls: C) -> C: ...

    @overload
    @staticmethod
    def required_args_constructor(*, access: AccessLevel = AccessLevel.PUBLIC, static_name: Optional[str] = None) -> Callable[[C], C]: ...

    @staticmethod
    def required_args_constructor(cls: Optional[C] = None, *, access: AccessLevel = AccessLevel.PUBLIC, static_name: Optional[str] = None) -> Any:
        """
        Generates required_args_constructor.
        """
        def wrapper(c: C) -> C:
            c = apply_generator(c, lambda ast_cls, t: generate_constructor(ast_cls, t, "required", access, static_name))
            return c
        return wrapper(cls) if cls is not None else wrapper

    @overload
    @staticmethod
    def all_args_constructor(cls: C) -> C: ...

    @overload
    @staticmethod
    def all_args_constructor(*, access: AccessLevel = AccessLevel.PUBLIC, static_name: Optional[str] = None) -> Callable[[C], C]: ...

    @staticmethod
    def all_args_constructor(cls: Optional[C] = None, *, access: AccessLevel = AccessLevel.PUBLIC, static_name: Optional[str] = None) -> Any:
        """
        Generates all_args_constructor.
        """
        def wrapper(c: C) -> C:
            c = apply_generator(c, lambda ast_cls, t: generate_constructor(ast_cls, t, "all", access, static_name))
            return c
        return wrapper(cls) if cls is not None else wrapper

    @overload
    @staticmethod
    def to_str(cls: C) -> C: ...

    @overload
    @staticmethod
    def to_str(*, onlyExplicitlyIncluded: bool = False, callSuper: bool = False, includeFieldNames: bool = True, doNotUseGetters: bool = False, exclude: Optional[List[str]] = None, of: Optional[List[str]] = None) -> Callable[[C], C]: ...

    @staticmethod
    def to_str(cls: Optional[C] = None, *, onlyExplicitlyIncluded: bool = False, callSuper: bool = False, includeFieldNames: bool = True, doNotUseGetters: bool = False, exclude: Optional[List[str]] = None, of: Optional[List[str]] = None) -> Any:
        """
        Generates __str__.
        """
        def wrapper(c: C) -> C:
            c = apply_generator(c, lambda ast_cls, t: generate_to_str(ast_cls, t, onlyExplicitlyIncluded, callSuper, includeFieldNames, doNotUseGetters, exclude, of))
            return c
        return wrapper(cls) if cls is not None else wrapper

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

    @overload
    @staticmethod
    def builder(cls: C) -> C: ...

    @overload
    @staticmethod
    def builder(*, access: AccessLevel = AccessLevel.PUBLIC) -> Callable[[C], C]: ...

    @staticmethod
    def builder(cls: Optional[C] = None, *, access: AccessLevel = AccessLevel.PUBLIC) -> Any:
        """
        Generates a fluent Builder API.
        """
        def wrapper(c: C) -> C:
            c = apply_generator(c, lambda ast_cls, t: generate_builder(ast_cls, t, access))
            return c
        return wrapper(cls) if cls is not None else wrapper

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

    @overload
    @staticmethod
    def getter(cls: C) -> C: ...

    @overload
    @staticmethod
    def getter(*, access: AccessLevel = AccessLevel.PUBLIC) -> Callable[[C], C]: ...

    @staticmethod
    def getter(cls: Optional[C] = None, *, access: AccessLevel = AccessLevel.PUBLIC) -> Any:
        """
        Generates get_<field>() methods.
        """
        def wrapper(c: C) -> C:
            c = apply_generator(c, lambda ast_cls, t: generate_accessors(ast_cls, t, False, True, False, False, access))
            return c
        return wrapper(cls) if cls is not None else wrapper

    @overload
    @staticmethod
    def setter(cls: C) -> C: ...

    @overload
    @staticmethod
    def setter(*, access: AccessLevel = AccessLevel.PUBLIC) -> Callable[[C], C]: ...

    @staticmethod
    def setter(cls: Optional[C] = None, *, access: AccessLevel = AccessLevel.PUBLIC) -> Any:
        """
        Generates set_<field>(value) methods.
        """
        def wrapper(c: C) -> C:
            c = apply_generator(c, lambda ast_cls, t: generate_accessors(ast_cls, t, False, False, True, False, access))
            return c
        return wrapper(cls) if cls is not None else wrapper

    @staticmethod
    def withers(cls: C) -> C:
        """
        Generates immutable with_<field>() methods.

        Example:
            new_user = user.with_name("John")
        """
        cls = apply_generator(cls, lambda c, t: generate_accessors(c, t, False, False, False, True))
        return cls

    @overload
    @staticmethod
    def logger(cls: C) -> C: ...

    @overload
    @staticmethod
    def logger(*, level: int = logging.DEBUG, topic: Optional[str] = None) -> Callable[[C], C]: ...

    @staticmethod
    def logger(cls: Optional[C] = None, *, level: int = logging.DEBUG, topic: Optional[str] = None) -> Any:
        """
        Injects a logger instance.
        """
        def wrapper(c: C) -> C:
            c = apply_generator(c, lambda ast_cls, t: generate_logger(ast_cls, t, level, topic))
            return c
        return wrapper(cls) if cls is not None else wrapper

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

    @overload
    @staticmethod
    def to_string(cls: C) -> C: ...

    @overload
    @staticmethod
    def to_string(*, onlyExplicitlyIncluded: bool = False, callSuper: bool = False, includeFieldNames: bool = True, doNotUseGetters: bool = False, exclude: Optional[List[str]] = None, of: Optional[List[str]] = None) -> Callable[[C], C]: ...

    @staticmethod
    def to_string(cls: Optional[C] = None, *, onlyExplicitlyIncluded: bool = False, callSuper: bool = False, includeFieldNames: bool = True, doNotUseGetters: bool = False, exclude: Optional[List[str]] = None, of: Optional[List[str]] = None) -> Any:
        """
        Alias for @komodo.to_str.
        """
        def wrapper(c: C) -> C:
            c = apply_generator(c, lambda ast_cls, t: generate_to_str(ast_cls, t, onlyExplicitlyIncluded, callSuper, includeFieldNames, doNotUseGetters, exclude, of))
            return c
        return wrapper(cls) if cls is not None else wrapper


komodo = _Komodo()
__all__ = ["komodo"]
